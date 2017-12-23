import settings
import math
import googlemaps
import pprint
from pyshorteners import Shortener

shortener = Shortener('Google', api_key=settings.SHORT_GURL_TOKEN)


PP = pprint.PrettyPrinter(indent=4)


def coord_distance(lat1, lon1, lat2, lon2):
    """
    Finds the distance between two pairs of latitude and longitude.
    :param lat1: Point 1 latitude.
    :param lon1: Point 1 longitude.
    :param lat2: Point two latitude.
    :param lon2: Point two longitude.
    :return: Kilometer distance.
    """
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    km = 6367 * c
    return km


def in_box(coords, box):
    """
    Find if a coordinate tuple is inside a bounding box.
    :param coords: Tuple containing latitude and longitude.
    :param box: Two tuples, where first is the bottom left, and the second is the top right of the box.
    :return: Boolean indicating if the coordinates are in the box.
    """
    if box[0][0] < coords[0] < box[1][0] and box[1][1] < coords[1] < box[0][1]:
        return True
    return False


def post_listing_to_slack(sc, listing):
    """
    Posts the listing to slack.
    :param sc: A slack client.
    :param listing: A record of the listing.
    """
    try:
        desc = u'{0} | {1} | {2} | <{3}>'.format(
            listing["area"],
            listing["price"],
            listing["name"],
            shortener.short(listing["url"]),
        )
        # options.append({"commuter": commute["commuter"],
        #                 "time": travel_time,
        #                 "fare": fare,
        #                 "steps": step_breakdown})
        for commute in listing["commute"]:
            time_breakdown = "Total:{:.2f} ".format(commute['total'])
            for commute_type, time in commute["time"].iteritems():
                time_breakdown += "{0}:{1:.2f} ".format(commute_type, time)
            time_breakdown += "Extra:{:.2f}".format(commute['extra'])

            desc += u"\n{0} | {1} steps | ${2} | {3} | {4}".format(
                commute["commuter"],
                commute["steps"],
                commute["fare"],
                time_breakdown,
                commute["maps_url"],
            )

        if not settings.DEV_MODE:
            sc.api_call(
                "chat.postMessage", channel=settings.SLACK_CHANNEL, text=desc,
                username='pybot', icon_emoji=':robot_face:'
            )
        else:
            print desc
    except (UnicodeEncodeError, UnicodeDecodeError) as exc:
        print "ERROR: {}".format(exc)


def find_points_of_interest(geotag, location):
    """
    Find points of interest, like transit, near a result.
    :param geotag: The geotag field of a Craigslist result.
    :param location: The where field of a Craigslist result.  Is a string containing a description of where
    the listing was posted.
    :return: A dictionary containing annotations.
    """
    area = "Unknown"
    commutes = {}
    # Look to see if the listing is in any of the neighborhood boxes we
    # defined.
    for a, coords in settings.BOXES.items():
        if in_box(geotag, coords):
            area = a

    # If the listing isn't in any of the boxes we defined, check to see if the string description of the neighborhood
    # matches anything in our list of neighborhoods.
    if len(area) == 0:
        for hood in settings.NEIGHBORHOODS:
            if hood in location.lower():
                area = hood

    commutes = process_google(geotag)

    return {
        "area_found": len(commutes) > 0,
        "area": area,
        "commute": commutes,
    }


GMAPS = googlemaps.Client(settings.MAPS_TOKEN)


def process_google(source_addr):
    """Look things up on google's apis."""
    # Request directions via public transit
    commutes = []
    found = {}
    for commute in settings.COMMUTERS:

        print commute["work"]
        found[commute["commuter"]] = False

        for cmode in settings.COMMUTE_MODES:

            if commute["max_limits"]["time." + cmode.upper()] == 0:
                # dont waste a query on something we will immediately throw out
                continue

            directions_result = GMAPS.directions(
                source_addr,
                commute["work"],
                mode=cmode,
                alternatives=settings.ALTERNATES,
                transit_routing_preference="fewer_transfers",
                arrival_time=commute["start_time"])

            options = []
            for route in directions_result:
                origin = route["legs"][0]["start_location"]
                destination = route["legs"][-1]["end_location"]
                maps_url = get_gmaps_directions_url(origin, destination, cmode)

                travel_time, total, extra = route_time(route)
                option = {
                    "commuter": commute["commuter"],
                    "time": travel_time,
                    "total": total,
                    "extra": extra,
                    "fare": route_cost(route),
                    "steps": route_steps(route),
                    "maps_url": maps_url,
                }
                print option

                evaluation = check_against_limits(
                    option, commute["max_limits"])
                for key, val in evaluation.iteritems():
                    if not val:
                        print "FAIL: {} > {}".format(key, commute["max_limits"][key])

                if False not in evaluation.values():
                    options.append(option)
                    found[commute["commuter"]] = True
                else:
                    PP.pprint(directions_result)

            if options:
                options.sort(key=lambda option: option["fare"])
                commutes.append(options[0])

    print
    if False in found.values():
        commutes = []
    return commutes


def check_against_limits(option, limits, leader=""):
    vals = {}
    for key, value in option.iteritems():
        if isinstance(value, dict):
            vals.update(
                check_against_limits(
                    value,
                    limits,
                    leader +
                    key +
                    "."))
        elif leader + key in limits:
            vals[leader + key] = value <= limits[leader + key]
    return vals


def route_steps(route):
    """Count number of steps between src and dest."""
    steps = {}
    for leg in route["legs"]:
        for step in leg["steps"]:
            mode = step["travel_mode"]
            steps[mode] = steps.get(mode, 0) + 1
    return steps


def route_cost(route):
    """Return cost of route. Default to zero if doenst exist."""
    return route.get('fare', {'value': 0})["value"]


def route_time(route):
    """Return the time spent not on transit."""
    legs = route["legs"]
    # PP.pprint(steps)

    # legs only matter if you're doing a multi stop trip, not sure if there can
    # be a gap between the end of one leg and the start of the next

    travel_time = {}

    total_time = 0
    extra_time = 0

    for leg in legs:

        total_time += leg["duration"]["value"]
        extra_time += leg["duration"]["value"]

        for step in leg["steps"]:

            keys = step.keys()
            if "travel_mode" in keys:
                mode = step["travel_mode"]
                step_time = step["duration"]["value"]

                extra_time -= step_time
                if mode not in travel_time.keys():
                    travel_time[mode] = 0
                travel_time[mode] += step_time

    for key in travel_time:
        travel_time[key] /= 60.0
    return travel_time, total_time / 60.0, extra_time / 60.0


def get_gmaps_directions_url(origin_location, destination_location, mode):
    url = "https://www.google.com/maps/dir/?api=1"
    url += "&origin={},{}".format(
        origin_location["lat"],
        origin_location["lng"])
    url += "&destination={},{}".format(
        destination_location["lat"],
        destination_location["lng"])
    url += "&travelmode={}".format(mode)
    return shortener.short(url)

import settings
import math
import googlemaps


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
            listing["url"],
        )
        for commute in listing["commute"]:
            desc += u"\n{0}".format(commute)

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
    area_found = False
    area = ""
    # Look to see if the listing is in any of the neighborhood boxes we
    # defined.
    for a, coords in settings.BOXES.items():
        if in_box(geotag, coords):
            area = a
            area_found = True

    # TODO add google maps location resolution
    commutes = process_google(geotag)

    # If the listing isn't in any of the boxes we defined, check to see if the string description of the neighborhood
    # matches anything in our list of neighborhoods.
    if len(area) == 0:
        for hood in settings.NEIGHBORHOODS:
            if hood in location.lower():
                area = hood

    return {
        "area_found": area_found,
        "area": area,
        "commute": commutes,
    }

GMAPS = googlemaps.Client(settings.MAPS_TOKEN)

def process_google(source_addr):
    """Look things up on google's apis."""
    # Request directions via public transit
    commutes = []
    for commute in settings.COMMUTERS:
        for cmode in settings.COMMUTE_MODES:
            directions_result = GMAPS.directions(source_addr,
                                                 commute["work"],
                                                 mode=cmode,
                                                 alternatives=False,
                                                 arrival_time=commute["start_time"])
            options = []
            # PP.pprint(directions_result)
            for route in directions_result:
                fare = route_cost(route)
                steps = 1
                step_breakdown = route_steps(route)
                steps = step_breakdown.get("TRANSIT", 0)
                travel_time = route_time(route)
                extra = travel_time.get("WALKING", 0) + travel_time["extra"]
                # print travel_time
                # print step_breakdown
                # print fare, total, extra, steps
                if (extra <= commute["max_extra"] and
                        fare <= commute["max_fare"] and
                        steps <= commute["max_transit_steps"]):
                    options.append({"time": travel_time,
                                    "fare": fare,
                                    "steps": step_breakdown})

            options.sort(key=lambda option: option["fare"])

            if options:
                commutes.append(options[0])

    return commutes


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

    travel_time["extra"] = extra_time
    travel_time["total"] = total_time
    for key in travel_time:
        travel_time[key] /= 60.0
    return travel_time

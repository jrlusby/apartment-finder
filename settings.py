import os
from datetime import datetime

DEV_MODE = False

if DEV_MODE:
    LIMIT = 5
    ALTERNATES=False
else:
    LIMIT = 10
    ALTERNATES=True


## Price

FILTERS = {
    'min_price': 1500,
    'max_price': 2700,
    'min_bedrooms': 1,
    'cats_ok': 1,
    'min_bathrooms': 1,
    'min_ft2': 450,
}

# The minimum rent you want to pay per month.
MIN_PRICE = 1500

# The maximum rent you want to pay per month.
MAX_PRICE = 2700

## Location preferences

# The Craigslist site you want to search on.
# For instance, https://sfbay.craigslist.org is SF and the Bay Area.
# You only need the beginning of the URL.
CRAIGSLIST_SITE = 'sfbay'

# What Craigslist subdirectories to search on.
# For instance, https://sfbay.craigslist.org/eby/ is the East Bay, and https://sfbay.craigslist.org/sfc/ is San Francisco.
# You only need the last three letters of the URLs.
if DEV_MODE:
    AREAS = ["sfc"]
else:
    AREAS = ["pen", "eby", "sfc", "sby", "nby", "scz"]

# A list of neighborhoods and coordinates that you want to look for apartments in.  Any listing that has coordinates
# attached will be checked to see which area it is in.  If there's a match, it will be annotated with the area
# name.  If no match, the neighborhood field, which is a string, will be checked to see if it matches
# anything in NEIGHBORHOODS.
BOXES = {
    "adams_point": [
        [37.80789, -122.25000],
        [37.81589,	-122.26081],
    ],
    "piedmont": [
        [37.82240, -122.24768],
        [37.83237, -122.25386],
    ],
    "rockridge": [
        [37.83826, -122.24073],
        [37.84680, -122.25944],
    ],
    "berkeley": [
        [37.86226, -122.25043],
        [37.86781, -122.26502],
    ],
    "north_berkeley": [
        [37.86425, -122.26330],
        [37.87655, -122.28974],
    ],
    "pac_heights": [
        [37.79124, -122.42381],
        [37.79850, -122.44784],
    ],
    "lower_pac_heights": [
        [37.78554, -122.42878],
        [37.78873, -122.44544],
    ],
    "haight": [
        [37.77059, -122.42688],
        [37.77086, -122.45401],
    ],
    "sunset": [
        [37.75451, -122.46422],
        [37.76258, -122.50825],
    ],
    "richmond": [
        [37.77188, -122.47263],
        [37.78029, -122.51005],
    ],
    "presidio": [
        [37.77805, -122.43959],
        [37.78829, -122.47151],
    ],
    "bay_area": [
        [37.2025, -121.6406],
        [38.1826, -122.8102],
    ],
}

# A list of neighborhood names to look for in the Craigslist neighborhood name field. If a listing doesn't fall into
# one of the boxes you defined, it will be checked to see if the neighborhood name it was listed under matches one
# of these.  This is less accurate than the boxes, because it relies on the owner to set the right neighborhood,
# but it also catches listings that don't have coordinates (many listings are missing this info).
NEIGHBORHOODS = ["berkeley north", "berkeley", "rockridge", "adams point", "oakland lake merritt", "cow hollow", "piedmont", "pac hts", "pacific heights", "lower haight", "inner sunset", "outer sunset", "presidio", "palo alto", "richmond / seacliff", "haight ashbury", "alameda", "twin peaks", "noe valley", "bernal heights", "glen park", "sunset", "mission district", "potrero hill", "dogpatch"]

# ## Transit preferences

JANE_COMMUTE = {
    "commuter": "Jane",
    "work": "Scale Computing, 360 Ritch St #300, San Francisco, CA 94107",
    "start_time": datetime(2018, 1, 8, 9),
    "max_limits": {
        "fare": 15,
        "time.DRIVING": 0,
        "time.BICYCLING": 30,
        "time.TRANSIT": 90,
        "time.WALKING": 15,
        "steps.TRANSIT": 3,
        "total": 90,
        "extra": 20,
    }
}

PAIGE_COMMUTE = {
    "commuter": "Paige",
    "work": "DaVita, Golden Gate",
    "start_time": datetime(2018, 1, 8, 6),
    "max_limits": {
        "fare": 15,
        "time.DRIVING": 20,
        "time.BICYCLING": 30,
        "time.TRANSIT": 90,
        "time.WALKING": 15,
        "steps.TRANSIT": 3,
        "total": 90,
        "extra": 20,
    }
}

if DEV_MODE:
    COMMUTERS = [JANE_COMMUTE]
    COMMUTE_MODES = ['transit']
else:
    COMMUTERS = [JANE_COMMUTE, PAIGE_COMMUTE]
    COMMUTE_MODES = ['transit', 'bicycling', 'walking', 'driving']

## Search type preferences

# The Craigslist section underneath housing that you want to search in.
# For instance, https://sfbay.craigslist.org/search/apa find apartments for rent.
# https://sfbay.craigslist.org/search/sub finds sublets.
# You only need the last 3 letters of the URLs.
CRAIGSLIST_HOUSING_SECTION = 'apa'

## System settings

# How long we should sleep between scrapes of Craigslist.
# Too fast may get rate limited.
# Too slow may miss listings.
SLEEP_INTERVAL = 20 # seconds

# Which slack channel to post the listings into.
SLACK_CHANNEL = "#housing"

# The token that allows us to connect to slack.
# Should be put in private.py, or set as an environment variable.
SLACK_TOKEN = os.getenv('SLACK_TOKEN', "")

# Any private settings are imported here.
try:
    from private import *
except Exception:
    pass

# Any external private settings are imported from here.
try:
    from config.private import *
except Exception:
    pass

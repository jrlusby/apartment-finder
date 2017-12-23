#! /usr/bin/env python2
"""Main loop for apartment finding slack bot."""
import time
import sys
import traceback
import settings
from scraper import do_scrape

if __name__ == "__main__":
    while True:
        print("{}: Starting scrape cycle".format(time.ctime()))

        try:
            do_scrape()
        except KeyboardInterrupt:
            print("Exiting....")
            sys.exit(1)
        except Exception as exc:
            print("Error with the scraping:", sys.exc_info()[0])
            traceback.print_exc()
        else:
            print("{}: Successfully finished scraping".format(time.ctime()))

        if settings.DEV_MODE:
            break

        time.sleep(settings.SLEEP_INTERVAL)

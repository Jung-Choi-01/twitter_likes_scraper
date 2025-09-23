import os
import sys
import argparse
from twitter_scraper import twitter_scraper

try:
    from dotenv import load_dotenv

    print("Loading .env file")
    load_dotenv()
    print("Loaded .env file\n")
except Exception as e:
    print(f"Error loading .env file: {e}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        add_help=True,
        usage="python likes_scraper [option] ... [arg] ...",
        description="Likes Scraper is a stripped version of Twitter Scraper for your own likes.",
    )
    try:
        parser.add_argument(
            "--user",
            type=str,
            default=os.getenv("TWITTER_USERNAME"),
            help="Your Twitter username.",
        )

        parser.add_argument(
            "--authtoken",
            type=str,
            default=os.getenv("AUTH_TOKEN"),
            help="Your auth token.",
        )

        parser.add_argument(
            "--headlessState",
            type=str,
            default=os.getenv("HEADLESS"),
            help="Headless mode? [yes/no]"
        )
    
    except Exception as e:
        print(f"Error retrieving environment variables: {e}")
        sys.exit(1)

    parser.add_argument(
        "-t",
        "--tweets",
        type=int,
        default=5,
        help="Number of tweets to scrape (default: 5)",
    )

    parser.add_argument(
        "-ntl",
        "--no_tweets_limit",
        nargs='?',
        default=False,
        help="Set no limit to the number of tweets to scrape (will scrape until no more tweets are available).",
    )

    parser.add_argument(
        "--rateLimit",
        type=int,
        default=os.getenv("RATELIMIT") if os.getenv("RATELIMIT") is not None else 3,
        help="T/S to throttle to (integer)"
    )

    parser.add_argument(
        "--stopId",
        type=str,
        help="Tweet ID to stop scraping at"
    )

    args = parser.parse_args()

    USER_UNAME = args.user
    USER_AUTHTOKEN = args.authtoken
    HEADLESS_MODE= args.headlessState
    RATELIMIT = args.rateLimit

    if USER_UNAME is None:
        USER_UNAME = input("Twitter Username: ")

    if USER_AUTHTOKEN is None:
        USER_AUTHTOKEN = input("Enter authtoken: ")

    if HEADLESS_MODE is None:
        HEADLESS_MODE = str(input("Headless?[Yes/No]")).lower()

    print()

    if USER_UNAME is not None and USER_AUTHTOKEN is not None:
        scraper = twitter_scraper(
            username=USER_UNAME,
            authtoken=USER_AUTHTOKEN,
            headless_state=HEADLESS_MODE,
            ratelimit=RATELIMIT,
            stop_id=args.stopId
        )
        scraper.login()
        try:
            scraper.scrape_tweets(
                max_tweets=args.tweets,
                no_tweets_limit= args.no_tweets_limit if args.no_tweets_limit is not None else True,
                username=USER_UNAME
            )
        except Exception as e:
            print(e)
        finally:
            scraper.save_to_json()
        
        if not scraper.interrupted:
            scraper.driver.close()
    else:
        print("Missing Twitter username or password environment variables. Please check your .env file.")
if __name__ == "__main__":
    main()

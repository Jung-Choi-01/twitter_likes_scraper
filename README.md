# twitter_likes_scraper
Scrapes likes from Twitter using selenium given an auth token and a username.

## Usage:
1. Install dependencies with `pip install -r requirements.txt`
2. Obtain your AUTH_TOKEN cookie by signing in to twitter and downloading your cookies. Cookies.txt ([Chrome](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)/[Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)) may be helpful for this step. You should have a cookie named auth_token containing a hexadecimal value.
3. (Optional) Create a .env variable in the package root with the following information:
```
TWITTER_USERNAME="USERNAME"
AUTH_TOKEN="AUTHTOKEN"
HEADLESS="no"
# optional values
RATELIMIT=INTEGER_VALUE
```
- If you do not create a .env file, you will be prompted for the required information on app startup, except for ratelimit which will default to 3 tweets/second.
4. Run `python likes_scraper` and specify any optional arguments, which are:
- `-t or --tweets=INTEGER`: the number of likes to scrape
- `-ntl or --no_tweets_limit`: to continue scraping until no tweets are left (`-t`)
- `--rateLimit=INTEGER`: the tweets per second to limit scraping by
    - Scraping will run at a rate lower than this because throttling currently ensures every tweet takes *at least* 1/rateLimit seconds to process, but does not compensate for going longer.
- `--stopId=STRING`: the tweet ID to stop scraping at (overrides `-t` and `-ntl`)
- These arguments can also be viewed with `python likes_scraper --help`
5. View your JSON tweet data in ./tweets/...

## Acknowledgements
This code is based off of [godkingjay's selenium-twitter-scraper](https://github.com/godkingjay/selenium-twitter-scraper), with the following modifications:
- Authentication uses an auth_token instead of a password
- Scraper can now only retrieve likes
- Scraper shows tweets per second in progress bar
- Extra fields for liked tweets added (quote tweet info, video scraping, is reply, and more)
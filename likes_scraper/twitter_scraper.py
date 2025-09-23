import os
import sys
import json
import pandas as pd
from progress import Progress
from scroller import Scroller
from tweet import Tweet

from datetime import datetime
from fake_headers import Headers
from time import sleep
from time import time

from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

class twitter_scraper:
    def __init__(
        self,
        username,
        authtoken,
        headless_state,
        ratelimit,
        max_tweets=50,
        stop_id=None,
        proxy=None
    ):
        print("Initializing Twitter Scraper...")
        self.username = username
        self.authtoken = authtoken
        self.headless_state = headless_state
        self.interrupted = False
        self.tweet_ids = set()
        self.data = []
        self.tweet_cards = []
        self.max_tweets = max_tweets
        self.progress = Progress(0, max_tweets)
        self.driver = self._get_driver(proxy)
        self.actions = ActionChains(self.driver)
        self.scroller = Scroller(self.driver)
        self.ratelimit = ratelimit
        self.stop_id = stop_id
        self._config_scraper(
            max_tweets,
            username
        )

    def _config_scraper(
        self,
        max_tweets=50,
        username=None
    ):
        self.tweet_ids = set()
        self.data = []
        self.tweet_cards = []
        self.max_tweets = max_tweets
        self.progress = Progress(0, max_tweets)
        self.scraper_details = {
            "type": None,
            "username": username,
        }
        self.scroller = Scroller(self.driver)

    def _get_driver(
        self,
        proxy=None,
    ): 
        print("Setup WebDriver...")

        # User agent of a andoird smartphone device
        header="Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.87 Mobile Safari/537.36"

        browser_option = FirefoxOptions()
        browser_option.add_argument("--no-sandbox")
        browser_option.add_argument("--disable-dev-shm-usage")
        browser_option.add_argument("--ignore-certificate-errors")
        browser_option.add_argument("--disable-gpu")
        browser_option.add_argument("--log-level=3")
        browser_option.add_argument("--disable-notifications")
        browser_option.add_argument("--disable-popup-blocking")
        browser_option.add_argument("--user-agent={}".format(header))
        if proxy is not None:
            browser_option.add_argument("--proxy-server=%s" % proxy)

        # Option to hide browser or not
        # If not yes then skips the headless
        if self.headless_state == 'yes':
            # For Hiding Browser
            browser_option.add_argument("--headless")

        try:
            print("Initializing FirefoxDriver...")
            driver = webdriver.Firefox(
                options=browser_option,
            )

            print("WebDriver Setup Complete")
            return driver
        except WebDriverException:
            print("Downloading FirefoxDriver...")
            firefoxdriver_path = GeckoDriverManager().install()
            firefox_service = FirefoxService(executable_path=firefoxdriver_path)

            print("Initializing FirefoxDriver...")
            driver = webdriver.Firefox(
                service=firefox_service,
                options=browser_option,
            )

            print("WebDriver Setup Complete")
            return driver

    def login(self):
        print()
        print("Logging in to Twitter...")

        self.driver.execute_script("document.body.style.zoom='150%'") #set zoom to 150%
        self.driver.get("https://x.com")
        sleep(3)

        # set up request interceptor before navigating to likes, in case it's really early on
        self.driver.request_interceptor = self.request_interceptor
        self.blob_queue = []

        self.driver.add_cookie({"name": "auth_token", "value": self.authtoken})
        self.driver.get(f"https://x.com/{self.username}/likes")
        sleep(3)
        if self.driver.current_url.count("/") != 4:
            raise ValueError(
                """Failed to login. This may be due to the following:

- Internet connection is unstable
- Username is incorrect
- Password is incorrect
""")
        print()
        print("Login Successful")
        print()

    def _input_unusual_activity(self):
        input_attempt = 0

        while True:
            try:
                unusual_activity = self.driver.find_element(
                    "xpath", "//input[@data-testid='ocfEnterTextTextInput']"
                )
                unusual_activity.send_keys(self.username)
                unusual_activity.send_keys(Keys.RETURN)
                sleep(3)
                break
            except NoSuchElementException:
                input_attempt += 1
                if input_attempt >= 3:
                    break

    def get_tweet_cards(self):
        self.tweet_cards = self.driver.find_elements(
            "xpath", '//article[@data-testid="tweet" and not(@disabled)]'
        )

    def request_interceptor(self, request):
        if ".m3u8" in request.url and "?variant_version=1" in request.url: # second tag seems to filter only main video from tweet
            self.blob_queue.append(request.url)

    # this is the big scary awesome function
    def scrape_tweets(
        self,
        max_tweets=50,
        username=None,
        no_tweets_limit=False
    ):
        self._config_scraper(
            max_tweets,
            username
        )
        
        print(f"Scraping likes from: {username}");

        # Accept cookies to make the banner disappear
        try:
            accept_cookies_btn = self.driver.find_element(
            "xpath", "//span[text()='Refuse non-essential cookies']/../../..")
            accept_cookies_btn.click()
        except NoSuchElementException:
            pass

        start_time = time()
        self.progress.print_progress(0, False, 0, no_tweets_limit, time() - start_time)

        refresh_count = 0
        added_tweets = 0
        empty_count = 0
        retry_cnt = 0

        # sometimes the first blobbed videos don't load if we don't have this
        sleep(2)

        while self.scroller.scrolling:
            try:
                # gets every tweet card in the browser view currently
                self.get_tweet_cards()
                added_tweets = 0

                # for each of the last 15 cards in the tweet cards in view (limit processing?)
                for card in self.tweet_cards[-15:]:
                    try:
                        card_start_time = time()

                        tweet_id = str(card)

                        # if we haven't processed the tweet yet
                        if tweet_id in self.tweet_ids: continue
                        self.tweet_ids.add(tweet_id)
                        
                        # center the screen around the card
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView();", card
                        )
                        tweet = Tweet(card=card, blob_queue=self.blob_queue)
                        tweet.process()

                        # store the data and track that we've stored it, if it's not null
                        if tweet is None: continue
                        if tweet.error: continue
                        if tweet.tweet_dictionary is None: continue 
                        if tweet.is_ad: continue

                        tweet.tweet_dictionary['tweet_id'] = int(tweet.tweet_dictionary['tweet_id'])
                        self.data.append(tweet.tweet_dictionary)
                        added_tweets += 1
                        current_num_tweets = len(self.data)
                        self.progress.print_progress(current_num_tweets, False, 0, no_tweets_limit, time() - start_time)

                        if len(self.data) >= self.max_tweets and not no_tweets_limit \
                        or tweet.tweet_dictionary['tweet_id'] == self.stop_id:
                            self.scroller.scrolling = False
                            break

                        # throttle by remaining time required to get t/s, or 0 if that would've been negative
                        sleep(max(1/self.ratelimit - (time() - card_start_time), 0))
                                
                    except NoSuchElementException:
                        continue

                if len(self.data) >= self.max_tweets and not no_tweets_limit:
                    break

                if added_tweets == 0:
                    # Check if there is a button "Retry" and click on it with a regular basis until a certain amount of tries
                    try:
                        while retry_cnt < 15:
                            retry_button = self.driver.find_element(
                            "xpath", "//span[text()='Retry']/../../..")
                            self.progress.print_progress(len(self.data), True, retry_cnt, no_tweets_limit, time() - start_time)
                            sleep(600)
                            retry_button.click()
                            retry_cnt += 1
                            sleep(2)
                    # There is no Retry button so the counter is reseted
                    except NoSuchElementException:
                        retry_cnt = 0
                        self.progress.print_progress(len(self.data), False, 0, no_tweets_limit, time() - start_time)

                    if empty_count >= 5:
                        if refresh_count >= 3:
                            print()
                            print("No more tweets to scrape")
                            break
                        refresh_count += 1
                    empty_count += 1
                    sleep(1)
                else:
                    empty_count = 0
                    refresh_count = 0
            except StaleElementReferenceException:
                sleep(2)
                continue

        print("")

        if len(self.data) >= self.max_tweets or no_tweets_limit:
            print("Scraping Complete")
        else:
            print("Scraping Incomplete")

        if not no_tweets_limit:
            print("Tweets: {} out of {}\n".format(len(self.data), self.max_tweets))

    def save_to_json(self):
        print("Saving Tweets to json...")
        folder_path = "./tweets/"

        # now actually create the file
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print("Created Folder: {}".format(folder_path))
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_path = f"{folder_path}{self.username}_{current_time}_tweets_1-{len(self.data)}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        print("JSON Saved: {}".format(file_path))

    def get_tweets(self):
        return self.data

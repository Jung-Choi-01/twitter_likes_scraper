from time import sleep
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def remove_name_param(url):
    parsed = urlparse(url)
    # Parse query parameters into a dict
    query = parse_qs(parsed.query)
    # Remove the 'name' parameter if it exists
    query.pop('name', None)
    # Rebuild the query string
    new_query = urlencode(query, doseq=True)
    # Rebuild the URL without the 'name' parameter
    new_url = urlunparse(parsed._replace(query=new_query))
    return new_url

class Tweet:
    def __init__(self, card: WebDriver, blob_queue: list) -> None:
        self.card = card
        self.blob_queue = blob_queue
    
    def process(self):
        self.error = False
        self.tweet_dictionary = {}

        # required data:

        # tweet post time
        # grab this first because if there's an error it's an ad and so we don't want to grab the rest of it at all
        try:
            self.tweet_dictionary['date_time'] = self.card.find_element("xpath", ".//time").get_attribute(
                "datetime"
            )

            if self.tweet_dictionary['date_time'] is not None:
                self.is_ad = False
        except NoSuchElementException:
            self.is_ad = True
            self.error = True
            self.date_time = "skip"
        if self.error:
            return
        
        # address (url of tweet)
        try:
            self.tweet_dictionary['tweet_link'] = self.card.find_element(
                "xpath",
                ".//a[contains(@href, '/status/')]",
            ).get_attribute("href")
            self.tweet_dictionary['tweet_id'] = str(self.tweet_dictionary['tweet_link'].split("/")[-1])
        except NoSuchElementException:
            self.tweet_dictionary['tweet_link'] = ""
            self.tweet_dictionary['tweet_id'] = ""

        # tweet text
        self.tweet_dictionary['content'] = ""
        elements = self.card.find_elements(
            "xpath",
            '(.//div[@data-testid="tweetText" and not(ancestor::div[div[span[text()="Quote"]]])])[1]/span | (.//div[@data-testid="tweetText" and not(ancestor::div[div[span[text()="Quote"]]])])[1]/a'
        )
        for element in elements:
            # this is main tweet text
            self.tweet_dictionary['content'] += element.text + "\n"

        # quote text
        self.tweet_dictionary['quote_tweet_text'] = ""
        try:
            quote_element = self.card.find_element(
                'xpath',
                './/div[div[span[text()="Quote"]]]'
            )
            quote_tweet_text_elements = quote_element.find_elements(
                'xpath',
                './/div[@data-testid="tweetText"][1]/span'
            )
            for element in quote_tweet_text_elements:
                self.tweet_dictionary['quote_tweet_text'] += element.text + "\n"
        except NoSuchElementException:
            pass

        # poster handle + user
        try:
            user_name_spans = self.card.find_elements("xpath", './/div[@data-testid="User-Name"]//span')
            # trust me bro
            self.tweet_dictionary['user'] = user_name_spans[0].text
            self.tweet_dictionary['handle'] = user_name_spans[3].text 
        except NoSuchElementException:
            self.error = True
            self.tweet_dictionary['handle'] = "skip"
        
        # is_quoted_tweet
        try:
            # if there is more than one user avatar on the tweet, it's probably a quote
            self.tweet_dictionary['is_quote_tweet'] = bool(len(self.card.find_elements(
                "xpath", './/div[@data-testid="Tweet-User-Avatar"]'
            )) > 1)
        except NoSuchElementException:
            self.tweet_dictionary['is_quote_tweet'] = ""
        
        # is_reply_tweet
        try:
            # if the text "Replying to" exists, flag this tweet
            self.tweet_dictionary['replying_to'] = self.card.find_element("xpath",
            './/div[contains(text(), "Replying to") and not(ancestor::div[@data-testid="tweetText"])]//span').text
        except NoSuchElementException:
            self.tweet_dictionary['replying_to'] = ""
        
        # media details
        self.tweet_dictionary['media_url'] = []
        # tweet media details
        self.tweet_dictionary['quote_tweet_images'] = []
        # media details pt 1. image URL's
        try:
            elements = self.card.find_elements(
                "xpath", './/div[@data-testid="tweetPhoto"]//img'
            )
            for element in elements:
                if "video_thumb" in element.get_attribute("src"): continue
                # the href in the first a class above the tweet photo associates the tweetPhoto to its post. if its ID does not match this one, it is a quote tweet photo!
                if self.tweet_dictionary['tweet_id'] not in element.find_element("xpath", "ancestor::a[1]").get_attribute("href"):
                    self.tweet_dictionary['quote_tweet_images'].append(remove_name_param(element.get_attribute("src")))
                else:
                    self.tweet_dictionary['media_url'].append(remove_name_param(element.get_attribute("src")))
        except NoSuchElementException:
            pass

        # media details pt 2. gif URL's OR single-video posts
        try:
            elements = self.card.find_elements(
                "xpath", './/div[@data-testid="videoComponent"]//video'
            )
            for element in elements:
                if "video_thumb" in element.get_attribute("src"): continue
                # if self.tweet_dictionary['tweet_id'] not in element.find_element("xpath", "ancestor::a[1]").get_attribute("href"): continue

                if element.get_attribute("src") == '':
                    # we have a live video, wait for the request to come in
                    time_wait = 0.0
                    while len(self.blob_queue) == 0 and time_wait < 10:
                        sleep(.05)
                        time_wait += 0.05
                    self.tweet_dictionary['media_url'].append('' if len(self.blob_queue) == 0 else self.blob_queue.pop(0))
                else:
                    self.tweet_dictionary['media_url'].append(element.get_attribute("src"))
        except NoSuchElementException:
            pass

        # has_media
        self.tweet_dictionary['has_media'] = len(self.tweet_dictionary) != 0

        # profile image
        try:
            self.tweet_dictionary['profile_img'] = self.card.find_element(
                "xpath", './/div[@data-testid="Tweet-User-Avatar"]//img'
            ).get_attribute("src")
        except NoSuchElementException:
            self.tweet_dictionary['profile_img'] = ""

        # 
        # UNUSED/LEFTOVER CODE HERE
        # 

        # reply count?
        # if self.error:
        #     return
        # try:
        #     self.reply_cnt = card.find_element(
        #         "xpath", './/button[@data-testid="reply"]//span'
        #     ).text

        #     if self.reply_cnt == "":
        #         self.reply_cnt = "0"
        # except NoSuchElementException:
        #     self.reply_cnt = "0"

        # retweet count?
        # try:
        #     self.retweet_cnt = card.find_element(
        #         "xpath", './/button[@data-testid="retweet"]//span'
        #     ).text

        #     if self.retweet_cnt == "":
        #         self.retweet_cnt = "0"
        # except NoSuchElementException:
        #     self.retweet_cnt = "0"

        # like count?
        # try:
        #     self.like_cnt = card.find_element(
        #         "xpath", './/button[@data-testid="like"]//span'
        #     ).text

        #     if self.like_cnt == "":
        #         self.like_cnt = "0"
        # except NoSuchElementException:
        #     self.like_cnt = "0"

        # ...analytics... count?
        # try:
        #     self.analytics_cnt = card.find_element(
        #         "xpath", './/a[contains(@href, "/analytics")]//span'
        #     ).text

        #     if self.analytics_cnt == "":
        #         self.analytics_cnt = "0"
        # except NoSuchElementException:
        #     self.analytics_cnt = "0"

        # hashtags i think
        # try:
        #     self.tags = card.find_elements(
        #         "xpath",
        #         './/a[contains(@href, "src=hashtag_click")]',
        #     )
        #     self.tags = [tag.text for tag in self.tags]
        # except NoSuchElementException:
        #     self.tags = []

        # mentions
        # try:
        #     self.mentions = card.find_elements(
        #         "xpath",
        #         '(.//div[@data-testid="tweetText"])[1]//a[contains(text(), "@")]',
        #     )
        #     self.mentions = [mention.text for mention in self.mentions]
        # except NoSuchElementException:
        #     self.mentions = []

        # emojis
        # try:
        #     raw_emojis = card.find_elements(
        #         "xpath",
        #         '(.//div[@data-testid="tweetText"])[1]/img[contains(@src, "emoji")]',
        #     )

        #     self.emojis = [
        #         emoji.get_attribute("alt").encode("unicode-escape").decode("ASCII")
        #         for emoji in raw_emojis
        #     ]
        # except NoSuchElementException:
        #     self.emojis = []

        # a lot of info regarding poster stats (followers, following. don't really care)
        # self.following_cnt = "0"
        # self.followers_cnt = "0"
        # self.user_id = None

        # if scrape_poster_details:
        #     el_name = card.find_element(
        #         "xpath", './/div[@data-testid="User-Name"]//span'
        #     )

        #     ext_hover_card = False
        #     ext_user_id = False
        #     ext_following = False
        #     ext_followers = False
        #     hover_attempt = 0

        #     while (
        #         not ext_hover_card
        #         or not ext_user_id
        #         or not ext_following
        #         or not ext_followers
        #     ):
        #         try:
        #             actions.move_to_element(el_name).perform()

        #             hover_card = driver.find_element(
        #                 "xpath", '//div[@data-testid="hoverCardParent"]'
        #             )

        #             ext_hover_card = True

        #             while not ext_user_id:
        #                 try:
        #                     raw_user_id = hover_card.find_element(
        #                         "xpath",
        #                         '(.//div[contains(@data-testid, "-follow")]) | (.//div[contains(@data-testid, "-unfollow")])',
        #                     ).get_attribute("data-testid")

        #                     if raw_user_id == "":
        #                         self.user_id = None
        #                     else:
        #                         self.user_id = str(raw_user_id.split("-")[0])

        #                     ext_user_id = True
        #                 except NoSuchElementException:
        #                     continue
        #                 except StaleElementReferenceException:
        #                     self.error = True
        #                     return

        #             while not ext_following:
        #                 try:
        #                     self.following_cnt = hover_card.find_element(
        #                         "xpath", './/a[contains(@href, "/following")]//span'
        #                     ).text

        #                     if self.following_cnt == "":
        #                         self.following_cnt = "0"

        #                     ext_following = True
        #                 except NoSuchElementException:
        #                     continue
        #                 except StaleElementReferenceException:
        #                     self.error = True
        #                     return

        #             while not ext_followers:
        #                 try:
        #                     self.followers_cnt = hover_card.find_element(
        #                         "xpath",
        #                         './/a[contains(@href, "/verified_followers")]//span',
        #                     ).text

        #                     if self.followers_cnt == "":
        #                         self.followers_cnt = "0"

        #                     ext_followers = True
        #                 except NoSuchElementException:
        #                     continue
        #                 except StaleElementReferenceException:
        #                     self.error = True
        #                     return
        #         except NoSuchElementException:
        #             if hover_attempt == 3:
        #                 self.error
        #                 return
        #             hover_attempt += 1
        #             sleep(0.5)
        #             continue
        #         except StaleElementReferenceException:
        #             self.error = True
        #             return

        #     if ext_hover_card and ext_following and ext_followers:
        #         actions.reset_actions()
import contextlib
import json
import random
import time
from datetime import date, timedelta

import requests
from selenium.common.exceptions import (
    NoAlertPresentException,
    UnexpectedAlertPresentException,
)
from selenium.webdriver.common.by import By

from src.browser import Browser
from src.utils import prGreen


class Searches:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def getGoogleTrends(self, wordsCount: int) -> list:
        searchTerms: list[str] = []
        i = 0
        while len(searchTerms) < wordsCount:
            i += 1
            r = requests.get(
                f'https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
            )
            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0][
                "trendingSearches"
            ]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(
                    relatedTopic["query"].lower()
                    for relatedTopic in topic["relatedQueries"]
                )
            searchTerms = list(set(searchTerms))
        del searchTerms[wordsCount : (len(searchTerms) + 1)]
        return searchTerms

    def getRelatedTerms(self, word: str) -> list:
        try:
            r = requests.get(
                f"https://api.bing.com/osjson.aspx?query={word}",
                headers={"User-agent": self.browser.userAgent},
            )
            return r.json()[1]
        except Exception:  # pylint: disable=broad-except
            return []

    def bingSearches(self, numberOfSearches: int, pointsCounter: int = 0):
        print(
            "[BING]",
            f"Starting {self.browser.browserType.capitalize()} Edge Bing searches...",
        )

        i = 0
        search_terms = self.getGoogleTrends(numberOfSearches)
        for word in search_terms:
            i += 1
            print("[BING]", f"{i}/{numberOfSearches}")
            points = self.bingSearch(word)
            if points <= pointsCounter:
                relatedTerms = self.getRelatedTerms(word)[:2]
                for term in relatedTerms:
                    points = self.bingSearch(term)
                    if not points <= pointsCounter:
                        break
            if points > 0:
                pointsCounter = points
            else:
                break
        prGreen(
            f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !"
        )
        return pointsCounter

    def bingSearch(self, word: str):
        self.webdriver.get("https://bing.com")
        self.browser.utils.waitUntilClickable(By.ID, "sb_form_q")
        searchbar = self.webdriver.find_element(By.ID, "sb_form_q")
        searchbar.send_keys(word)
        searchbar.submit()
        time.sleep(random.randint(10, 15))
        stringPoints = None
        with contextlib.suppress(Exception):
            if not self.browser.mobile:
                stringPoints = self.webdriver.find_element(
                    By.ID, "id_rc"
                ).get_attribute("innerHTML")

            else:
                try:
                    self.webdriver.find_element(By.ID, "mHamburger").click()
                    time.sleep(1)
                except UnexpectedAlertPresentException:
                    with contextlib.suppress(NoAlertPresentException):
                        self.webdriver.switch_to.alert.accept()
                        self.webdriver.find_element(By.ID, "mHamburger").click()
                stringPoints = self.webdriver.find_element(
                    By.ID, "fly_id_rc"
                ).get_attribute("innerHTML")

        return int(stringPoints) if stringPoints is not None else 0
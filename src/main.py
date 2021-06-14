from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC, wait 
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup, Tag

from time import sleep

# SOURCE_ADDRESS = "https://www.atptour.com/en/scores/archive/wimbledon/540/2019/results?matchType=singles"
SOURCE_ADDRESS = "https://www.atptour.com/en/scores/current/roland-garros/520/results"

def wait_until_loaded(browser, timeout):
    WebDriverWait(browser, timeout).until(lambda driver: driver.execute_script("return document.readyState") == "complete")


def is_half_point(score_elem: Tag):
    for score_part in score_elem.stripped_strings:
        if "w/o" in score_part.lower() or "ret" in score_part.lower():
            return True


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")

    browser = webdriver.Chrome(options=options)
    browser.get(SOURCE_ADDRESS)

    try:
        wait_until_loaded(browser, 20)
    except TimeoutException:
        print("Timed out waiting for page to load")
        browser.quit()

    soup = BeautifulSoup(browser.page_source, features="html.parser")
    results_container: Tag = soup.find(id="scoresResultsContent").find("table", class_="day-table")
    
    # TODO: half points from walkover or retirement
    # TODO: if we can't parse, just assume no results instead of throwing an error

    player_wins = {}
    round: Tag = None
    for round in results_container.children:
        if round.name == "thead":
            round_name = round.find("th").string
            if "qualifying" in round_name.lower():
                break
        elif round.name == "tbody":
            match: Tag = None
            for match in round.find_all("tr"):
                winner = match.find("td", class_="day-table-name").find("a").string
                score = match.find("td", class_="day-table-score").find("a")
                incr = 0.5 if is_half_point(score) else 1
                player_wins[winner] = player_wins.get(winner, 0) + incr

    browser.quit()

    for k, v in player_wins.items():
        print(f"{k} has won {v} match(es)")


if __name__ == "__main__":
    main()
from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC, wait 
from selenium.common.exceptions import TimeoutException

from typing import List

from bs4 import BeautifulSoup, Tag

from time import sleep

# SOURCE_ADDRESS = "https://www.atptour.com/en/scores/archive/wimbledon/540/2019/results?matchType=singles"
# SOURCE_ADDRESS = "https://www.atptour.com/en/scores/current/halle/500/results"
SOURCE_ADDRESS = "https://www.atptour.com/en/scores/current/roland-garros/520/results"

def wait_until_loaded(browser, timeout):
    WebDriverWait(browser, timeout).until(lambda driver: driver.execute_script("return document.readyState") == "complete")

def is_half_point(score_elem: Tag):
    for score_part in score_elem.stripped_strings:
        if "w/o" in score_part.lower() or "ret" in score_part.lower():
            return True

class Match: 
    def __init__(self, winner: str, loser: str, round_name: str, tags: List[str]=[]):
        self.winner = winner
        self.loser = loser
        self.round_name = round_name
        self.tags = tags

class Team:
    def __init__(self, team_name: str, players: List[str]):
        self.team_name = team_name
        self.players = players

class Tournament:
    def __init__(self, matches: List[Match], teams: List[Team]):
        self.matches = matches
        self.teams = teams


TEAMS = [
    Team("D", ["Novak Djokovic", "Jannik Sinner"]),
    Team("Bab", ["Matteo Berrettini", "Daniil Medvedev"])
]

def parse_tournament(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")

    browser = webdriver.Chrome(options=options)
    browser.get(url)

    try:
        wait_until_loaded(browser, 20)
    except TimeoutException:
        print("Timed out waiting for page to load")
        browser.quit()

    soup = BeautifulSoup(browser.page_source, features="html.parser")
    browser.quit()

    matches: List[Match] = []

    results_container: Tag = soup.find(id="scoresResultsContent").find("table", class_="day-table")

    round: Tag = None
    round_name: str = None
    for round in results_container.children:
        if round.name == "thead":
            round_name = round.find("th").string
            if "qualifying" in round_name.lower():
                break
        elif round.name == "tbody":
            match: Tag = None
            for match in round.find_all("tr"):
                players = match.find_all("td", class_="day-table-name")
                winner = players[0].find("a").string
                loser = players[1].find("a").string

                tags = []
                score = match.find("td", class_="day-table-score").find("a")
                if is_half_point(score):
                    tags.append("default_win")

                matches.append(Match(winner, loser, round_name, tags))


    tourney = Tournament(matches, TEAMS)

    for m in tourney.matches:
        print(f"{m.winner} d. {m.loser}")

if __name__ == "__main__":
    parse_tournament(SOURCE_ADDRESS)
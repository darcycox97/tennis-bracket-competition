from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC, wait 
from selenium.common.exceptions import TimeoutException

from typing import List

from bs4 import BeautifulSoup, Tag

import boto3

from time import sleep

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

    def to_db_item(self):
        item = {
            "winner": self.winner,
            "loser": self.loser,
            "round_name": self.round_name,
            "tags": self.tags
        }

        return item

class Team:
    def __init__(self, team_name: str, players: List[str]):
        self.team_name = team_name
        self.players = players

    def to_db_item(self):
        item = {
            "name": self.team_name,
            "players": self.players
        }

        return item

class Tournament:
    def __init__(self, name: str, matches: List[Match], teams: List[Team]):
        self.name = name
        self.matches = matches
        self.teams = teams

    def to_db_item(self):
        teams = [t.to_db_item() for t in self.teams]
        matches = [m.to_db_item() for m in self.matches]

        item = {
            "tournament_name": self.name,
            "teams": teams,
            "matches": matches
        }

        return item

def parse_tournament(url, tourney_name, teams: List[Team]):
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

    exists: bool = soup.find(id="scoresResultsContent") != None
    if not exists:
        return Tournament(tourney_name, [], teams)
        
    results_container: Tag = soup.find(id="scoresResultsContent").find("table", class_="day-table")

    round: Tag = None
    round_name: str = None
    for round in results_container.children:
        if round.name == "thead":
            round_name = str(round.find("th").string)
            if "qualifying" in round_name.lower():
                break
        elif round.name == "tbody":
            match: Tag = None
            for match in round.find_all("tr"):
                players = match.find_all("td", class_="day-table-name")
                winner = str(players[0].find("a").string)
                loser = str(players[1].find("a").string)

                tags = []
                score = match.find("td", class_="day-table-score").find("a")
                if is_half_point(score):
                    tags.append("default_win")

                matches.append(Match(winner, loser, round_name, tags))


    tourney = Tournament(tourney_name, matches, teams)

    for m in tourney.matches:
        print(f"{m.winner} d. {m.loser} in {m.round_name}. tags={m.tags}")

    return tourney

def create_table(db):
    # TODO: beware this is async
    table = db.create_table(
        TableName='TennisTournament',
        KeySchema=[
            {
                'AttributeName': 'tournament_name',
                'KeyType': 'HASH'  # Partition key
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'tournament_name',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    print(table)


def upload_to_db(tourney: Tournament):
    db = boto3.resource("dynamodb", region_name="us-east-2")
    table = db.Table('TennisTournament')
    tourney_item = tourney.to_db_item()
    table.put_item(Item=tourney_item)

if __name__ == "__main__":

    # TODO: these should be configurable in the web page
    teams = [
        Team("Robert Baker", [
            "Matteo Berrettini",
            "Reilly Opelka",
            "Ugo Humbert",
            "Roger Federer",
            "Andy Murray",
            "Karen Khachanov",
            "Sebastian Korda",
            "Alexander Zverev"]),
        Team("Hendy", [
            "Novak Djokovic",
            "Casper Ruud",
            "Alex de Minaur",
            "Taylor Fritz",
            "Cameron Norrie",
            "Marin Cilic",
            "Richard Gasquet",
            "Kei Nishikori"]),
        Team("Davy Groggs", [
            "Daniil Medvedev",
            "Andrey Rublev",
            "Sam Querrey",
            "Roberto Bautista Agut",
            "Grigor Dimitrov",
            "Jannik Sinner",
            "John Isner",
            "Nick Kyrgios"]),
    ]

    # TODO: these should be command line args
    url = "https://www.atptour.com/en/scores/current/wimbledon/540/results"
    tourney_info = parse_tournament(url, "Wimbledon 2021", teams)
    upload_to_db(tourney_info)


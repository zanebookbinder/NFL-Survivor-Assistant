import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

class GameWinScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.all_games = None

    def fetch(self, week):
        url = f"{self.base_url}{week}.htm"
        resp = requests.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')

    def get_games_df(self, week) -> pd.DataFrame:
        """
        Returns a DataFrame containing all games for the week, with winner, loser, score, etc.
        """
        soup = self.fetch(week)
        tables = []

        for div in soup.find_all("div", class_="game_summary"):
            for table in div.find_all("table", class_="teams"):
                tables.append(table)

        # Heuristic: the main schedule table likely has a specific id or recognizable columns,
        # but to be robust, we scan for a table that has both 'Winner/tie' and 'Loser/tie' (or similar) columns.
        game_results = []
        for table in tables:
            game_results.append(self.parse_game_table(table))
        rows = []

        for tbl in tables:
            winner, winner_score, loser, loser_score = self.parse_game_table(tbl)

            rows.append({
                "week": week,
                "winner": winner,
                "winner_score": winner_score,
                "loser": loser,
                "loser_score": loser_score
            })

        df = pd.DataFrame(rows)
        self.all_games = df if self.all_games is None else pd.concat([self.all_games, df], ignore_index=True)

    def parse_game_table(self, table):
        draw_rows = table.find_all("tr", class_="draw")
        if len(draw_rows) == 2:
            team1 = draw_rows[0].find_all("td")[0].get_text(strip=True)
            score1 = int(draw_rows[0].find_all("td")[1].get_text(strip=True))

            team2 = draw_rows[1].find_all("td")[0].get_text(strip=True)
            score2 = int(draw_rows[1].find_all("td")[1].get_text(strip=True))

            return team1, score1, team2, score2

        # --- Normal winner/loser case ---
        loser_row = table.find("tr", class_="loser")
        winner_row = table.find("tr", class_="winner")

        if not loser_row or not winner_row:
            return '', -1, '', -1

        loser = loser_row.find_all("td")[0].get_text(strip=True)
        loser_score = int(loser_row.find_all("td")[1].get_text(strip=True))

        winner = winner_row.find_all("td")[0].get_text(strip=True)
        winner_score = int(winner_row.find_all("td")[1].get_text(strip=True))

        return winner, winner_score, loser, loser_score

    def get_all_games_df(self) -> pd.DataFrame:
        return self.all_games

base_url = "https://www.pro-football-reference.com/years/2025/week_"
scraper = GameWinScraper(base_url)

for week in range(12, 14):
    scraper.get_games_df(week)
    time.sleep(3)

all_df = scraper.get_all_games_df()
all_df.to_csv('data/all_game_results_df.csv', index=False)
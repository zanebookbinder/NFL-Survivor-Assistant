import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd


class TeamWinScraper:
    def update_wins_column_in_csv(csv_file_path):
        """
        Update the 'wins' column in the specified CSV file with the latest
        win counts scraped from Pro Football Reference.
        """
        team_wins = TeamWinScraper.get_team_wins_dict()
        df = pd.read_csv(csv_file_path)

        # Update the 'wins' column
        def get_wins(team):
            return team_wins.get(team, 0)

        df["current_wins"] = df["team"].apply(get_wins)
        df = df.sort_values(by=["current_wins", "team"], ascending=[False, True])

        # Save the updated CSV
        df.to_csv(csv_file_path, index=False)
        print(f"Updated 'current_wins' column in {csv_file_path}.")

    def get_team_wins_dict():
        """
        Scrape the Pro Football Reference page for the specified year
        and return a dictionary mapping team names to their number of wins.
        """
        # Fetch the page
        nfl_season = datetime.now().year - (datetime.now().month <= 5)
        url = f"https://www.pro-football-reference.com/years/{nfl_season}/"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # The two main division IDs to scrape
        div_ids = ["all_AFC", "all_NFC"]
        team_wins = {}

        for div_id in div_ids:
            div = soup.find("div", id=div_id)
            if not div:
                continue

            table = div.find("table")
            if not table:
                continue

            for row in table.find("tbody").find_all("tr"):
                if "class" in row.attrs and "thead" in row["class"]:
                    continue

                team_cell = row.find("th", {"data-stat": "team"})
                wins_cell = row.find("td", {"data-stat": "wins"})
                ties_cell = row.find("td", {"data-stat": "ties"})

                if team_cell and wins_cell:
                    team_name = (
                        team_cell.get_text(strip=True).replace("*", "").replace("+", "")
                    )
                    wins = wins_cell.get_text(strip=True)
                    ties = ties_cell.get_text(strip=True)
                    if wins.isdigit():
                        team_wins[team_name] = int(wins)

                    if ties.isdigit():
                        team_wins[team_name] += int(ties) * 0.5

        return team_wins


# Example usage:
# scraper = NFLWinScraper()
# wins = scraper.get_team_wins_dict()

# # Sort and print by wins descending
# for team, win_count in sorted(wins.items(), key=lambda x: x[1], reverse=True):
#     print(f"{team}: {win_count}")

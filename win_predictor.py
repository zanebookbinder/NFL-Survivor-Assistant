import pandas as pd
import numpy as np

INJURY_ADJUSTMENTS = {
    'CIN': [[2, 100, -4]], # Joe Burrow injury (9.5 proj to 5.5 est)
}

HOME_TEAM_ADJUSTMENTS = {
    # Best home advantages
    'KC': 1,
    'SEA': 1,
    'PHI': 0.5,
    'GB': 0.5,
    'DEN': 0.5,
    'BUF': 0.5,

    # Bad home advantages
    'JAX': -0.5,
    'LV': -0.5,
    'LAR': -0.5,
    'CAR': -0.5
}

BAD_TEAM_UPSET_RISKINESS_ADJUSTMENTS = {
    'NYG': 1,
    'HOU': 1,
    'MIA': 1,
    'CLE': 1,
    'NE': 0.5,
    'NYJ': 0.5,
    'DAL': 0.5,
    'ATL': 0.5,

    'TEN': -0.5,
    'NO': -0.5,
}

class WinPredictor:
    def __init__(self, csv_path, scale=5.9, home_field_advantage=1.0, current_weight=0.3):
        self.data = pd.read_csv(csv_path)
        self.projected_wins = dict(zip(self.data["abbreviation"], self.data["projected_wins"]))
        self.current_wins = dict(zip(self.data["abbreviation"], self.data["wins_after_week_3"]))

        self.team_wins = {
            team: (current_weight * self.current_wins[team] +
                (1 - current_weight) * self.projected_wins[team])
            for team in self.projected_wins
        }

        self.scale = scale
        self.home_field_advantage = home_field_advantage

    def calculate_win_probability(self, team1, team2, week_number, home_team=None):
        """
        Calculate probability of team1 winning against team2 using a scaled logistic model.

        Args:
            team1 (str): First team name
            team2 (str): Second team name
            home_team (str, optional): Team that is playing at home (team1 or team2)

        Returns:
            float: Probability (0-1) that team1 wins.
        """
        if team1 not in self.team_wins or team2 not in self.team_wins:
            raise ValueError("Both teams must exist in the dataset")

        wins1 = self.team_wins[team1]
        wins2 = self.team_wins[team2]

        # Home field advantage adjustment
        if home_team == team1:
            wins1 += self.home_field_advantage + HOME_TEAM_ADJUSTMENTS.get(team1, 0)
        elif home_team == team2:
            wins2 += self.home_field_advantage + HOME_TEAM_ADJUSTMENTS.get(team2, 0)

        # Injury adjustment
        if team1 in INJURY_ADJUSTMENTS:
            for start_week, end_week, adjustment in INJURY_ADJUSTMENTS[team1]:
                if start_week <= week_number <= end_week:
                    wins1 += adjustment

        if team2 in INJURY_ADJUSTMENTS:
            for start_week, end_week, adjustment in INJURY_ADJUSTMENTS[team2]:
                if start_week <= week_number <= end_week:
                    wins2 += adjustment

        # Riskiness adjustment for potential upsets
        wins1 += BAD_TEAM_UPSET_RISKINESS_ADJUSTMENTS.get(team1, 0)
        wins2 += BAD_TEAM_UPSET_RISKINESS_ADJUSTMENTS.get(team2,0)

        # Scaled logistic function
        diff = (wins1 - wins2) / self.scale
        prob_team1 = 1 / (1 + np.exp(-diff))
        return prob_team1

    def get_probability_table(self, min_diff=-5, max_diff=5):
        """
        Generate a table of win probabilities for a range of win total differences.

        Args:
            min_diff (int): Minimum win difference to display
            max_diff (int): Maximum win difference to display

        Returns:
            dict: Mapping of win difference -> probability that team1 wins
        """
        table = {}
        for diff in range(min_diff, max_diff + 1):
            prob = 1 / (1 + np.exp(-diff / self.scale))
            table[diff] = prob
        return table


class NFLGamePredictor:
    def __init__(self, schedule_csv='data/nfl_schedule.csv', wins_csv='data/nfl_projected_wins.csv', scale=3.5, home_field_advantage=0.5):
        self.schedule = pd.read_csv(schedule_csv)
        self.predictor = WinPredictor(wins_csv, scale, home_field_advantage)

    def add_win_probabilities(self, csv_file_path=None):
        rows = []
        for _, row in self.schedule.iterrows():
            week = row["week"]
            home = row["home_team"]
            away = row["away_team"]

            # Compute probability that home team wins
            prob_home = self.predictor.calculate_win_probability(home, away, week, home_team=home)
            prob_away = 1 - prob_home

            rows.append({
                "week": week,
                "home_team": home,
                "away_team": away,
                "home_win_prob": round(prob_home, 3),
                "away_win_prob": round(prob_away, 3)
            })

        result = pd.DataFrame(rows)

        if csv_file_path:
            result.to_csv(csv_file_path, index=False)
        else:
           return result
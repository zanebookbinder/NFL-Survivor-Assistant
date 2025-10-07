import pandas as pd
import numpy as np
from win_predictor_adjustments_helper import \
    (HOME_TEAM_ADJUSTMENTS, 
     INJURY_ADJUSTMENTS,
     BAD_TEAM_UPSET_RISKINESS_ADJUSTMENTS,
     BYE_WEEK_ADJUSTMENT)

class WinPredictor:
    def __init__(
        self,
        csv_path,
        weeks_played,
        scale=5.9,
        home_field_advantage=1.0,
    ):
        self.data = pd.read_csv(csv_path)
        self.projected_wins = dict(
            zip(self.data["abbreviation"], self.data["projected_wins"])
        )
        self.current_wins = dict(
            zip(self.data["abbreviation"], self.data["current_wins"])
        )

        current_week_weight = weeks_played / 18
        self.team_wins = {
            team: (
                (self.current_wins[team] * current_week_weight)
                + (self.projected_wins[team] * (1 - current_week_weight))
            )
            for team in self.projected_wins
        }

        self.scale = scale
        self.home_field_advantage = home_field_advantage
        self.team_bye_week = self.create_bye_week_map()

    def create_bye_week_map(self, schedule_csv="data/nfl_schedule.csv"):
        schedule = pd.read_csv(schedule_csv)
        teams = set(schedule["home_team"]).union(set(schedule["away_team"]))
        weeks = set(schedule["week"])
        bye_week_map = {}
        for team in teams:
            played_weeks = set(
                schedule.loc[
                    (schedule["home_team"] == team) | (schedule["away_team"] == team),
                    "week",
                ]
            )
            bye_weeks = weeks - played_weeks

            if len(bye_weeks) > 1 or bye_weeks == set():
                print(f"Warning: Team {team} has multiple bye weeks: {bye_weeks}")
                raise ValueError(
                    "Each team should have only one bye week in a standard NFL season."
                )

            bye_week_map[team] = list(bye_weeks)[0] if bye_weeks else None
        return bye_week_map

    def calculate_win_probability(self, home_team, away_team, week_number):
        """
        Calculate probability of home_team winning against away_team using a scaled logistic model.

        Args:
            home_team (str): Home team name
            away_team (str): Away team name
            week_number (int): Current week number

        Returns:
            float: Probability (0-1) that home_team wins.
        """
        if home_team not in self.team_wins or away_team not in self.team_wins:
            raise ValueError("Both teams must exist in the dataset")

        home_score = self.team_wins[home_team]
        away_score = self.team_wins[away_team]

        home_wins_preadjustment = home_score
        away_wins_preadjustment = away_score

        # Home field advantage adjustment
        home_score += self.home_field_advantage + HOME_TEAM_ADJUSTMENTS.get(
            home_team, 0
        )

        # Injury adjustment
        if home_team in INJURY_ADJUSTMENTS:
            for start_week, end_week, adjustment in INJURY_ADJUSTMENTS[home_team]:
                if start_week <= week_number and week_number <= end_week:
                    home_score += adjustment

        if away_team in INJURY_ADJUSTMENTS:
            for start_week, end_week, adjustment in INJURY_ADJUSTMENTS[away_team]:
                if start_week <= week_number and week_number <= end_week:
                    away_score += adjustment

        # Bye week adjustment
        if self.team_bye_week.get(home_team) == week_number - 1:
            home_score += BYE_WEEK_ADJUSTMENT
        if self.team_bye_week.get(away_team) == week_number - 1:
            away_score += BYE_WEEK_ADJUSTMENT

        # Riskiness adjustment for potential upsets
        if home_score <= away_score:
            home_score += BAD_TEAM_UPSET_RISKINESS_ADJUSTMENTS.get(home_team, 0)
        else:
            away_score += BAD_TEAM_UPSET_RISKINESS_ADJUSTMENTS.get(away_team, 0)

        # Scaled logistic function
        diff = (home_score - away_score) / self.scale
        home_prob = 1 / (1 + np.exp(-diff))

        return ({
            "week": week_number,
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": round(home_prob, 4),
            "away_win_prob": round(1 - home_prob, 4),
        }, 
        {
            "week": week_number,
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": round(home_prob, 4),
            "away_win_prob": round(1 - home_prob, 4),
            "home_score": round(home_score, 2),
            "away_score": round(away_score, 2),
            "home_preadjustment": round(home_wins_preadjustment, 2),
            "away_preadjustment": round(away_wins_preadjustment, 2)
        })

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
    def __init__(
        self,
        weeks_played,
        schedule_csv="data/nfl_schedule.csv",
        wins_csv="data/nfl_projected_wins.csv",
        full_calc_path_csv = "data/nfl_schedule_with_probs_fullcalcs.csv",
        scale=3.5,
        home_field_advantage=0.5,
    ):
        self.full_calc_path_csv = full_calc_path_csv
        self.schedule = pd.read_csv(schedule_csv)
        self.predictor = WinPredictor(
            wins_csv, weeks_played, scale, home_field_advantage
        )

    def add_win_probabilities(self, csv_file_path=None):
        rows = []
        calc_rows = []
        for _, row in self.schedule.iterrows():
            week = row["week"]
            home = row["home_team"]
            away = row["away_team"]

            # Compute probability that home team wins
            result_dict, result_dict_with_cals = (
                self.predictor.calculate_win_probability(
                    home, away, week
                )
            )

            rows.append(result_dict)
            calc_rows.append(result_dict_with_cals)

        result = pd.DataFrame(rows)
        calc_result = pd.DataFrame(calc_rows)

        if csv_file_path:
            result.to_csv(csv_file_path, index=False)
        calc_result.to_csv(self.full_calc_path_csv, index=False)
        return result

# n = NFLGamePredictor(4)
# n.add_win_probabilities()

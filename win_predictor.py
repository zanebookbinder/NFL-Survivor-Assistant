import pandas as pd
import numpy as np
import math
from nfl_win_scraper import NFLWinScraper
from win_predictor_adjustments_helper import \
    (HOME_TEAM_ADJUSTMENTS, 
     INJURY_ADJUSTMENTS,
     BAD_TEAM_UPSET_RISKINESS_ADJUSTMENTS,
     BYE_WEEK_ADJUSTMENT,
     TEAMS_TO_AVOID_IN_WEEK_18,
     MOMENTUM_ADJUSTMENTS)

class WinPredictor:
    def __init__(
        self,
        csv_path,
        current_prediction_week,
        scale=5.9,
        home_field_advantage=1.0,
        prediction_decay_halflife=25,
    ):
        self.current_prediction_week = current_prediction_week
        self.scale = scale
        self.home_field_advantage = home_field_advantage
        self.prediction_decay_halflife = prediction_decay_halflife
        self.data = pd.read_csv(csv_path)
        self.projected_wins = dict(
            zip(self.data["abbreviation"], self.data["projected_wins"])
        )
        self.current_wins = dict(
            zip(self.data["abbreviation"], self.data["current_wins"])
        )
        self.team_bye_week = self.create_bye_week_map()

        self.team_wins = {}
        for team, projected in self.projected_wins.items():
            bye_week = self.team_bye_week[team]
            # If the bye week already happened, they’ve played one fewer game
            if bye_week < current_prediction_week:
                team_weeks_played = current_prediction_week - 1
            else:
                team_weeks_played = current_prediction_week

            current_week_weight = team_weeks_played / 17
            self.team_wins[team] = (
                (self.current_wins[team] * current_week_weight)
                + (projected * (1 - current_week_weight))
            )

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

        # Momentum adjustment
        home_score += MOMENTUM_ADJUSTMENTS.get(home_team, 0)
        away_score += MOMENTUM_ADJUSTMENTS.get(away_team, 0)

        # Scaled logistic function
        diff = (home_score - away_score) / self.scale
        home_prob = 1 / (1 + np.exp(-diff))
        away_prob = 1 - home_prob

        # Avoid good teams in week 18 - they might not have anything to play for
        if week_number == 18 and (home_team in TEAMS_TO_AVOID_IN_WEEK_18 or away_team in TEAMS_TO_AVOID_IN_WEEK_18):
            home_prob, away_prob = 0, 0

        adj_home_prob = self.shrink_prob(home_prob, self.current_prediction_week - week_number, self.prediction_decay_halflife)
        adj_away_prob = self.shrink_prob(away_prob, self.current_prediction_week - week_number, self.prediction_decay_halflife)

        base_dict = {
            "week": week_number,
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": round(adj_home_prob, 4),
            "away_win_prob": round(adj_away_prob, 4),
        }

        return ( # Returns two separate dictionaries, one with intermediate stats for debugging
            base_dict,
            {
                **base_dict,
                "home_score": round(home_score, 2),
                "away_score": round(away_score, 2),
                "home_preadjustment": round(home_wins_preadjustment, 2),
                "away_preadjustment": round(away_wins_preadjustment, 2),
            },
        )

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

    def shrink_prob(self, current_prob, weeks_from_now, half_life_weeks):
        if weeks_from_now <= 0 or not current_prob:
            return current_prob  # No adjustment for past or current week
        
        k = math.log(2) / half_life_weeks
        return 0.5 + (current_prob - 0.5) * math.exp(-k * weeks_from_now)

class NFLGamePredictor:
    def __init__(
        self,
        current_prediction_week,
        schedule_csv="data/nfl_schedule.csv",
        wins_csv="data/nfl_projected_wins.csv",
        should_scrape_current_wins=True,
        full_calc_path_csv="data/nfl_schedule_with_probs_fullcalcs.csv",
        scale=3.5,
        home_field_advantage=0.5,
    ):
        self.full_calc_path_csv = full_calc_path_csv
        self.schedule = pd.read_csv(schedule_csv)

        if should_scrape_current_wins:
            NFLWinScraper.update_wins_column_in_csv(wins_csv)
            
        self.predictor = WinPredictor(
            wins_csv, current_prediction_week, scale, home_field_advantage
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

# n = NFLGamePredictor(8)
# n.add_win_probabilities()

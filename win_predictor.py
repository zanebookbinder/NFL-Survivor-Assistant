import pandas as pd
import numpy as np
import math
from nfl_win_scraper import NFLWinScraper
from win_predictor_adjustments_helper import (
    HOME_TEAM_ADJUSTMENTS,
    TEAMS_TO_AVOID_IN_WEEK_18,
    apply_injury_adjustment,
    apply_bye_week_adjustment,
    apply_upset_riskiness_adjustment,
    apply_momentum_adjustment
)

SCHEDULE_CSV = "data/nfl_schedule.csv"
SCHEDULE_WITH_PROBABILITIES_PATH = "data/nfl_schedule_with_probs.csv"
FULL_CALC_PATH_CSV = "data/nfl_schedule_with_probs_fullcalcs.csv"
WINS_CSV = "data/nfl_projected_wins.csv"
SCALE = 3.5
HOME_FIELD_ADVANTAGE = 0.5
PREDICTION_DECAY_HALFLIFE = 25


class NFLWinPredictor:
    def __init__(
        self,
        current_prediction_week,
        should_scrape_current_wins,
    ):
        if should_scrape_current_wins:
            NFLWinScraper.update_wins_column_in_csv(WINS_CSV)

        self.current_prediction_week = current_prediction_week
        self.scale = SCALE
        self.home_field_advantage = HOME_FIELD_ADVANTAGE
        self.prediction_decay_halflife = PREDICTION_DECAY_HALFLIFE
        self.data = pd.read_csv(WINS_CSV)
        self.schedule = pd.read_csv(SCHEDULE_CSV)
        self.projected_wins = dict(
            zip(self.data["abbreviation"], self.data["projected_wins"])
        )
        self.current_wins = dict(
            zip(self.data["abbreviation"], self.data["current_wins"])
        )
        self.team_bye_week = self.create_bye_week_map()
        self.team_wins = self.calculate_team_wins_dict(current_prediction_week)

    def calculate_team_wins_dict(self, current_prediction_week):
        team_wins = {}
        for team, projected in self.projected_wins.items():
            bye_week = self.team_bye_week[team]
            # If the bye week already happened, they’ve played one fewer game
            if bye_week < current_prediction_week:
                team_weeks_played = current_prediction_week - 1
            else:
                team_weeks_played = current_prediction_week

            current_week_weight = team_weeks_played / 17
            team_wins[team] = (self.current_wins[team] * current_week_weight) + (
                projected * (1 - current_week_weight)
            )
        return team_wins

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
        if home_team not in self.team_wins or away_team not in self.team_wins:
            raise ValueError("Both teams must exist in the dataset")

        home_score = home_wins_preadjustment = self.team_wins[home_team]
        away_score = away_wins_preadjustment = self.team_wins[away_team]

        # Home field advantage adjustment
        home_score += self.home_field_advantage + HOME_TEAM_ADJUSTMENTS.get(
            home_team, 0
        )

        # Injury adjustments
        home_score = apply_injury_adjustment(home_team, week_number, home_score)
        away_score = apply_injury_adjustment(away_team, week_number, away_score)

        # Bye week adjustment
        home_score = apply_bye_week_adjustment(
            self.team_bye_week.get(home_team), week_number, home_score
        )
        away_score = apply_bye_week_adjustment(
            self.team_bye_week.get(away_team), week_number, away_score
        )

        home_score, away_score = apply_upset_riskiness_adjustment(home_team, away_team, home_score, away_score)

        # Momentum adjustment
        home_score = apply_momentum_adjustment(home_team, home_score)
        away_score = apply_momentum_adjustment(away_team, away_score)

        # Scaled logistic function
        diff = (home_score - away_score) / self.scale
        home_prob = 1 / (1 + np.exp(-diff))
        away_prob = 1 - home_prob

        # Avoid good teams in week 18 - they might not have anything to play for
        if week_number == 18 and (
            home_team in TEAMS_TO_AVOID_IN_WEEK_18
            or away_team in TEAMS_TO_AVOID_IN_WEEK_18
        ):
            home_prob, away_prob = 0, 0

        adj_home_prob = self.time_dilate_probability(
            home_prob,
            self.current_prediction_week - week_number,
            self.prediction_decay_halflife,
        )
        adj_away_prob = self.time_dilate_probability(
            away_prob,
            self.current_prediction_week - week_number,
            self.prediction_decay_halflife,
        )

        base_dict = {
            "week": week_number,
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": round(adj_home_prob, 4),
            "away_win_prob": round(adj_away_prob, 4),
        }

        return (  # Returns two separate dictionaries, one with intermediate stats for debugging
            base_dict,
            {
                **base_dict,
                "home_score": round(home_score, 2),
                "away_score": round(away_score, 2),
                "home_preadjustment": round(home_wins_preadjustment, 2),
                "away_preadjustment": round(away_wins_preadjustment, 2),
            },
        )

    def time_dilate_probability(self, current_prob, weeks_from_now, half_life_weeks):
        if weeks_from_now <= 0 or not current_prob:
            return current_prob  # No adjustment for past or current week

        k = math.log(2) / half_life_weeks
        return 0.5 + (current_prob - 0.5) * math.exp(-k * weeks_from_now)

    def add_win_probabilities_to_csv(self):
        rows = []
        calc_rows = []
        schedule = pd.read_csv(SCHEDULE_CSV)
        for _, row in schedule.iterrows():
            week = row["week"]
            home = row["home_team"]
            away = row["away_team"]

            # Compute probability that home team wins
            result_dict, result_dict_with_cals = self.calculate_win_probability(
                home, away, week
            )

            rows.append(result_dict)
            calc_rows.append(result_dict_with_cals)

        result = pd.DataFrame(rows)
        calc_result = pd.DataFrame(calc_rows)

        if SCHEDULE_WITH_PROBABILITIES_PATH:
            result.to_csv(SCHEDULE_WITH_PROBABILITIES_PATH, index=False)
        calc_result.to_csv(FULL_CALC_PATH_CSV, index=False)
        return result


# n = NFLWinPredictor(8, True)
# n.add_win_probabilities_to_csv()

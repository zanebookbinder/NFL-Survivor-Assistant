import pandas as pd
import numpy as np
import os
from win_predictor import NFLGamePredictor

SCHEDULE_CSV_PATH = "data/nfl_schedule.csv"
SCHEDULE_WITH_PROBABILITIES_PATH = "data/nfl_schedule_with_probs.csv"
PROJECTED_WIN_CSV_PATH = "data/nfl_projected_wins.csv"
MC_PICKS_OUTPUT_CSV_PREFIX = "nfl_survivor_picks_mc"

ALREADY_CHOSEN_TEAMS = {
    1: [["DEN"], [1], ["L"]],
    2: [["BAL"], [1], ["L"]],
    3: [["SEA"], [1], ["L"]],
    4: [["HOU"], [1], ["L"]],
}

class NFLSurvivorPickerMonteCarlo:
    def __init__(self, games_csv, simulations=100000):
        game_predictor = NFLGamePredictor(SCHEDULE_CSV_PATH, PROJECTED_WIN_CSV_PATH)
        game_predictor.add_win_probabilities(SCHEDULE_WITH_PROBABILITIES_PATH)

        self.games = pd.read_csv(games_csv)
        self.total_weeks = len(self.games["week"].unique())
        self.simulations = simulations

    def do_monte_carlo_simulations(self, output_csv_path=None):
        best_path = None
        best_score = 0

        weeks = sorted(self.games["week"].unique())
        candidates = self.precompute_weekly_candidates(weeks)

        for sim in range(self.simulations):
            if sim and not sim % int(self.simulations / 10):
                print(f"After {sim} simulations, best probability is: {best_score}")

            used_teams = set()
            path = []
            score = 1.0

            for week in weeks:
                teams, opponents, probs = candidates[week]
                mask = np.array([t not in used_teams for t in teams])
                if not mask.any():
                    score = 0
                    break

                available_teams = teams[mask]
                available_probs = probs[mask]  # original win probabilities
                available_opponents = opponents[mask]

                # Weighted random selection
                available_probs_normalized = available_probs / available_probs.sum()
                idx = np.random.choice(
                    len(available_teams), p=available_probs_normalized
                )
                team = available_teams[idx]
                prob = available_probs[idx]
                opponnent = available_opponents[idx]

                remaining_weeks = len(weeks) - weeks.index(week) - 1
                max_possible_score = score * prob * (0.9**remaining_weeks)
                if max_possible_score < best_score:
                    score = 0  # prune path, it cannot beat current best
                    break

                path.append((week, team, opponnent, prob))
                score *= prob
                used_teams.add(team)

            if score > best_score:
                best_score = score
                best_path = path

        result = pd.DataFrame(
            best_path, columns=["week", "pick", "opponent", "win_prob"]
        )

        if output_csv_path:
            current_week = max(ALREADY_CHOSEN_TEAMS.keys()) + 1
            week_folder = f"data/week{current_week}"
            os.makedirs(week_folder, exist_ok=True)

            output_csv_path = f"data/week{current_week}/{output_csv_path}_"
            output_csv_path += str(best_score).replace(".", "")[1:8] + ".csv"
            result.to_csv(output_csv_path, index=False)

        return result

    def precompute_weekly_candidates(self, weeks):
        candidates = {}
        for week in weeks:
            week_games = self.games[self.games["week"] == week]
            if week in ALREADY_CHOSEN_TEAMS:
                teams, probs, opponents = ALREADY_CHOSEN_TEAMS[week]
            else:
                teams, probs, opponents = [], [], []
                for _, row in week_games.iterrows():
                    if row.home_win_prob > 0.63:
                        teams.append(row.home_team)
                        probs.append(row.home_win_prob)
                        opponents.append(row.away_team)
                    if row.away_win_prob > 0.63:
                        teams.append(row.away_team)
                        probs.append(row.away_win_prob)
                        opponents.append(row.home_team)

            candidates[week] = (np.array(teams), np.array(opponents), np.array(probs))
        return candidates


picker = NFLSurvivorPickerMonteCarlo(
    SCHEDULE_WITH_PROBABILITIES_PATH, simulations=1_000_000
)
survivor_picks = picker.do_monte_carlo_simulations(MC_PICKS_OUTPUT_CSV_PREFIX)
print(survivor_picks)

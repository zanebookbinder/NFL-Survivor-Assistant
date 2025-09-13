import pandas as pd
import numpy as np
from win_predictor import NFLGamePredictor

SCHEDULE_CSV_PATH = "data/nfl_schedule.csv"
SCHEDULE_WITH_PROBABILITIES_PATH = "data/nfl_schedule_with_probs.csv"
PROJECTED_WIN_CSV_PATH = "data/nfl_projected_wins.csv"
MC_PICKS_OUTPUT_CSV_PATH = "data/nfl_survivor_picks_mc"


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
            if not sim % int(self.simulations / 25):
                print(f"After {sim} simulations, best probability is: {best_score}")

            used_teams = set()
            path = []
            score = 1.0

            for week in weeks:
                teams, probs = candidates[week]
                mask = np.array([t not in used_teams for t in teams])
                available_teams = teams[mask]
                available_probs = probs[mask]  # original win probabilities

                if len(available_teams) == 0:
                    score = 0
                    break

                # Weighted random selection
                available_probs_normalized = available_probs / available_probs.sum()
                idx = np.random.choice(
                    len(available_teams), p=available_probs_normalized
                )
                team = available_teams[idx]
                prob = available_probs[idx]

                remaining_weeks = len(weeks) - weeks.index(week) - 1
                max_possible_score = score * prob * (0.9**remaining_weeks)
                if max_possible_score < best_score:
                    score = 0  # prune path, it cannot beat current best
                    break

                path.append((week, team, prob))
                score *= prob
                used_teams.add(team)

            if score > best_score:
                best_score = score
                best_path = path

        result = pd.DataFrame(best_path, columns=["week", "pick", "win_prob"])

        if output_csv_path:
            output_csv_path += str(best_score).replace(".", "")[1:8] + ".csv"
            result.to_csv(output_csv_path, index=False)

        return result

    def precompute_weekly_candidates(self, weeks):
        candidates = {}
        for week in weeks:
            week_games = self.games[self.games["week"] == week]
            teams, probs = [], []
            for _, row in week_games.iterrows():
                if row.home_win_prob > 0.7:
                    teams.append(row.home_team)
                    probs.append(row.home_win_prob)
                if row.away_win_prob > 0.7:
                    teams.append(row.away_team)
                    probs.append(row.away_win_prob)

            candidates[week] = (np.array(teams), np.array(probs))
        return candidates


# Example usage:
picker = NFLSurvivorPickerMonteCarlo(
    SCHEDULE_WITH_PROBABILITIES_PATH, simulations=1000000
)
survivor_picks = picker.do_monte_carlo_simulations(MC_PICKS_OUTPUT_CSV_PATH)
print(survivor_picks)

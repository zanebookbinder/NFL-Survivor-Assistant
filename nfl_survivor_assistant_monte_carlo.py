from calendar import week
import pandas as pd
import numpy as np
import os
from win_predictor import NFLWinPredictor
from datetime import datetime
from win_predictor_adjustments_helper import ALREADY_CHOSEN_TEAMS

CHOOSE_THIS_WEEK = {
    # 6: ["ARI", 0.7119, "TEN"]
}

NUM_SIMULATIONS = 10_000_000
SHOULD_SCRAPE_CURRENT_WINS = True
SECOND_CHANCE_WEEK_START = 6

class NFLSurvivorPickerMonteCarlo:
    def __init__(self, simulations=NUM_SIMULATIONS):
        self.simulations = simulations
        self.current_prediction_week = (
            max(ALREADY_CHOSEN_TEAMS.keys()) + 1
            if ALREADY_CHOSEN_TEAMS
            else max(SECOND_CHANCE_WEEK_START, 1)
        )

        game_predictor = NFLWinPredictor(
            self.current_prediction_week, SHOULD_SCRAPE_CURRENT_WINS
        )
        self.games_with_probs = game_predictor.add_win_probabilities_to_csv()
        self.full_dfs_counter = 0
        self.full_dfs_top_paths = set()

    def do_monte_carlo_simulations(self):
        top_paths = set()  # Set of (score, path) tuples
        best_score = float("-inf")
        weeks = [
            x
            for x in sorted(self.games_with_probs["week"].unique())
            if x >= self.current_prediction_week
        ]
        used_teams = set(team for team, _, _ in ALREADY_CHOSEN_TEAMS.values())
        candidates = self.precompute_weekly_candidates(weeks, used_teams)
        week_indices = {week: i for i, week in enumerate(weeks)}
        n_weeks = len(weeks)
        all_teams = np.unique(
            np.concatenate([candidates[w][0] for w in weeks] + [np.array(list(used_teams))])
        )
        team_to_idx = {team: i for i, team in enumerate(all_teams)}
        n_teams = len(all_teams)

        if n_weeks < 6:
            print("Less than 6 weeks remaining, enumerating all possible paths instead.")
            self.simulations = 0

            best_score = self.full_dfs(
                candidates, min(weeks), used_teams, [], 1, best_score=float("-inf")
            )
            top_paths = self.full_dfs_top_paths
            print('Explored ', self.full_dfs_counter, ' paths in full DFS.')

        for sim in range(self.simulations):
            if sim and not sim % int(self.simulations / 10):
                print(f"After {sim} simulations, best probability is: {round(best_score * 100, 5)}%")

            path, score = self.run_simulation(
                best_score if best_score != float("-inf") else 0,
                weeks,
                candidates,
                week_indices,
                n_weeks,
                team_to_idx,
                n_teams,
                used_teams
            )

            if score > 0:
                top_paths.add((score, tuple(path)))
                if score > best_score:
                    best_score = score
                if len(top_paths) > 5000:
                    top_paths = set(sorted(top_paths, key=lambda x: -x[0])[:100])

        # After all simulations, get top 100
        top_paths = sorted(top_paths, key=lambda x: -x[0])[:100]

        all_result_weeks = [
            x
            for x in sorted(self.games_with_probs["week"].unique())
            if x >= SECOND_CHANCE_WEEK_START
        ]
        result = self.save_results(all_result_weeks, top_paths)
        return result

    def run_simulation(
        self, best_score, weeks, candidates, week_indices, n_weeks, team_to_idx, n_teams, used_teams
    ):
        used_mask = np.zeros(n_teams, dtype=bool)
        for team in used_teams:
            used_mask[team_to_idx[team]] = True
        path = []
        score = 1.0

        for week in weeks:
            teams, opponents, probs = candidates[week]
            team_idxs = np.array([team_to_idx[t] for t in teams])
            mask = ~used_mask[team_idxs]
            if not np.any(mask):
                score = 0
                break

            available_teams = teams[mask]
            available_probs = probs[mask]
            available_opponents = opponents[mask]

            available_probs_sum = available_probs.sum()
            if available_probs_sum == 0:
                score = 0
                break
            available_probs_normalized = available_probs / available_probs_sum
            idx = np.random.choice(len(available_teams), p=available_probs_normalized)
            team = available_teams[idx]
            prob = available_probs[idx]
            opponent = available_opponents[idx]

            remaining_weeks = n_weeks - week_indices[week] - 1
            max_possible_score = score * prob * (0.9**remaining_weeks)
            if max_possible_score < best_score:
                score = 0
                break

            path.append((week, team, opponent, prob))
            score *= prob
            used_mask[team_to_idx[team]] = True
        return path, score

    def full_dfs(
        self,
        weekly_candidates,
        week_idx,
        picked_teams,
        path,
        score,
        best_score
    ):
        if week_idx == 19:
            self.full_dfs_counter += 1
            if score > 0:
                self.full_dfs_top_paths.add((score, tuple(path)))
                if score > best_score:
                    best_score = score
                if len(self.full_dfs_top_paths) > 5000:
                    self.full_dfs_top_paths = set(sorted(self.full_dfs_top_paths, key=lambda x: -x[0])[:100])
                
            return best_score

        teams, opponents, probs = weekly_candidates[week_idx]

        if len(teams) == 0:
            self.full_dfs_counter += 1
            return best_score

        # Try each possible team this week
        for team, opponent, prob in zip(teams, opponents, probs):
            if team in picked_teams:
                continue

            next_score = score * prob

            picked_teams.add(team)
            new_path = path + [(week_idx, team, opponent, prob)]

            # Recurse
            best_score = self.full_dfs(
                weekly_candidates, week_idx + 1, picked_teams,
                new_path, next_score, best_score,
            )

            picked_teams.remove(team)

        return best_score


    def save_results(self, weeks, top_paths):
        # Calculate team pick percentages per week
        week_team_counts = {week: {} for week in weeks}
        for _, path in top_paths:
            for week, team, opponent, prob in path:
                old_count = (
                    week_team_counts[week].get(team)[0]
                    if team in week_team_counts[week]
                    else 0
                )
                week_team_counts[week][team] = [old_count + 1, opponent, prob]
        
        # Output formatted results
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_str = f"Top {len(top_paths)} Paths (generated at {timestamp}):\n"
        for week in weeks:
            if not week_team_counts[week]:
                continue
            total = sum(w[0] for w in week_team_counts[week].values())
            week_str = f"Week {week}: "
            sorted_entries = sorted(
                week_team_counts[week].items(), key=lambda item: -item[1][0]
            )
            team_percents = [
                f"{team} over {value[1]} ({int(value[0]/total*100)}% of paths, {int(value[2]*100)}% to win)"
                for team, value in sorted_entries
            ]
            week_str += ", ".join(team_percents)
            output_str += week_str + "\n"
        print(output_str)

        # Output best path as before
        best_score, best_path = top_paths[0]

        previous_picks = [[k, v[0], v[2], v[1]] for k, v in ALREADY_CHOSEN_TEAMS.items()]

        result = pd.DataFrame(
            previous_picks + list(best_path), columns=["week", "pick", "opponent", "win_prob"]
        )

        week_folder = f"data/{'second_chance/' if SECOND_CHANCE_WEEK_START > 0 else 'first_chance/'}week{self.current_prediction_week}/{str(best_score).replace('.', '')[1:8]}"
        os.makedirs(week_folder, exist_ok=True)
        output_csv_path = f"{week_folder}/picks.csv"
        result.to_csv(output_csv_path, index=False)

        # write output_str to a text file in the same folder
        with open(f"{week_folder}/weekly_options.txt", "w") as f:
            f.write(output_str)

        print(result.to_string(index=False))
        return result

    def precompute_weekly_candidates(self, weeks, used_teams):
        candidates = {}
        for week in weeks:
            week_games = self.games_with_probs[self.games_with_probs["week"] == week]
            if week in ALREADY_CHOSEN_TEAMS:
                team, prob, opponent = ALREADY_CHOSEN_TEAMS[week]
                teams, probs, opponents = [team], [prob], [opponent]
            elif week in CHOOSE_THIS_WEEK:
                team, prob, opponent = CHOOSE_THIS_WEEK[week]
                teams, probs, opponents = [team], [prob], [opponent]
            else:
                teams, probs, opponents = [], [], []
                for _, row in week_games.iterrows():
                    if row["home_win_prob"] > 0.6 and row["home_team"] not in used_teams:
                        teams.append(row["home_team"])
                        probs.append(row["home_win_prob"])
                        opponents.append(row["away_team"])
                    if row["away_win_prob"] > 0.6 and row["away_team"] not in used_teams:
                        teams.append(row["away_team"])
                        probs.append(row["away_win_prob"])
                        opponents.append(row.home_team)

            candidates[week] = (np.array(teams), np.array(opponents), np.array(probs))

        return candidates


picker = NFLSurvivorPickerMonteCarlo(simulations=NUM_SIMULATIONS)
survivor_picks = picker.do_monte_carlo_simulations()

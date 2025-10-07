import pandas as pd

class NFLSurvivorPicker:
    def __init__(self, games_csv, pruning_threshold=0.05):
        self.games = pd.read_csv(games_csv)
        self.total_weeks = len(self.games["week"].unique())
        self.pruning_threshold = pruning_threshold  # Skip branches with very low probability

    def pick_team(self):
        weeks = sorted(self.games["week"].unique())

        best_path = []
        best_score = -1

        def dfs(week_idx, picked_teams, path, score):
            nonlocal best_path, best_score

            if week_idx == len(weeks):
                if score > best_score:
                    best_score = score
                    best_path = path[:]
                    print(best_score, path)
                return

            week = weeks[week_idx]
            week_games = self.games[self.games["week"] == week]

            candidates = []
            for _, row in week_games.iterrows():
                if row.home_win_prob > 0.5 and row.home_team not in picked_teams:
                    candidates.append((row.home_team, row.home_win_prob))
                if row.away_win_prob > 0.5 and row.away_team not in picked_teams:
                    candidates.append((row.away_team, row.away_win_prob))

            if not candidates:
                return  # dead end

            # Sort by probability descending
            candidates.sort(key=lambda x: -x[1])

            for team, prob in candidates:
                next_score = score * prob if score > 0 else prob

                # Pruning: skip branches that are unlikely to beat current best
                if best_score > 0 and next_score < best_score * self.pruning_threshold:
                    continue

                picked_teams.add(team)
                dfs(week_idx + 1, picked_teams, path + [(week, team, prob)], next_score)
                picked_teams.remove(team)

        dfs(0, set(), [], 0)
        return pd.DataFrame(best_path, columns=["week", "pick", "win_prob"])

# Example usage:
picker = NFLSurvivorPicker("data/nfl_schedule_with_probs.csv")
survivor_picks = picker.pick_team()
print(survivor_picks)
survivor_picks.to_csv("daa/nfl_survivor_picks.csv", index=False)

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from constants import (
	SCHEDULE_WITH_PROBABILITIES_PATH,
    PROJECTED_WINS_CSV_PATH)

class PredictionEvaluator:
    def __init__(self, results_path, probabilities_path, appreviation_path, threshold=0.60):
        """
        results_df: actual game results
        probs_df: predicted win probabilities
        abbrev_df: mapping team names -> abbreviations
        threshold: probability cutoff (ex. 0.60)
        """
        self.results = pd.read_csv(results_path)
        self.probs = pd.read_csv(probabilities_path)
        self.abbrev = pd.read_csv(appreviation_path)
        self.threshold = threshold

        # Build a mapping: full name -> abbreviation
        self.name_to_abbrev = dict(zip(self.abbrev["team"], self.abbrev["abbreviation"]))

    def _normalize_team_name(self, name):
        """Convert full name to abbreviation if possible."""
        return self.name_to_abbrev.get(name, name)

    def evaluate_week(self, week, verbose):
        """Return (correct_predictions, total_considered) for a given week."""
        survivor_assistant_predictions = self.probs
        if os.path.exists("data/prediction_history/week_{}.csv".format(week)):
            survivor_assistant_predictions = pd.read_csv("data/prediction_history/week_{}.csv".format(week))
        
        week_results = self.results[self.results["week"] == week].copy()
        week_probs = survivor_assistant_predictions[survivor_assistant_predictions["week"] == week].copy()

        correct = 0
        total = 0

        if verbose:
            print('Week ', week)
        for _, game in week_probs.iterrows():
            home = game["home_team"]
            away = game["away_team"]
            home_prob = game["home_win_prob"]
            away_prob = game["away_win_prob"]

            # Only consider predictions above threshold
            if max(home_prob, away_prob) < self.threshold:
                continue  # skip game

            predicted_winner = home if home_prob > away_prob else away
            predicted_loser = away if predicted_winner == home else home

            # Find actual result — convert full names to abbreviations
            for _, result in week_results.iterrows():
                winner = self._normalize_team_name(result["winner"])
                loser = self._normalize_team_name(result["loser"])

                if set([winner, loser]) == set([home, away]):
                    actual_winner = winner
                    break
            else:
                # Game not found — skip it
                continue

            total += 1
            if predicted_winner == actual_winner:
                if verbose:
                    print(f"\t Correct prediction: {predicted_winner} over {predicted_loser}")
                correct += 1
            else:
                if verbose:
                    print(f"\t Bad prediction: {predicted_winner} over {predicted_loser}, actual winner: {actual_winner}")

        return correct, total

    def evaluate_season(self, verbose):
        """Return accuracy by week and overall."""
        weeks = sorted(self.results["week"].unique())

        summary = {}
        total_correct = 0
        total_considered = 0

        for wk in weeks:
            correct, considered = self.evaluate_week(wk, verbose)
            summary[wk] = {
                "correct": correct,
                "considered": considered,
                "accuracy": correct / considered if considered else None
            }
            total_correct += correct
            total_considered += considered

        overall_accuracy = (
            total_correct / total_considered if total_considered else None
        )

        return summary, overall_accuracy, total_considered
    
    def plot_performance_by_threshold(self):
        thresholds = np.arange(0.5, 0.91, 0.05)

        prediction_counts = []
        win_percentages = []

        for t in thresholds:
            
            self.threshold = t
            _, overall_accuracy, games_considered = self.evaluate_season(verbose=False)
            
            prediction_counts.append(games_considered)
            win_percentages.append(overall_accuracy)

        _, ax1 = plt.subplots(figsize=(10, 6))

        # Prediction count line
        ax1.plot(thresholds, prediction_counts, label="Prediction Count")
        ax1.set_xlabel("Threshold")
        ax1.set_ylabel("Prediction Count")

        # Second y-axis for accuracy
        ax2 = ax1.twinx()
        ax2.plot(thresholds, win_percentages, label="Win %", linestyle='--')
        ax2.set_ylabel("Win Percentage")

        plt.title("Prediction Count and Win % by Threshold")
        plt.show()


evaluator = PredictionEvaluator(
                "data/all_game_results_df.csv",
                SCHEDULE_WITH_PROBABILITIES_PATH,
                PROJECTED_WINS_CSV_PATH,
                threshold=0.5
            )

evaluator.plot_performance_by_threshold()

# evaluator = PredictionEvaluator("data/all_game_results_df.csv", 
#                                 SCHEDULE_WITH_PROBABILITIES_PATH, 
#                                 PROJECTED_WINS_CSV_PATH, 
#                                 threshold=0.5)
# week_summary, overall_accuracy = evaluator.evaluate_season()

# print("Week-by-week record:")
# for wk, data in week_summary.items():
#     print(f"Week {wk}: {data['correct']} correct out of {data['considered']}")

# print("\nOverall accuracy:", overall_accuracy)
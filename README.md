# NFL Survivor Assistant Monte Carlo

## Project Overview
This project is a Monte Carlo simulation tool designed to help players optimize their picks in NFL Survivor pools. It uses projected win probabilities and historical data to simulate thousands of possible pick paths, helping users identify the best strategies for advancing through each week of the NFL season.

### Goal
The goal is to maximize your chances of surviving each week in an NFL Survivor pool by making data-driven picks. The tool analyzes all possible pick combinations, taking into account teams already chosen and custom win probability adjustments, to recommend the most optimal paths.

## How It Works
- The simulation runs thousands of possible pick paths for the remaining weeks of the NFL season.
- It uses win probabilities from the schedule and allows for custom adjustments.
- The tool tracks which teams have already been picked and ensures no team is picked twice.
- Results include the top 100 pick paths and team pick percentages for each week.

### WEEKLY UPDATES REQUIRED
1. Adjustments for injuries, momentum, etc. in helper file
2. Update already-picked teams in ALREADY_CHOSEN_TEAMS variable (format is [WinningTeam, 1.0, LosingTeam])
3. Update the wins for each team in nfl_projected_wins.csv (will update that to pull wins automatically soon)

## How to Update Adjustments
Adjustments to win probabilities can be made in the `win_predictor_adjustments_helper.py` file. This file allows you to:
- Change the win probability for specific games or teams.
- Add new adjustments as the season progresses or as new information becomes available.

After updating adjustments, rerun the simulation to see the impact on recommended picks.

## How to Update Already-Picked Teams
Already-picked teams are tracked in the `ALREADY_CHOSEN_TEAMS` dictionary in `nfl_survivor_assistant_monte_carlo.py`. To update:
- Add or modify entries in the dictionary for each week, using the format:
  ```python
  ALREADY_CHOSEN_TEAMS = {
      1: [["DEN"], [1], ["L"]],
      2: [["BAL"], [1], ["L"]],
      # ...
  }
  ```
- Each entry should specify the team picked, the week, and the team played (or just "L" for loser)

## Running the Simulation
1. Ensure your schedule and projected wins CSV files are up to date in the `data/` directory.
2. Update adjustments and already-picked teams as needed.
3. Run `nfl_survivor_assistant_monte_carlo.py` to generate pick recommendations and statistics.
4. Results will be saved in the appropriate `data/weekX/` folder.

## Output
- **Top Paths:** The best 100 pick paths found by the simulation.
- **Team Percentages:** The percentage of paths in which each team is picked each week.
- **CSV Output:** The best path is saved as a CSV for easy review.
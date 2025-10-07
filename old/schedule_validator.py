import pandas as pd

# Load schedule CSV
schedule = pd.read_csv("nfl_schedule_unique.csv")  # replace with your csv filename

# Check for duplicate rows
duplicates = schedule.duplicated(subset=["week", "home_team", "away_team"])
if duplicates.any():
    print("❌ Duplicate games found:")
    print(schedule[duplicates])
else:
    print("✅ No duplicate games found.")

# Count appearances for each team
team_counts = (
    pd.concat([schedule["home_team"], schedule["away_team"]])
    .value_counts()
    .sort_index()
)

# Check if every team has exactly 17 games
bad_counts = team_counts[team_counts != 17]
if not bad_counts.empty:
    print("❌ Teams with incorrect number of games:")
    print(bad_counts)
else:
    print("✅ Every team appears in exactly 17 games.")

# Check for invalid rows (same team playing itself)
invalid_games = schedule[schedule["home_team"] == schedule["away_team"]]
if not invalid_games.empty:
    print("❌ Invalid games where a team plays itself:")
    print(invalid_games)
else:
    print("✅ No invalid self-match games.")

# Check weekly game counts
weekly_counts = schedule.groupby("week").size()
invalid_weeks = weekly_counts[weekly_counts != 16]
if not invalid_weeks.empty:
    print("❌ Weeks with incorrect number of games:")
    print(invalid_weeks)
else:
    print("✅ Every week has exactly 16 games.")

# Show each team's opponents by week
print("\n--- Team schedules ---")
for team in sorted(team_counts.index):
    games = schedule[(schedule.home_team == team) | (schedule.away_team == team)]
    opponents = []
    for _, row in games.sort_values("week").iterrows():
        if row.home_team == team:
            opponents.append(f"W{row.week}: vs {row.away_team}")
        else:
            opponents.append(f"W{row.week}: @ {row.home_team}")
    print(f"\n{team} ({len(opponents)} games):")
    for opp in opponents:
        print("  ", opp)
# WEEKLY - NEED TO UPDATE
INJURY_ADJUSTMENTS = {
    # Season-long injuries
    "CIN": [[2, 100, -3.5]],  # Joe Burrow injury (9.5 projected wins to 6)
    "ARI": [[3, 100, -0.25]],  # James Conner injury
    "SF": [[3, 100, -0.5], [6, 100, -0.25]],  # Nick Bosa injury + Fred Warner injury
    "NYG": [[4, 100, -0.75]],  # Nabers injury
    "MIA": [[4, 100, -0.5]],  # Tyreek Hill
    "TB": [[7, 100, -0.5]],  # Mike Evans injury
    # Temporary injuries (UPDATE THE END WEEKS)
    "LAR": [[7, 8, -0.75]],  # Puka Nakua injury
    "WAS": [[7, 8, -2.5]],  # Jayden Daniels injury
    # Old injuries
    #  "DAL": [[3, 6, -0.75]],  # CeeDee Lamb injury
    # "BAL": [[4, 7, -4.0]],  # Lamar Jackson injury
}

MOMENTUM_ADJUSTMENTS = {
    "IND": 1,
    "KC": 1,
    "NE": 1,
    "CAR": 0.75,
    "CHI": 0.75,
    "DEN": 0.75,
    "NYG": 0.5,
    "LV": -0.5,
    "MIA": -0.5,
    "NYJ": -0.5,
    "BAL": -1,
}

UPSET_RISKINESS_ADJUSTMENTS = {
    "NYG": 1,
    "DAL": 1,
    "CAR": 1,
    "ATL": 1,
    "HOU": 0.5,
    "CLE": 0.5,
    "CIN": 0.5,
    "MIA": -0.5,
    "TEN": -0.5,
    "NYJ": -0.5,
    "LV": -0.5,
}

TEAMS_TO_AVOID_IN_WEEK_18 = ["BUF", "KC", "PHI", "IND", "TB"]

# STATIC - SHOULD NOT CHANGE
HOME_TEAM_ADJUSTMENTS = {
    # Best home advantages
    "KC": 1,
    "SEA": 1,
    "PHI": 0.5,
    "GB": 0.5,
    "BUF": 0.5,
    # Bad home advantages
    "JAX": -0.5,
    "LV": -0.5,
    "LAR": -0.5,
    "CAR": -0.5,
}

BYE_WEEK_ADJUSTMENT = 0.75


def apply_injury_adjustment(team_name, week_number, current_score):
    if team_name in INJURY_ADJUSTMENTS:
        for start_week, end_week, adjustment in INJURY_ADJUSTMENTS[team_name]:
            if start_week <= week_number and week_number <= end_week:
                current_score += adjustment
    return current_score


def apply_bye_week_adjustment(team_bye_week, current_week_number, current_score):
    if team_bye_week == current_week_number - 1:
        current_score += BYE_WEEK_ADJUSTMENT
    return current_score


def apply_upset_riskiness_adjustment(home_team, away_team, home_score, away_score):
    if home_score <= away_score:
        home_score += UPSET_RISKINESS_ADJUSTMENTS.get(home_team, 0)
    else:
        away_score += UPSET_RISKINESS_ADJUSTMENTS.get(away_team, 0)

    return home_score, away_score

def apply_momentum_adjustment(team_name, current_score):
    if team_name in MOMENTUM_ADJUSTMENTS:
        current_score += MOMENTUM_ADJUSTMENTS[team_name]
    return current_score
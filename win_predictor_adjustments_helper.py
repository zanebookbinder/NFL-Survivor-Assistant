# WEEKLY - NEED TO UPDATE
INJURY_ADJUSTMENTS = {
    # Season-long injuries
    "CIN": [[2, 100, -3.5]],  # Joe Burrow (9.5 projected wins to 6)
    "ARI": [[3, 100, -0.25]],  # James Conner
    "SF": [[3, 100, -0.5], [6, 100, -0.25]],  # Nick Bosa + Fred Warner

    # DART CONCUSSION INCLUDED HERE
    "NYG": [[4, 100, -0.75], [8, 100, -0.5], [10, 11, -1.5]],  # Nabers, Skattebo
    "MIA": [[4, 100, -0.5]],  # Tyreek Hill
    "TB": [[7, 100, -0.5]],  # Mike Evans
    "GB": [[9, 100, -0.25]],  # Tucker Kraft
    "TEN": [[11, 100, -0.25]],  # Calvin Ridley

    # Temporary injuries (UPDATE THE END WEEKS)
    "WAS": [[10, 13, -2]],  # Jayen Daniels
    "PIT": [[11, 12, -2.0]],  # Aaron Rodgers
}

MOMENTUM_ADJUSTMENTS = {
    "NE": 1,
    "DEN": 1,
    "LAR": 1,

    "CHI": 0.75,
    "BUF": 0.75,

    "IND": 0.5,
    "SEA": 0.5,
    "JAX": 0.5,
    "SF": 0.5,
    "BAL": 0.5,

    "DAL": -0.5,
    "NO": -0.5,
    "NYG": -0.5,
    "CIN": -0.5,

    "NYJ": -0.75,
    "LV": -0.75,
    "TEN": -0.75,
    "WAS": -0.75,
}

UPSET_RISKINESS_ADJUSTMENTS = {
    "DAL": 1,
    "CAR": 1,
    "CIN": 1,
    "ATL": 0.75,
    "HOU": 0.75,
    "MIA": 0.5,

    "CLE": 0,
    "NO": 0,

    "NYJ": -0.5,
    "NYG": -0.5,
    "LV": -0.75,
    "TEN": -0.75,
}

TEAMS_TO_AVOID_IN_WEEK_18 = ["BUF", "PHI", "IND", "TB", "NE", "LAR"]

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

def apply_injury_adjustment(team_name, week_number, current_score):
    if team_name in INJURY_ADJUSTMENTS:
        for start_week, end_week, adjustment in INJURY_ADJUSTMENTS[team_name]:
            if start_week <= week_number and week_number <= end_week:
                current_score += adjustment
    return current_score


BYE_WEEK_ADJUSTMENT = 0.75
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

divisions = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LV", "LAC"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "LAR", "SF", "SEA"],
}

DIVISIONAL_UNDERDOG_MATCHUP_ADJUSTMENT = 0.5
def apply_divisional_underdog_adjustment(home_team, away_team, home_score, away_score):
    for _, teams in divisions.items():
        if home_team in teams and away_team in teams:
            if home_score < away_score:
                home_score += DIVISIONAL_UNDERDOG_MATCHUP_ADJUSTMENT
            elif away_score < home_score:
                away_score += DIVISIONAL_UNDERDOG_MATCHUP_ADJUSTMENT

            return home_score, away_score
    return home_score, away_score

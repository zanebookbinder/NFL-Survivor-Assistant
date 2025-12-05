# WEEKLY - NEED TO UPDATE
ALREADY_CHOSEN_TEAMS = {
    6: ["GB", 1.0, "CIN"],
    7: ["KC", 1.0, "LV"],
    8: ["IND", 1.0, "TEN"],
    9: ["LAR", 1.0, "NO"],
    10: ["DEN", 1.0, "LV"],
    11: ["BAL", 1.0, "CLE"],
    12: ["DET", 1.0, "NYG"],
    13: ["LAC", 1.0, "LV"],
}

INJURY_ADJUSTMENTS = {
    # Season-long injuries

    "ARI": [[3, 100, -0.25]],  # James Conner
    "SF": [[3, 100, -0.5], [6, 100, -0.25]],  # Nick Bosa + Fred Warner

    "NYG": [[4, 100, -0.75], [8, 100, -0.5]],  # Nabers, Skattebo
    "MIA": [[4, 100, -0.5]],  # Tyreek Hill
    "TB": [[7, 100, -0.5]],  # Mike Evans
    "GB": [[9, 100, -0.25]],  # Tucker Kraft
    "TEN": [[11, 100, -0.25]],  # Calvin Ridley

    # Temporary injuries (UPDATE THE END WEEKS)
    "MIN": [[13,14, -0.25]],  # Aaron Jones
    "WAS": [[10, 14, -2]],  # Jayen Daniels
    "PIT": [[11, 14, -2.0]],  # Aaron Rodgers
}

MOMENTUM_ADJUSTMENTS = {
    "NE": 1,
    "DEN": 1,
    "CHI": 1,
    "SEA": 1,
    "JAX": 1,

    "SF": 0.75,
    "CIN": 0.75,
    "DAL": 0.75,
    "LAR": 0.5,

    "CLE": 0.25,

    "BAL": 0,

    "NYJ": -0.5,
    "KC": -0.5,
    "NO": -0.75,
    "NYG": -0.75,

    "LV": -1,
    "TEN": -1,
    "WAS": -1,
}

UPSET_RISKINESS_ADJUSTMENTS = {
    "DAL": 1,
    "CAR": 1,
    "HOU": 1,
    "CIN": 1,
    "ATL": 0.75,

    "NO": 0,
    "NYG": 0,
    
    "CLE": -0.75,
    "NYJ": -0.75,
    "LV": -1,
    "TEN": -1,
}

TEAMS_TO_AVOID_IN_WEEK_18 = ["DEN", "NE", "LAR"]

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

# WEEKLY - NEED TO UPDATE
INJURY_ADJUSTMENTS = {
    # Season-long injuries
    "CIN": [[2, 100, -3.5]],  # Joe Burrow injury (9.5 proj to 6)
    "ARI": [[3, 100, -0.25]],  # James Conner injury
    "SF": [[3, 100, -0.5]],  # Nick Bosa injury
    "NYG": [[4, 100, -0.5]],  # Nabers injury

    # Temporary injuries (UPDATE THE END WEEKS)
    "DAL": [[3, 6, -0.75]],  # CeeDee Lamb injury
    "BAL": [[4, 6, -4.0]],  # Lamar Jackson injury
}

BAD_TEAM_UPSET_RISKINESS_ADJUSTMENTS = {
    "NYG": 1,
    "HOU": 1,
    "MIA": 1,
    "CLE": 1,
	"DAL": 0.75,
    "NE": 0.5,
    "NYJ": 0.5,
    "ATL": 0.5,
	
    "TEN": -0.5,
}

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

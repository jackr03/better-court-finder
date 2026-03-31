import os

VENUE_MAP = {
	'sugden-sports-centre': 'Sugden Sports Centre',
	'ardwick-sports-hall': 'Ardwick Sports Hall'
}

# Venue slugs
SUGDEN_SPORTS_CENTRE = 'sugden-sports-centre'
ARDWICK_SPORTS_HALL = 'ardwick-sports-hall'

# Activity slugs
BADMINTON_40MIN = 'badminton-40min'
BADMINTON_60MIN = 'badminton-60min'

# File locations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURTS_DB_PATH = os.path.join(BASE_DIR, '../../data/courts.db')
BOT_CONFIG_PATH = os.path.join(BASE_DIR, '../../data/bot_config.toml')

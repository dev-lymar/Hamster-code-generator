# Supported languages
SUPPORTED_LANGUAGES = ['en', 'ru', 'uk', 'sk', 'es', 'fr', 'tr', 'ar', 'de', 'fa', 'ur', 'hi']

ACHIEVEMENTS = [
    "newcomer", "key_seeker",
    "bonus_hunter", "code_expert",
    "key_master", "elite_player",
    "game_legend", "absolute_leader"
]


GAMES = [
    'Pin Out Master',
    'Count Masters',
    'Hide Ball',
    'Bouncemasters',
    'Merge Away',
    'Stone Age',
    'Train Miner',
    'Mow and Trim',
    'Chain Cube 2048',
    'Fluff Crusade',
    'Polysphere',
    'Twerk Race 3D',
    'Zoopolis',
    'Tile Trio'
]

STATUS_LIMITS = {
    'free': {
        'daily_limit': 2, 'interval_minutes': 60,
        'safety_daily_limit': 1, 'safety_interval_minutes': 240
    },
    'friend': {'daily_limit': 5, 'interval_minutes': 10},
    'premium': {
        'daily_limit': 4, 'interval_minutes': 10,
        'safety_daily_limit': 2, 'safety_interval_minutes': 240
    }
}

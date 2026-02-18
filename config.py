"""
Configuration and constants for SlotBot
"""
import os
from typing import Set

# Telegram Bot Token
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# File paths
SCORES_FILE = "scores.json"
USERS_FILE = "users.json"
DUELS_FILE = "duels.json"

# Game constants
WIN_VALUES: Set[int] = {1, 22, 43, 64}
CURRENT_JSON_VERSION = 2

# Debug and Safety
DEBUG_MODE = False
SLOT_BLOCKED = False

# Domain Expansion timing (in seconds)
DOMAIN_EXPANSION_DURATION = 4 * 60 + 11  # 4 minutes 11 seconds
DOMAIN_EXPANSION_MESSAGE_WINDOW = 10  # Messages to activate after triple

# ELO calculation constant
ELO_K_FACTOR = 32

# Backup settings
MAX_BACKUPS = 10
BACKUP_INTERVAL_HOURS = 12

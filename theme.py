"""
theme.py
========
Central place for colors/fonts/sizes so every screen looks consistent.
Change values here later to re-skin the whole app in one place.

v2 - refreshed to a more professional "fintech" look: a deep teal brand
color, a dark sidebar for the app shell (Dashboard/Transactions), and
dedicated income/expense accent colors used throughout the money screens.
"""

import os

# ---------------------------------------------------------------------------
# Brand / primary palette
# ---------------------------------------------------------------------------
COLOR_PRIMARY = "#0F6D5C"         # deep teal - professional, "money" without being neon
COLOR_PRIMARY_HOVER = "#0B5546"
COLOR_PRIMARY_LIGHT = "#E7F3F0"   # soft tint, used for side panel/highlights
COLOR_ACCENT = "#D9A441"          # muted gold, matches the coin in the logo

# Status colors
COLOR_DANGER = "#C0392B"
COLOR_DANGER_HOVER = "#992E23"
COLOR_INCOME = "#1E8E5A"          # green - money in
COLOR_INCOME_LIGHT = "#E5F5EC"
COLOR_EXPENSE = "#C0392B"         # red - money out
COLOR_EXPENSE_LIGHT = "#FBEAE8"
COLOR_WARNING = "#C77B15"
COLOR_WARNING_LIGHT = "#FBF0DF"

# Surfaces
COLOR_BG = "transparent"
COLOR_BG_APP = "#F4F6F7"          # app-shell background behind cards
COLOR_CARD_BG = "#FFFFFF"
COLOR_BORDER = "#E3E7E6"

# Sidebar (dark shell used by Dashboard / Transactions / etc.)
COLOR_SIDEBAR_BG = "#12211E"
COLOR_SIDEBAR_TEXT = "#CFE3DC"
COLOR_SIDEBAR_TEXT_MUTED = "#7E9690"
COLOR_SIDEBAR_ACTIVE = "#1B4A3E"
COLOR_SIDEBAR_HOVER = "#173A31"

# Text
COLOR_TEXT_MUTED = "gray45"
COLOR_TEXT_DARK = "#182422"

# ---------------------------------------------------------------------------
# Fonts (family, size)
# ---------------------------------------------------------------------------
FONT_APP_NAME = ("Segoe UI", 22, "bold")
FONT_TITLE = ("Segoe UI", 26, "bold")
FONT_PAGE_TITLE = ("Segoe UI", 24, "bold")
FONT_SUBTITLE = ("Segoe UI", 14)
FONT_FIELD_LABEL = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 13)
FONT_SMALL = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 14, "bold")
FONT_LINK = ("Segoe UI", 12, "underline")
FONT_STAT_VALUE = ("Segoe UI", 24, "bold")
FONT_STAT_LABEL = ("Segoe UI", 12)
FONT_SECTION_TITLE = ("Segoe UI", 16, "bold")
FONT_SIDEBAR_ITEM = ("Segoe UI", 13, "bold")
FONT_TABLE_HEADER = ("Segoe UI", 11, "bold")
FONT_TABLE_CELL = ("Segoe UI", 12)

# ---------------------------------------------------------------------------
# Sizes
# ---------------------------------------------------------------------------
WINDOW_MIN_SIZE = (1100, 700)
ENTRY_WIDTH = 320
ENTRY_HEIGHT = 42
BUTTON_WIDTH = 320
BUTTON_HEIGHT = 44
CORNER_RADIUS = 10
SIDEBAR_WIDTH = 220

# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")

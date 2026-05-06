"""
Flappy Bird — Cinematic Visual Overhaul Edition
All original gameplay mechanics preserved.
Visual enhancements:
  - Volumetric multi-layer sky with atmospheric haze and god rays
  - Realistic billowing clouds with soft depth layers and rim lighting
  - Metallic chrome pipes with rivets, animated shine, and specular highlights
  - Cinematic main menu with neon particle field and animated title card
  - Enhanced bird with feather shading, expression, and dynamic shadow
  - Cobblestone ground with animated grass tufts and edge glow
  - Glassmorphic HUD with animated score rings
  - Post-processing vignette and chromatic-aberration-style edge glow
  - Improved particle system with sparkle trails and ember drift
"""

import os
import sys
import json
import random
import math
import time
import shutil
import array
from collections import deque

import pygame

# ----------------------------- Configuration ---------------------------------
WIDTH, HEIGHT = 480, 720
CAPTION = "Flappy Bird — Cinematic Edition"
FPS = 60

# Colors
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
UI_BG  = (8, 10, 22)

# Sky — day: rich atmospheric layers
DAY_SKY_ZENITH  = (8,  40, 120)
DAY_SKY_MID     = (30, 110, 210)
DAY_SKY_HORIZON = (140, 200, 255)
DAY_SKY_HAZE    = (220, 235, 255)

# Sky — night
NIGHT_SKY_ZENITH = (2,   3,  18)
NIGHT_SKY_MID    = (6,  16,  52)
NIGHT_SKY_BOT    = (5,  32,  28)
NIGHT_HORIZON    = (12,  24,  60)

# Ground — richer palette
GROUND_COBBLE_A = (90, 78, 65)
GROUND_COBBLE_B = (72, 62, 52)
GROUND_GRASS_A  = (55, 170, 45)
GROUND_GRASS_B  = (38, 130, 28)
GROUND_EDGE     = (70, 200, 55)
GROUND_H        = 68

# Pipe — chrome/steel
PIPE_CHROME_A   = (80, 180, 60)
PIPE_CHROME_B   = (45, 130, 35)
PIPE_CHROME_C   = (20,  85, 18)
PIPE_SHINE      = (180, 255, 140)
PIPE_RIM_A      = (130, 230, 90)
PIPE_RIM_B      = (25, 100, 20)
PIPE_RIVET      = (55, 150, 40)

# UI / Accents
NEON_GOLD   = (255, 215, 60)
NEON_CYAN   = (60, 230, 255)
NEON_PINK   = (255, 80, 160)
NEON_GREEN  = (80, 255, 130)

# Gameplay tuning (unchanged from original)
GRAVITY              = 0.5
FLAP_STRENGTH        = -7.5
BASE_PIPE_SPEED      = 3.2
PIPE_WIDTH           = 80
PIPE_GAP_MIN         = 130
PIPE_GAP_MAX         = 200
POWERUP_SIZE         = 24
POWERUP_DURATION_SEC = 8
PIPE_SPAWN_INTERVAL  = 1.5

PARTICLE_LIMIT    = 350
SHAKE_DURATION    = 0.35
CAMERA_SHAKE_MAG  = 8
START_PIPE_COUNT  = 3
START_GRACE_SEC   = 2.2
START_SPEED_SCALE = 0.78

BIRD_HITBOX_SCALE_X = 0.34
BIRD_HITBOX_SCALE_Y = 0.29

EXTREME_GAP_MIN   = 105
EXTREME_GAP_MAX   = 175
EXTREME_GAP_SWING = (18, 32)
EXTREME_TOP_SWING = (16, 34)

HIGH_SCORES_FILE = "high_scores.json"
STATS_FILE       = "stats.json"
SETTINGS_FILE    = "settings.json"
SAVE_FILE        = "save.json"

ASSETS = {
    "bird_black":  "bird_black.png",
    "bird_blue":   "bird_blue.png",
    "bird_red":    "bird_red.png",
    "flap":        "flap.wav",
    "hit":         "hit.wav",
    "power":       "powerup.wav",
    "score":       "score.wav",
    "bg_music":    "bg_music.mp3"
}

BIRD_KEYS = ["black", "blue", "red", "yellow"]
BIRD_COLORS = {
    "black":  (55,  55,  70),
    "blue":   (20, 130, 255),
    "red":    (235,  35,  35),
    "yellow": (255, 210,  30)
}
BIRD_SHINE = {
    "black":  (140, 140, 165),
    "blue":   (140, 215, 255),
    "red":    (255, 145, 120),
    "yellow": (255, 255, 170)
}
BIRD_SECONDARY = {
    "black":  (25,  25,  38),
    "blue":   (15,  80, 210),
    "red":    (175,  15,  15),
    "yellow": (215, 145,  10)
}

BG_OPTIONS        = ["day", "night"]
TRAIL_OPTIONS = [
    ("none",  "None",  None),
    ("bird",  "Match", None),
    ("gold",  "Gold",  NEON_GOLD),
    ("cyan",  "Cyan",  NEON_CYAN),
    ("pink",  "Pink",  NEON_PINK),
    ("lime",  "Lime",  NEON_GREEN),
    ("pearl", "Pearl", (245, 245, 255)),
]
TRAIL_KEYS = [key for key, _, _ in TRAIL_OPTIONS]
TRAIL_COLORS = {key: color for key, _, color in TRAIL_OPTIONS}

# Tune all shop prices from one place.
SHOP_PRICE_MULTIPLIER = 2
QUEST_REWARD_MULTIPLIER = 0.75

def scale_cost_map(costs, multiplier=SHOP_PRICE_MULTIPLIER):
    return {key: value * multiplier for key, value in costs.items()}

def scale_accessory_options(options, multiplier=SHOP_PRICE_MULTIPLIER):
    return {
        category: [{**item, "cost": item["cost"] * multiplier} for item in items]
        for category, items in options.items()
    }

def scale_quest_reward(value, multiplier=QUEST_REWARD_MULTIPLIER):
    return max(1, int(round(value * multiplier)))

def scale_quest_reward_list(values, multiplier=QUEST_REWARD_MULTIPLIER):
    return [scale_quest_reward(value, multiplier) for value in values]

BIRD_COSTS = scale_cost_map({
    "yellow": 0,
    "black": 160,
    "blue": 240,
    "red": 320,
})
BG_COSTS = scale_cost_map({
    "day": 0,
    "night": 480,
})
TRAIL_COSTS = scale_cost_map({
    "none": 0,
    "bird": 0,
    "gold": 140,
    "cyan": 180,
    "pink": 220,
    "lime": 250,
    "pearl": 300,
})
ACCESSORY_SHOP_UNLOCK_COST = 1000 * SHOP_PRICE_MULTIPLIER
ACCESSORY_CATEGORIES = [
    {"key": "hat", "label": "Headwear", "tab": "Hats", "accent": (255, 218, 120)},
    {"key": "neckwear", "label": "Neckwear", "tab": "Neck", "accent": (255, 140, 140)},
    {"key": "face", "label": "Face Gear", "tab": "Face", "accent": (130, 235, 255)},
    {"key": "wings", "label": "Wing Styles", "tab": "Wings", "accent": (155, 255, 175)},
    {"key": "eyes", "label": "Eye Colors", "tab": "Eyes", "accent": (210, 185, 255)},
]
ACCESSORY_CATEGORY_ORDER = [category["key"] for category in ACCESSORY_CATEGORIES]
ACCESSORY_CATEGORY_LABELS = {category["key"]: category["label"] for category in ACCESSORY_CATEGORIES}
ACCESSORY_TAB_LABELS = {category["key"]: category["tab"] for category in ACCESSORY_CATEGORIES}
ACCESSORY_CATEGORY_ACCENTS = {category["key"]: category["accent"] for category in ACCESSORY_CATEGORIES}
ACCESSORY_OPTIONS = scale_accessory_options({
    "hat": [
        {"id": "none", "label": "Bare", "cost": 0},
        {"id": "beanie", "label": "Beanie", "cost": 340},
        {"id": "cowboy", "label": "Cowboy", "cost": 520},
        {"id": "top_hat", "label": "Top Hat", "cost": 680},
        {"id": "crown", "label": "Crown", "cost": 960},
        {"id": "propeller", "label": "Prop Cap", "cost": 1200},
    ],
    "neckwear": [
        {"id": "none", "label": "None", "cost": 0},
        {"id": "red_scarf", "label": "Red Scarf", "cost": 280},
        {"id": "sky_scarf", "label": "Sky Scarf", "cost": 360},
        {"id": "bow_tie", "label": "Bow Tie", "cost": 420},
        {"id": "necktie", "label": "Necktie", "cost": 520},
        {"id": "royal_scarf", "label": "Royal", "cost": 780},
    ],
    "face": [
        {"id": "none", "label": "Clear", "cost": 0},
        {"id": "round_glasses", "label": "Rounds", "cost": 390},
        {"id": "monocle", "label": "Monocle", "cost": 460},
        {"id": "sunglasses", "label": "Shades", "cost": 620},
        {"id": "aviators", "label": "Aviators", "cost": 760},
        {"id": "visor", "label": "Visor", "cost": 980},
    ],
    "wings": [
        {"id": "classic", "label": "Classic", "cost": 0},
        {"id": "rose", "label": "Rose", "cost": 420},
        {"id": "frost", "label": "Frost", "cost": 540},
        {"id": "emerald", "label": "Emerald", "cost": 680},
        {"id": "royal", "label": "Royal", "cost": 860},
        {"id": "shadow", "label": "Shadow", "cost": 1100},
    ],
    "eyes": [
        {"id": "classic", "label": "Classic", "cost": 0},
        {"id": "amber", "label": "Amber", "cost": 260},
        {"id": "emerald", "label": "Emerald", "cost": 320},
        {"id": "ruby", "label": "Ruby", "cost": 380},
        {"id": "violet", "label": "Violet", "cost": 450},
        {"id": "neon", "label": "Neon", "cost": 640},
    ],
})
ACCESSORY_DEFAULTS = {category: ACCESSORY_OPTIONS[category][0]["id"] for category in ACCESSORY_CATEGORY_ORDER}
ACCESSORY_KEYS = {category: [item["id"] for item in ACCESSORY_OPTIONS[category]] for category in ACCESSORY_CATEGORY_ORDER}
ACCESSORY_COSTS = {
    category: {item["id"]: item["cost"] for item in ACCESSORY_OPTIONS[category]}
    for category in ACCESSORY_CATEGORY_ORDER
}
ACCESSORY_LABELS = {
    category: {item["id"]: item["label"] for item in ACCESSORY_OPTIONS[category]}
    for category in ACCESSORY_CATEGORY_ORDER
}

def build_default_accessory_selection():
    return dict(ACCESSORY_DEFAULTS)

def make_owned_accessories():
    return {category: [ACCESSORY_DEFAULTS[category]] for category in ACCESSORY_CATEGORY_ORDER}

DEFAULT_STATS = {
    "games_played": 0,
    "normal_games_played": 0,
    "extreme_games_played": 0,
    "best_score": 0,
    "best_normal_score": 0,
    "best_extreme_score": 0,
    "total_score": 0,
    "total_flaps": 0,
    "longest_run_sec": 0.0,
    "total_run_time_sec": 0.0,
    "powerups_collected": 0,
    "coins_earned": 0,
    "coins_spent": 0,
    "items_bought": 0,
}

def make_daily_stats():
    return {
        "games_played": 0,
        "normal_games_played": 0,
        "extreme_games_played": 0,
        "total_score": 0,
        "best_score": 0,
        "best_normal_score": 0,
        "best_extreme_score": 0,
        "flaps": 0,
        "longest_run_sec": 0.0,
        "powerups_collected": 0,
        "coins_spent": 0,
        "items_bought": 0,
    }

def make_player_data():
    return {
        "coins": 0,
        "owned_birds": ["yellow"],
        "owned_trails": ["none", "bird"],
        "owned_backgrounds": ["day"],
        "accessory_shop_unlocked": False,
        "owned_accessories": make_owned_accessories(),
        "claimed_quests": [],
        "claimed_daily": [],
        "daily_assignments": [],
        "daily_refreshed_at": 0.0,
        "daily_stats": make_daily_stats(),
        "dev_tools_unlocked": False,
        "dev_cheats": {
            "infinite_gold": False,
            "infinite_immunity": False,
        },
    }

QUEST_RANKS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
DEV_TOOLS_CODE = "3483"
DEV_CHEAT_KEYS = ("infinite_gold", "infinite_immunity")
DEV_CHEAT_INFO = [
    {
        "key": "infinite_gold",
        "title": "Infinite Gold",
        "desc": "Shop items can be unlocked without spending coins.",
    },
    {
        "key": "infinite_immunity",
        "title": "Infinite Immunity",
        "desc": "Keeps the immunity power-up active the whole run.",
    },
]

QUEST_DEFINITIONS = [
    {"id": "first_flight", "title": "First Flight", "desc": "Play 1 game", "track": "games_played", "goal": 1, "reward": 15},
    {"id": "pipe_starter", "title": "Pipe Starter", "desc": "Score 10 points total", "track": "total_score", "goal": 10, "reward": 30},
    {"id": "double_digits", "title": "Double Digits", "desc": "Reach a score of 10 in one run", "track": "best_score", "goal": 10, "reward": 50},
    {"id": "rookie_flaps", "title": "Rookie Flaps", "desc": "Flap 60 times", "track": "total_flaps", "goal": 60, "reward": 35},
    {"id": "steady_glide", "title": "Steady Glide", "desc": "Stay alive for 15 seconds in one run", "track": "longest_run_sec", "goal": 15, "reward": 45},
    {"id": "power_sip", "title": "Power Sip", "desc": "Collect 2 power-ups", "track": "powerups_collected", "goal": 2, "reward": 55},
    {"id": "keep_going", "title": "Keep Going", "desc": "Play 10 games", "track": "games_played", "goal": 10, "reward": 60},
    {"id": "shopper", "title": "Shopper", "desc": "Buy 1 item in the shop", "track": "items_bought", "goal": 1, "reward": 60},
    {"id": "coin_drop", "title": "Coin Drop", "desc": "Spend 80 coins", "track": "coins_spent", "goal": 80, "reward": 80},
    {"id": "sky_runner", "title": "Sky Runner", "desc": "Reach a score of 20 in one run", "track": "best_score", "goal": 20, "reward": 90},
    {"id": "pipe_pacer", "title": "Pipe Pacer", "desc": "Score 50 points total", "track": "total_score", "goal": 50, "reward": 100},
    {"id": "flap_cadet", "title": "Flap Cadet", "desc": "Flap 250 times", "track": "total_flaps", "goal": 250, "reward": 95},
    {"id": "power_hunter", "title": "Power Hunter", "desc": "Collect 8 power-ups", "track": "powerups_collected", "goal": 8, "reward": 110},
    {"id": "survivor", "title": "Survivor", "desc": "Stay alive for 25 seconds in one run", "track": "longest_run_sec", "goal": 25, "reward": 120},
    {"id": "night_shift", "title": "Night Shift", "desc": "Play 1 extreme game", "track": "extreme_games_played", "goal": 1, "reward": 130},
    {"id": "extreme_breaker", "title": "Extreme Breaker", "desc": "Score 6 in extreme mode", "track": "best_extreme_score", "goal": 6, "reward": 160},
    {"id": "pipe_veteran", "title": "Pipe Veteran", "desc": "Score 120 points total", "track": "total_score", "goal": 120, "reward": 180},
    {"id": "collector", "title": "Collector", "desc": "Buy 4 items in the shop", "track": "items_bought", "goal": 4, "reward": 170},
    {"id": "high_flyer", "title": "High Flyer", "desc": "Reach a score of 35 in one run", "track": "best_score", "goal": 35, "reward": 220},
    {"id": "extreme_legend", "title": "Extreme Legend", "desc": "Score 15 in extreme mode", "track": "best_extreme_score", "goal": 15, "reward": 260},
]
QUEST_DEFINITIONS = [{**quest, "reward": scale_quest_reward(quest["reward"])} for quest in QUEST_DEFINITIONS]

EXTRA_QUEST_SERIES = [
    {
        "prefix": "sky_marathon",
        "title": "Sky Marathon",
        "desc_template": "Play {goal} games",
        "track": "games_played",
        "goals": [20, 35, 50, 75, 100, 150, 200, 300, 400, 500],
        "rewards": scale_quest_reward_list([70, 85, 100, 120, 140, 165, 190, 220, 250, 285]),
    },
    {
        "prefix": "sunny_miles",
        "title": "Sunny Miles",
        "desc_template": "Play {goal} normal games",
        "track": "normal_games_played",
        "goals": [10, 20, 30, 45, 60, 80, 100, 130, 160, 200],
        "rewards": scale_quest_reward_list([60, 75, 90, 105, 120, 140, 160, 185, 210, 240]),
    },
    {
        "prefix": "moon_runner",
        "title": "Moon Runner",
        "desc_template": "Play {goal} extreme games",
        "track": "extreme_games_played",
        "goals": [3, 5, 10, 15, 20, 30, 40, 50, 75, 100],
        "rewards": scale_quest_reward_list([80, 95, 115, 135, 160, 190, 220, 250, 285, 325]),
    },
    {
        "prefix": "pipe_bank",
        "title": "Pipe Bank",
        "desc_template": "Score {goal} total points",
        "track": "total_score",
        "goals": [200, 300, 450, 600, 800, 1000, 1300, 1700, 2200, 3000],
        "rewards": scale_quest_reward_list([75, 90, 110, 130, 155, 180, 210, 245, 280, 330]),
    },
    {
        "prefix": "ace_flyer",
        "title": "Ace Flyer",
        "desc_template": "Reach a score of {goal} in one run",
        "track": "best_score",
        "goals": [40, 50, 60, 70, 80, 90, 100, 115, 130, 150],
        "rewards": scale_quest_reward_list([100, 120, 140, 165, 195, 225, 260, 300, 345, 395]),
    },
    {
        "prefix": "extreme_ace",
        "title": "Extreme Ace",
        "desc_template": "Reach {goal} in extreme mode",
        "track": "best_extreme_score",
        "goals": [18, 22, 26, 30, 35, 40, 45, 50, 60, 75],
        "rewards": scale_quest_reward_list([115, 135, 155, 180, 210, 240, 275, 315, 360, 420]),
    },
    {
        "prefix": "wing_engine",
        "title": "Wing Engine",
        "desc_template": "Flap {goal} times",
        "track": "total_flaps",
        "goals": [400, 700, 1000, 1500, 2200, 3000, 4000, 5500, 7500, 10000],
        "rewards": scale_quest_reward_list([65, 80, 95, 115, 140, 170, 205, 245, 290, 340]),
    },
    {
        "prefix": "survival_chronicle",
        "title": "Survival Chronicle",
        "desc_template": "Stay alive for {goal} seconds in one run",
        "track": "longest_run_sec",
        "goals": [30, 40, 50, 60, 75, 90, 105, 120, 150, 180],
        "rewards": scale_quest_reward_list([90, 115, 140, 165, 195, 230, 265, 305, 355, 410]),
    },
    {
        "prefix": "power_collector",
        "title": "Power Collector",
        "desc_template": "Collect {goal} power-ups",
        "track": "powerups_collected",
        "goals": [15, 25, 40, 60, 90, 130, 180, 240, 320, 420],
        "rewards": scale_quest_reward_list([85, 100, 120, 145, 175, 210, 250, 295, 345, 400]),
    },
    {
        "prefix": "coin_crafter",
        "title": "Coin Crafter",
        "desc_template": "Spend {goal} coins",
        "track": "coins_spent",
        "goals": [150, 250, 350, 450, 550, 650, 775, 900, 1025, 1145],
        "rewards": scale_quest_reward_list([90, 110, 130, 150, 175, 205, 235, 270, 310, 355]),
    },
]

MEGA_QUEST_SERIES = [
    {
        "prefix": "sky_dominion",
        "title": "Sky Dominion",
        "desc_template": "Play {goal} games",
        "track": "games_played",
        "tiers": 100,
        "goal_start": 600,
        "goal_step": 18,
        "goal_curve": 0.95,
        "goal_round": 5,
        "reward_start": 320,
        "reward_step": 12,
        "reward_curve": 0.38,
        "reward_round": 5,
    },
    {
        "prefix": "sun_champion",
        "title": "Sun Champion",
        "desc_template": "Play {goal} normal games",
        "track": "normal_games_played",
        "tiers": 100,
        "goal_start": 300,
        "goal_step": 14,
        "goal_curve": 0.75,
        "goal_round": 5,
        "reward_start": 300,
        "reward_step": 11,
        "reward_curve": 0.32,
        "reward_round": 5,
    },
    {
        "prefix": "moon_emperor",
        "title": "Moon Emperor",
        "desc_template": "Play {goal} extreme games",
        "track": "extreme_games_played",
        "tiers": 100,
        "goal_start": 120,
        "goal_step": 7,
        "goal_curve": 0.45,
        "goal_round": 1,
        "reward_start": 360,
        "reward_step": 14,
        "reward_curve": 0.42,
        "reward_round": 5,
    },
    {
        "prefix": "score_constellation",
        "title": "Score Constellation",
        "desc_template": "Score {goal} total points",
        "track": "total_score",
        "tiers": 100,
        "goal_start": 3500,
        "goal_step": 85,
        "goal_curve": 4.5,
        "goal_round": 5,
        "reward_start": 340,
        "reward_step": 13,
        "reward_curve": 0.4,
        "reward_round": 5,
    },
    {
        "prefix": "high_altitude",
        "title": "High Altitude",
        "desc_template": "Reach a score of {goal} in one run",
        "track": "best_score",
        "tiers": 100,
        "goal_start": 155,
        "goal_step": 2.0,
        "goal_curve": 0.05,
        "goal_round": 1,
        "reward_start": 380,
        "reward_step": 14,
        "reward_curve": 0.32,
        "reward_round": 5,
    },
    {
        "prefix": "extreme_zenith",
        "title": "Extreme Zenith",
        "desc_template": "Reach {goal} in extreme mode",
        "track": "best_extreme_score",
        "tiers": 100,
        "goal_start": 80,
        "goal_step": 1.5,
        "goal_curve": 0.04,
        "goal_round": 1,
        "reward_start": 400,
        "reward_step": 16,
        "reward_curve": 0.35,
        "reward_round": 5,
    },
    {
        "prefix": "flap_dynasty",
        "title": "Flap Dynasty",
        "desc_template": "Flap {goal} times",
        "track": "total_flaps",
        "tiers": 100,
        "goal_start": 12000,
        "goal_step": 180,
        "goal_curve": 9.0,
        "goal_round": 5,
        "reward_start": 310,
        "reward_step": 11,
        "reward_curve": 0.34,
        "reward_round": 5,
    },
    {
        "prefix": "survival_citadel",
        "title": "Survival Citadel",
        "desc_template": "Stay alive for {goal} seconds in one run",
        "track": "longest_run_sec",
        "tiers": 100,
        "goal_start": 180,
        "goal_step": 3.0,
        "goal_curve": 0.04,
        "goal_round": 1,
        "reward_start": 390,
        "reward_step": 13,
        "reward_curve": 0.34,
        "reward_round": 5,
    },
    {
        "prefix": "power_oracle",
        "title": "Power Oracle",
        "desc_template": "Collect {goal} power-ups",
        "track": "powerups_collected",
        "tiers": 100,
        "goal_start": 450,
        "goal_step": 12,
        "goal_curve": 0.15,
        "goal_round": 1,
        "reward_start": 330,
        "reward_step": 12,
        "reward_curve": 0.33,
        "reward_round": 5,
    },
    {
        "prefix": "coin_tycoon",
        "title": "Coin Tycoon",
        "desc_template": "Spend {goal} coins",
        "track": "coins_spent",
        "tiers": 100,
        "goal_start": 1300,
        "goal_step": 35,
        "goal_curve": 1.5,
        "goal_round": 5,
        "reward_start": 320,
        "reward_step": 11,
        "reward_curve": 0.3,
        "reward_round": 5,
    },
]

def build_extra_quests():
    extra_quests = []
    for series in EXTRA_QUEST_SERIES:
        for rank, goal, reward in zip(QUEST_RANKS, series["goals"], series["rewards"]):
            extra_quests.append({
                "id": f"{series['prefix']}_{goal}",
                "title": f"{series['title']} {rank}",
                "desc": series["desc_template"].format(goal=goal),
                "track": series["track"],
                "goal": goal,
                "reward": reward,
            })
    return extra_quests

def round_progression_value(value, step):
    step = max(1, int(step))
    return int(round(value / step) * step)

def build_mega_quests():
    mega_quests = []
    for series in MEGA_QUEST_SERIES:
        last_goal = 0
        last_reward = 0
        for tier in range(1, series["tiers"] + 1):
            tier_index = tier - 1
            raw_goal = (
                series["goal_start"]
                + series["goal_step"] * tier_index
                + series["goal_curve"] * (tier_index ** 2)
            )
            raw_reward = (
                series["reward_start"]
                + series["reward_step"] * tier_index
                + series["reward_curve"] * (tier_index ** 2)
            )
            goal = max(last_goal + 1, round_progression_value(raw_goal, series.get("goal_round", 1)))
            scaled_reward = raw_reward * QUEST_REWARD_MULTIPLIER
            reward = max(last_reward + 1, round_progression_value(scaled_reward, series.get("reward_round", 1)))
            mega_quests.append({
                "id": f"{series['prefix']}_{tier:03d}",
                "title": f"{series['title']} {tier:03d}",
                "desc": series["desc_template"].format(goal=goal),
                "track": series["track"],
                "goal": goal,
                "reward": reward,
            })
            last_goal = goal
            last_reward = reward
    return mega_quests

QUEST_DEFINITIONS.extend(build_extra_quests())
QUEST_DEFINITIONS.extend(build_mega_quests())

DAILY_QUEST_POOL = [
    {"id": "daily_play_2", "title": "Warm-Up", "desc": "Play 2 games today", "track": "games_played", "goal": 2, "reward": 25},
    {"id": "daily_play_4", "title": "Session Grind", "desc": "Play 4 games today", "track": "games_played", "goal": 4, "reward": 45},
    {"id": "daily_score_8", "title": "Quick Pipes", "desc": "Score 8 points today", "track": "total_score", "goal": 8, "reward": 30},
    {"id": "daily_score_20", "title": "Big Day", "desc": "Score 20 points today", "track": "total_score", "goal": 20, "reward": 65},
    {"id": "daily_best_8", "title": "Sharp Start", "desc": "Reach 8 in one run today", "track": "best_score", "goal": 8, "reward": 40},
    {"id": "daily_best_15", "title": "Run Builder", "desc": "Reach 15 in one run today", "track": "best_score", "goal": 15, "reward": 75},
    {"id": "daily_flaps_40", "title": "Wing Workout", "desc": "Flap 40 times today", "track": "flaps", "goal": 40, "reward": 25},
    {"id": "daily_flaps_120", "title": "Air Drummer", "desc": "Flap 120 times today", "track": "flaps", "goal": 120, "reward": 55},
    {"id": "daily_power_1", "title": "Power Tap", "desc": "Collect 1 power-up today", "track": "powerups_collected", "goal": 1, "reward": 40},
    {"id": "daily_power_3", "title": "Power Sweep", "desc": "Collect 3 power-ups today", "track": "powerups_collected", "goal": 3, "reward": 80},
    {"id": "daily_buy_1", "title": "Fresh Look", "desc": "Buy 1 shop item today", "track": "items_bought", "goal": 1, "reward": 85},
    {"id": "daily_spend_75", "title": "Big Spender", "desc": "Spend 75 coins today", "track": "coins_spent", "goal": 75, "reward": 95},
    {"id": "daily_extreme_1", "title": "Moonlight Run", "desc": "Play 1 extreme game today", "track": "extreme_games_played", "goal": 1, "reward": 95},
    {"id": "daily_extreme_5", "title": "Extreme Touch", "desc": "Score 5 in extreme today", "track": "best_extreme_score", "goal": 5, "reward": 125},
    {"id": "daily_survive_20", "title": "Stay Calm", "desc": "Stay alive for 20 seconds today", "track": "longest_run_sec", "goal": 20, "reward": 85},
]
DAILY_QUEST_POOL = [{**quest, "reward": scale_quest_reward(quest["reward"])} for quest in DAILY_QUEST_POOL]
DEFAULT_SETTINGS = {
    "music": True,
    "music_volume": 0.28,
    "sfx": True,
    "sfx_volume": 0.85,
    "screenshake": True,
    "particles": True,
    "vignette": False,
    "show_fps": False,
    "hotkey_flap": "space",
    "hotkey_cosmetics": "c",
    "hotkey_settings": "o",
    "hotkey_high_scores": "h",
    "hotkey_stats": "s",
    "hotkey_extreme": "e",
    "hotkey_back": "escape",
    "selected_bird_key": "yellow",
    "selected_bg": "day",
    "selected_trail_key": "bird",
    "selected_accessories": build_default_accessory_selection(),
}
SETTINGS = {}
selected_bird_key = DEFAULT_SETTINGS["selected_bird_key"]
selected_bg       = DEFAULT_SETTINGS["selected_bg"]
selected_trail_key = DEFAULT_SETTINGS["selected_trail_key"]
selected_accessories = build_default_accessory_selection()
KEYBIND_KEYS = (
    "hotkey_flap",
    "hotkey_cosmetics",
    "hotkey_settings",
    "hotkey_high_scores",
    "hotkey_stats",
    "hotkey_extreme",
    "hotkey_back",
)

# ----------------------------- Init ------------------------------------------
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(CAPTION)
CLOCK = pygame.time.Clock()

# Fonts
try:
    FONT     = pygame.font.SysFont("Georgia",    18, bold=True)
    BIG      = pygame.font.SysFont("Georgia",    54, bold=True)
    MED      = pygame.font.SysFont("Georgia",    28, bold=True)
    SMALL    = pygame.font.SysFont("Verdana",    13)
    TINY     = pygame.font.SysFont("Verdana",    11)
    MONO     = pygame.font.SysFont("Consolas",   13)
    TITLE    = pygame.font.SysFont("Georgia",    44, bold=True)
    SUBTITLE = pygame.font.SysFont("Georgia",    20, italic=True)
    HUGE     = pygame.font.SysFont("Georgia",    70, bold=True)
except Exception:
    FONT     = pygame.font.SysFont("Verdana", 18)
    BIG      = pygame.font.SysFont("Verdana", 50)
    MED      = pygame.font.SysFont("Verdana", 26)
    SMALL    = pygame.font.SysFont("Verdana", 13)
    TINY     = pygame.font.SysFont("Verdana", 11)
    MONO     = pygame.font.SysFont("Verdana", 13)
    TITLE    = pygame.font.SysFont("Verdana", 40, bold=True)
    SUBTITLE = pygame.font.SysFont("Verdana", 18)
    HUGE     = pygame.font.SysFont("Verdana", 65, bold=True)

PERSISTENCE_ALERT = {
    "text": "",
    "color": (255, 145, 145),
    "sticky": False,
    "until": 0,
}

# ----------------------------- Helpers ---------------------------------------
def storage_backup_path(path):
    return f"{path}.bak"

def storage_temp_path(path):
    return f"{path}.tmp"

def storage_label(path):
    return os.path.basename(path)

def set_persistence_alert(text, color=(255, 145, 145), sticky=True, duration_ms=9000):
    if (
        PERSISTENCE_ALERT["text"] == text
        and PERSISTENCE_ALERT["color"] == color
        and PERSISTENCE_ALERT["sticky"] == sticky
    ):
        if not sticky:
            PERSISTENCE_ALERT["until"] = pygame.time.get_ticks() + max(1000, duration_ms)
        return
    PERSISTENCE_ALERT["text"] = text
    PERSISTENCE_ALERT["color"] = color
    PERSISTENCE_ALERT["sticky"] = sticky
    PERSISTENCE_ALERT["until"] = 0 if sticky else pygame.time.get_ticks() + max(1000, duration_ms)
    print(text)

def active_persistence_alert():
    if not PERSISTENCE_ALERT["text"]:
        return None
    if PERSISTENCE_ALERT["sticky"]:
        return PERSISTENCE_ALERT
    if pygame.time.get_ticks() <= PERSISTENCE_ALERT["until"]:
        return PERSISTENCE_ALERT
    PERSISTENCE_ALERT["text"] = ""
    return None

def load_json(path, default):
    backup_path = storage_backup_path(path)
    had_read_error = False
    for candidate in (path, backup_path):
        if not os.path.exists(candidate):
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                data = json.load(f)
            if candidate == backup_path:
                set_persistence_alert(
                    f"Recovered {storage_label(path)} from a backup copy.",
                    color=(255, 225, 140),
                    sticky=True,
                )
            return data
        except Exception as exc:
            had_read_error = True
            print(f"Couldn't read {candidate}: {exc}")
    if had_read_error:
        set_persistence_alert(
            f"{storage_label(path)} could not be read. Using a safe fallback for this session.",
            color=(255, 145, 145),
            sticky=True,
        )
    return default

def save_json(path, data):
    temp_path = storage_temp_path(path)
    backup_path = storage_backup_path(path)
    backup_failed = False
    try:
        if os.path.exists(path):
            try:
                shutil.copyfile(path, backup_path)
            except Exception as exc:
                backup_failed = True
                print(f"Couldn't refresh backup for {path}: {exc}")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            if hasattr(os, "fsync"):
                os.fsync(f.fileno())
        os.replace(temp_path, path)
        if backup_failed:
            set_persistence_alert(
                f"Saved {storage_label(path)}, but the backup copy could not be refreshed.",
                color=(255, 210, 140),
                sticky=False,
            )
        return True
    except Exception as exc:
        print(f"Couldn't save {path}: {exc}")
        set_persistence_alert(
            f"Couldn't save {storage_label(path)}. Progress may not persist until saving works again.",
            color=(255, 145, 145),
            sticky=True,
        )
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        return False

def unique_valid_keys(items, valid_keys, fallback):
    seen = set()
    cleaned = []
    for item in items:
        if item in valid_keys and item not in seen:
            seen.add(item)
            cleaned.append(item)
    if cleaned:
        return cleaned
    return list(fallback)

def load_stats_data():
    raw = load_json(STATS_FILE, {})
    if not isinstance(raw, dict):
        raw = {}

    stats = DEFAULT_STATS.copy()
    for key, default_value in DEFAULT_STATS.items():
        value = raw.get(key, default_value)
        try:
            if isinstance(default_value, float):
                stats[key] = float(value)
            else:
                stats[key] = int(value)
        except (TypeError, ValueError):
            stats[key] = default_value
    return stats

def save_stats():
    save_json(STATS_FILE, PLAYER_STATS)

def load_player_data():
    raw = load_json(SAVE_FILE, {})
    if not isinstance(raw, dict):
        raw = {}

    data = make_player_data()
    try:
        data["coins"] = max(0, int(raw.get("coins", data["coins"])))
    except (TypeError, ValueError):
        data["coins"] = 0

    raw_birds = raw.get("owned_birds", raw.get("owned", data["owned_birds"]))
    raw_trails = raw.get("owned_trails", data["owned_trails"])
    raw_backgrounds = raw.get("owned_backgrounds", data["owned_backgrounds"])
    data["owned_birds"] = unique_valid_keys(raw_birds if isinstance(raw_birds, list) else [], BIRD_KEYS, ["yellow"])
    data["owned_trails"] = unique_valid_keys(raw_trails if isinstance(raw_trails, list) else [], TRAIL_KEYS, ["none", "bird"])
    data["owned_backgrounds"] = unique_valid_keys(raw_backgrounds if isinstance(raw_backgrounds, list) else [], BG_OPTIONS, ["day"])
    raw_owned_accessories = raw.get("owned_accessories", {})
    if not isinstance(raw_owned_accessories, dict):
        raw_owned_accessories = {}
    data["owned_accessories"] = {}
    for category in ACCESSORY_CATEGORY_ORDER:
        raw_items = raw_owned_accessories.get(category, [])
        data["owned_accessories"][category] = unique_valid_keys(
            raw_items if isinstance(raw_items, list) else [],
            ACCESSORY_KEYS[category],
            [ACCESSORY_DEFAULTS[category]],
        )
    data["accessory_shop_unlocked"] = bool(raw.get("accessory_shop_unlocked", False)) or any(
        len(data["owned_accessories"][category]) > 1 for category in ACCESSORY_CATEGORY_ORDER
    )

    data["claimed_quests"] = unique_valid_keys(
        raw.get("claimed_quests", []),
        [quest["id"] for quest in QUEST_DEFINITIONS],
        [],
    )
    data["claimed_daily"] = unique_valid_keys(
        raw.get("claimed_daily", []),
        [quest["id"] for quest in DAILY_QUEST_POOL],
        [],
    )

    raw_assignments = raw.get("daily_assignments", [])
    data["daily_assignments"] = unique_valid_keys(
        raw_assignments if isinstance(raw_assignments, list) else [],
        [quest["id"] for quest in DAILY_QUEST_POOL],
        [],
    )
    try:
        data["daily_refreshed_at"] = float(raw.get("daily_refreshed_at", 0.0))
    except (TypeError, ValueError):
        data["daily_refreshed_at"] = 0.0

    raw_daily_stats = raw.get("daily_stats", {})
    if not isinstance(raw_daily_stats, dict):
        raw_daily_stats = {}
    daily_stats = make_daily_stats()
    for key, default_value in daily_stats.items():
        value = raw_daily_stats.get(key, default_value)
        try:
            if isinstance(default_value, float):
                daily_stats[key] = float(value)
            else:
                daily_stats[key] = int(value)
        except (TypeError, ValueError):
            daily_stats[key] = default_value
    data["daily_stats"] = daily_stats
    data["dev_tools_unlocked"] = False

    raw_cheats = raw.get("dev_cheats", {})
    if not isinstance(raw_cheats, dict):
        raw_cheats = {}
    data["dev_cheats"] = {
        cheat_key: bool(raw_cheats.get(cheat_key, False))
        for cheat_key in DEV_CHEAT_KEYS
    }
    return data

def save_player_data():
    # Dev-tools access is temporary and should always require the code again.
    data_to_save = dict(PLAYER_DATA)
    data_to_save["dev_tools_unlocked"] = False
    save_json(SAVE_FILE, data_to_save)

if not os.path.exists(HIGH_SCORES_FILE):
    save_json(HIGH_SCORES_FILE, {"normal": [], "extreme": []})
if not os.path.exists(STATS_FILE):
    save_json(STATS_FILE, DEFAULT_STATS)
if not os.path.exists(SETTINGS_FILE):
    save_json(SETTINGS_FILE, DEFAULT_SETTINGS)
if not os.path.exists(SAVE_FILE):
    save_json(SAVE_FILE, make_player_data())

def load_settings():
    raw = load_json(SETTINGS_FILE, {})
    if not isinstance(raw, dict):
        raw = {}

    settings = DEFAULT_SETTINGS.copy()
    settings["selected_accessories"] = build_default_accessory_selection()
    settings.update({k: raw[k] for k in DEFAULT_SETTINGS if k in raw})

    for key in ("music", "sfx", "screenshake", "particles", "vignette", "show_fps"):
        if not isinstance(settings.get(key), bool):
            settings[key] = DEFAULT_SETTINGS[key]

    for key in ("music_volume", "sfx_volume"):
        try:
            settings[key] = max(0.0, min(1.0, float(settings.get(key, DEFAULT_SETTINGS[key]))))
        except (TypeError, ValueError):
            settings[key] = DEFAULT_SETTINGS[key]

    for key in KEYBIND_KEYS:
        key_name = settings.get(key, DEFAULT_SETTINGS[key])
        if not isinstance(key_name, str):
            settings[key] = DEFAULT_SETTINGS[key]
            continue
        key_name = key_name.strip().lower()
        try:
            pygame.key.key_code(key_name)
            settings[key] = key_name
        except (TypeError, ValueError):
            settings[key] = DEFAULT_SETTINGS[key]

    if settings.get("selected_bird_key") not in BIRD_KEYS:
        settings["selected_bird_key"] = DEFAULT_SETTINGS["selected_bird_key"]
    if settings.get("selected_bg") not in BG_OPTIONS:
        settings["selected_bg"] = DEFAULT_SETTINGS["selected_bg"]
    if settings.get("selected_trail_key") not in TRAIL_KEYS:
        settings["selected_trail_key"] = DEFAULT_SETTINGS["selected_trail_key"]
    raw_selected_accessories = settings.get("selected_accessories", {})
    if not isinstance(raw_selected_accessories, dict):
        raw_selected_accessories = {}
    cleaned_accessories = {}
    for category in ACCESSORY_CATEGORY_ORDER:
        selected_key = raw_selected_accessories.get(category, ACCESSORY_DEFAULTS[category])
        cleaned_accessories[category] = selected_key if selected_key in ACCESSORY_KEYS[category] else ACCESSORY_DEFAULTS[category]
    settings["selected_accessories"] = cleaned_accessories
    return settings

SETTINGS = load_settings()
selected_bird_key = SETTINGS["selected_bird_key"]
selected_bg       = SETTINGS["selected_bg"]
selected_trail_key = SETTINGS["selected_trail_key"]
selected_accessories = dict(SETTINGS["selected_accessories"])
PLAYER_STATS = load_stats_data()
PLAYER_DATA = load_player_data()

def sync_settings_from_globals():
    SETTINGS["selected_bird_key"] = selected_bird_key
    SETTINGS["selected_bg"] = selected_bg
    SETTINGS["selected_trail_key"] = selected_trail_key
    SETTINGS["selected_accessories"] = dict(selected_accessories)

def resolve_trail_color(trail_key, bird_color):
    if trail_key == "bird":
        return bird_color
    return TRAIL_COLORS.get(trail_key, bird_color)

def current_accessory_selection():
    return {
        category: selected_accessories.get(category, ACCESSORY_DEFAULTS[category])
        for category in ACCESSORY_CATEGORY_ORDER
    }

def accessory_label(category, key):
    return ACCESSORY_LABELS.get(category, {}).get(key, key.replace("_", " ").title())

def save_settings():
    sync_settings_from_globals()
    save_json(SETTINGS_FILE, SETTINGS)

def ensure_owned_selection():
    global selected_bird_key, selected_bg, selected_trail_key, selected_accessories
    changed = False

    if selected_bird_key not in PLAYER_DATA["owned_birds"]:
        if PLAYER_DATA["owned_birds"]:
            selected_bird_key = PLAYER_DATA["owned_birds"][0]
        else:
            selected_bird_key = "yellow"
            PLAYER_DATA["owned_birds"] = ["yellow"]
        changed = True

    if selected_trail_key not in PLAYER_DATA["owned_trails"]:
        if PLAYER_DATA["owned_trails"]:
            selected_trail_key = PLAYER_DATA["owned_trails"][0]
        else:
            selected_trail_key = "bird"
            PLAYER_DATA["owned_trails"] = ["bird"]
        changed = True

    if selected_bg not in PLAYER_DATA["owned_backgrounds"]:
        if PLAYER_DATA["owned_backgrounds"]:
            selected_bg = PLAYER_DATA["owned_backgrounds"][0]
        else:
            selected_bg = "day"
            PLAYER_DATA["owned_backgrounds"] = ["day"]
        changed = True

    owned_accessories = PLAYER_DATA.setdefault("owned_accessories", make_owned_accessories())
    for category in ACCESSORY_CATEGORY_ORDER:
        owned_bucket = owned_accessories.get(category)
        if not isinstance(owned_bucket, list) or not owned_bucket:
            owned_accessories[category] = [ACCESSORY_DEFAULTS[category]]
            owned_bucket = owned_accessories[category]
            changed = True
        if selected_accessories.get(category) not in owned_bucket:
            selected_accessories[category] = owned_bucket[0]
            changed = True

    if changed:
        save_settings()
        save_player_data()

def grant_legacy_ownership():
    changed = False
    for key, bucket in (
        (selected_bird_key, "owned_birds"),
        (selected_trail_key, "owned_trails"),
        (selected_bg, "owned_backgrounds"),
    ):
        if key not in PLAYER_DATA[bucket]:
            PLAYER_DATA[bucket].append(key)
            changed = True
    owned_accessories = PLAYER_DATA.setdefault("owned_accessories", make_owned_accessories())
    for category in ACCESSORY_CATEGORY_ORDER:
        selected_key = selected_accessories.get(category, ACCESSORY_DEFAULTS[category])
        owned_bucket = owned_accessories.setdefault(category, [ACCESSORY_DEFAULTS[category]])
        if selected_key not in owned_bucket:
            owned_bucket.append(selected_key)
            changed = True
        if any(item != ACCESSORY_DEFAULTS[category] for item in owned_bucket):
            PLAYER_DATA["accessory_shop_unlocked"] = True
    if changed:
        save_player_data()

def refresh_daily_quests(force=False):
    now = time.time()
    quest_ids = [quest["id"] for quest in DAILY_QUEST_POOL]
    invalid_assignments = any(quest_id not in quest_ids for quest_id in PLAYER_DATA["daily_assignments"])
    should_refresh = (
        force
        or len(PLAYER_DATA["daily_assignments"]) != 5
        or invalid_assignments
        or now - PLAYER_DATA["daily_refreshed_at"] >= 24 * 60 * 60
    )
    if not should_refresh:
        return False

    rng = random.Random(int(now // (24 * 60 * 60)))
    PLAYER_DATA["daily_assignments"] = [quest["id"] for quest in rng.sample(DAILY_QUEST_POOL, 5)]
    PLAYER_DATA["claimed_daily"] = []
    PLAYER_DATA["daily_refreshed_at"] = now
    PLAYER_DATA["daily_stats"] = make_daily_stats()
    save_player_data()
    return True

def get_active_daily_quests():
    refresh_daily_quests()
    quest_lookup = {quest["id"]: quest for quest in DAILY_QUEST_POOL}
    return [quest_lookup[qid] for qid in PLAYER_DATA["daily_assignments"] if qid in quest_lookup]

def get_quest_progress(quest, daily=False):
    source = PLAYER_DATA["daily_stats"] if daily else PLAYER_STATS
    return max(0, source.get(quest["track"], 0))

def mark_quest_complete(quest, daily=False):
    completed_key = "claimed_daily" if daily else "claimed_quests"
    if quest["id"] in PLAYER_DATA[completed_key]:
        return None
    PLAYER_DATA[completed_key].append(quest["id"])
    PLAYER_DATA["coins"] += quest["reward"]
    PLAYER_STATS["coins_earned"] += quest["reward"]
    return quest["reward"]

def complete_ready_quests():
    refresh_daily_quests()
    rewards = []

    for quest in QUEST_DEFINITIONS:
        if quest["id"] in PLAYER_DATA["claimed_quests"]:
            continue
        if get_quest_progress(quest) >= quest["goal"]:
            reward = mark_quest_complete(quest, daily=False)
            if reward is not None:
                rewards.append((quest["title"], reward, False))

    for quest in get_active_daily_quests():
        if quest["id"] in PLAYER_DATA["claimed_daily"]:
            continue
        if get_quest_progress(quest, daily=True) >= quest["goal"]:
            reward = mark_quest_complete(quest, daily=True)
            if reward is not None:
                rewards.append((quest["title"], reward, True))

    if rewards:
        save_stats()
        save_player_data()
    return rewards

def format_time_progress(seconds):
    if seconds >= 60:
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins}m {secs:02d}s"
    return f"{int(seconds)}s"

def format_quest_progress(quest, daily=False):
    current = get_quest_progress(quest, daily)
    goal = quest["goal"]
    if quest["track"] == "longest_run_sec":
        return f"{format_time_progress(current)} / {format_time_progress(goal)}"
    return f"{int(current)} / {int(goal)}"

def seconds_until_daily_refresh():
    refresh_daily_quests()
    ends_at = PLAYER_DATA["daily_refreshed_at"] + 24 * 60 * 60
    return max(0, int(ends_at - time.time()))

def format_countdown(seconds):
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m {secs:02d}s"

def cheat_enabled(cheat_key):
    return bool(PLAYER_DATA.get("dev_cheats", {}).get(cheat_key, False))

def active_cheat_labels():
    labels = []
    if cheat_enabled("infinite_gold"):
        labels.append("INF GOLD")
    if cheat_enabled("infinite_immunity"):
        labels.append("INF IMMUNITY")
    return labels

def toggle_dev_cheat(cheat_key):
    if cheat_key not in DEV_CHEAT_KEYS:
        return False
    PLAYER_DATA["dev_cheats"][cheat_key] = not cheat_enabled(cheat_key)
    save_player_data()
    return PLAYER_DATA["dev_cheats"][cheat_key]

def unlock_dev_tools():
    PLAYER_DATA["dev_tools_unlocked"] = True

def apply_live_cheats(gs):
    if gs is None:
        return
    if cheat_enabled("infinite_immunity"):
        gs.bird.immunity = max(gs.bird.immunity, POWERUP_DURATION_SEC * FPS)

grant_legacy_ownership()
ensure_owned_selection()

def keybind_matches(ev, action):
    if ev.type != pygame.KEYDOWN:
        return False
    try:
        return ev.key == pygame.key.key_code(SETTINGS.get(action, DEFAULT_SETTINGS[action]))
    except (TypeError, ValueError):
        return ev.key == pygame.key.key_code(DEFAULT_SETTINGS[action])

def get_keybind_label(action):
    try:
        key_code = pygame.key.key_code(SETTINGS.get(action, DEFAULT_SETTINGS[action]))
        return pygame.key.name(key_code).upper()
    except (TypeError, ValueError):
        return DEFAULT_SETTINGS[action].upper()

def load_sound_safe(fname):
    try:
        if fname and os.path.exists(fname):
            return pygame.mixer.Sound(fname)
    except Exception:
        pass
    return None

def generate_beep(freq, duration_ms, volume=0.5):
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000.0)
    buffer = array.array('h')
    for i in range(num_samples):
        sample = int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
        buffer.append(sample)
    return pygame.mixer.Sound(buffer)

def generate_flap_sound():
    sample_rate = 44100
    duration_ms = 150
    num_samples = int(sample_rate * duration_ms / 1000.0)
    buffer = array.array('h')
    for i in range(num_samples):
        sample = int(0.3 * 32767 * (random.random() * 2 - 1))  # white noise burst
        buffer.append(sample)
    return pygame.mixer.Sound(buffer)

def generate_ding():
    sample_rate = 44100
    duration_ms = 200
    num_samples = int(sample_rate * duration_ms / 1000.0)
    buffer = array.array('h')
    for i in range(num_samples):
        t = i / sample_rate
        freq = 1000 - 500 * (t / (duration_ms / 1000.0))  # descending
        sample = int(0.4 * 32767 * math.sin(2 * math.pi * freq * t))
        buffer.append(sample)
    return pygame.mixer.Sound(buffer)

def generate_oof():
    sample_rate = 44100
    duration_ms = 400
    num_samples = int(sample_rate * duration_ms / 1000.0)
    buffer = array.array('h')
    for i in range(num_samples):
        t = i / sample_rate
        freq = 150 - 50 * (t / (duration_ms / 1000.0))  # descending
        sample = int(0.5 * 32767 * math.sin(2 * math.pi * freq * t))
        buffer.append(sample)
    return pygame.mixer.Sound(buffer)

SOUND_FLAP  = load_sound_safe(ASSETS.get("flap",  ""))
SOUND_HIT   = load_sound_safe(ASSETS.get("hit",   ""))
SOUND_POWER = load_sound_safe(ASSETS.get("power", ""))
SOUND_SCORE = load_sound_safe(ASSETS.get("score", ""))

# Fallback generated sounds if files not found
if not SOUND_FLAP:  SOUND_FLAP  = generate_flap_sound()  # Flapping noise
if not SOUND_HIT:   SOUND_HIT   = generate_oof()         # Oof on death
if not SOUND_POWER: SOUND_POWER = generate_ding()        # Ding on powerup
if not SOUND_SCORE: SOUND_SCORE = generate_beep(880, 120, volume=0.35)

SOUND_BASE_VOLUMES = {
    "flap": 0.55,
    "hit": 1.00,
    "power": 0.75,
    "score": 0.70,
}

if os.path.exists(ASSETS.get("bg_music", "")):
    try:
        pygame.mixer.music.load(ASSETS.get("bg_music"))
    except Exception:
        pass

def apply_audio_settings():
    sfx_volume = SETTINGS["sfx_volume"] if SETTINGS["sfx"] else 0.0
    for name, sound in (
        ("flap", SOUND_FLAP),
        ("hit", SOUND_HIT),
        ("power", SOUND_POWER),
        ("score", SOUND_SCORE),
    ):
        if sound:
            try:
                sound.set_volume(SOUND_BASE_VOLUMES[name] * sfx_volume)
            except Exception:
                pass
    try:
        pygame.mixer.music.set_volume(SETTINGS["music_volume"] if SETTINGS["music"] else 0.0)
    except Exception:
        pass

def play_sound(sound):
    if not SETTINGS["sfx"] or not sound:
        return
    try:
        sound.play()
    except Exception:
        pass

apply_audio_settings()

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))

def clamp(x, a, b):
    return max(a, min(b, x))

def ease_out_cubic(t):
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3

def fit_text_to_width(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text
    suffix = "..."
    trimmed = text
    while trimmed and font.size(trimmed + suffix)[0] > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + suffix) if trimmed else suffix

# ----------------------------- Particle System -------------------------------
class Particle:
    __slots__ = ('x','y','vx','vy','color','life','max_life','rad','glow','spin','fade_exp')

    def __init__(self, x, y, vx, vy, color, life, rad=3, glow=False, spin=0.0, fade_exp=1.0):
        self.x = float(x); self.y = float(y)
        self.vx = float(vx); self.vy = float(vy)
        self.color = color
        self.life = life; self.max_life = life
        self.rad = rad; self.glow = glow
        self.spin = spin; self.fade_exp = fade_exp

    def update(self):
        self.vy += 0.15
        self.vx *= 0.985
        self.x += self.vx; self.y += self.vy
        self.life -= 1

    def draw(self, surf, cam_offset=(0,0)):
        if self.life <= 0:
            return
        t = self.life / max(1, self.max_life)
        alpha = clamp(int(255 * (t ** self.fade_exp)), 0, 255)
        cx = int(self.x + cam_offset[0])
        cy = int(self.y + cam_offset[1])
        r  = max(1, self.rad)
        if self.glow:
            for r_m, a_d in [(3, 7), (2, 3), (1, 1)]:
                gr = max(1, r * r_m)
                s  = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, alpha // a_d), (gr, gr), gr)
                surf.blit(s, (cx-gr, cy-gr), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
            surf.blit(s, (cx-r, cy-r))

particles = deque()

def spawn_particles(x, y, color, count=12, spread=6, life=30, speed=3,
                    glow=False, fade_exp=1.0):
    if not SETTINGS["particles"]:
        return
    for _ in range(count):
        if len(particles) >= PARTICLE_LIMIT:
            break
        vx = random.uniform(-speed, speed)
        vy = random.uniform(-speed*0.8, -speed*0.15)
        p  = Particle(
            x + random.uniform(-spread, spread),
            y + random.uniform(-spread, spread),
            vx, vy, color,
            random.randint(life-6, life+8),
            rad=random.randint(2, 5),
            glow=glow,
            fade_exp=fade_exp
        )
        particles.append(p)

def spawn_embers(x, y, color, count=6):
    """Slow-rising ember particles."""
    if not SETTINGS["particles"]:
        return
    for _ in range(count):
        if len(particles) >= PARTICLE_LIMIT:
            break
        vx = random.uniform(-0.6, 0.6)
        vy = random.uniform(-1.5, -0.4)
        p  = Particle(x + random.uniform(-8,8), y + random.uniform(-4,4),
                      vx, vy, color, random.randint(40,80), rad=2, glow=True, fade_exp=0.5)
        particles.append(p)

# ----------------------------- Menu Particles (neon field) -------------------
class MenuParticle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.size = random.uniform(1, 3)
        self.speed = random.uniform(0.2, 0.9)
        self.angle = random.uniform(0, math.pi*2)
        self.color_idx = random.randint(0, 3)
        self.phase = random.uniform(0, math.pi*2)
        self.alpha = random.randint(60, 180)

    def update(self, t):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed * 0.5 - 0.15
        if self.y < -10 or self.x < -10 or self.x > WIDTH+10:
            self.reset()
            self.y = HEIGHT + 5

    def draw(self, surf, t):
        colors = [NEON_GOLD, NEON_CYAN, NEON_PINK, NEON_GREEN]
        col = colors[self.color_idx]
        pulse = 0.6 + 0.4 * math.sin(t * 2.0 + self.phase)
        a = int(self.alpha * pulse)
        r = max(1, int(self.size * pulse))
        s = pygame.Surface((r*4, r*4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, a//3), (r*2, r*2), r*2)
        pygame.draw.circle(s, (*col, a),    (r*2, r*2), r)
        surf.blit(s, (int(self.x)-r*2, int(self.y)-r*2), special_flags=pygame.BLEND_RGBA_ADD)

MENU_PARTICLES = [MenuParticle() for _ in range(80)]

# ----------------------------- Stars -----------------------------------------
STARS = [(random.randint(0, WIDTH),
          random.randint(0, HEIGHT//2 + 100),
          random.uniform(0.3, 1.0),
          random.uniform(0, 6.28),
          random.randint(1, 3)) for _ in range(160)]

STAR_CLUSTERS = [(random.randint(0, WIDTH), random.randint(0, HEIGHT//3),
                  random.uniform(0.4, 0.7)) for _ in range(12)]

# ----------------------------- Pre-baked surfaces ----------------------------
# Sky gradient surface (re-rendered per frame change only — in draw_background)
_cached_sky = {}

def get_sky_surface(mode):
    if mode in _cached_sky:
        return _cached_sky[mode]
    surf = pygame.Surface((WIDTH, HEIGHT))
    if mode == "day":
        stops = [DAY_SKY_ZENITH, DAY_SKY_MID, DAY_SKY_HORIZON, DAY_SKY_HAZE]
    else:
        stops = [NIGHT_SKY_ZENITH, NIGHT_SKY_MID, NIGHT_SKY_BOT, NIGHT_HORIZON]
    n = len(stops) - 1
    for y in range(HEIGHT):
        t_global = y / float(HEIGHT - 1)
        seg = min(int(t_global * n), n-1)
        t_local = t_global * n - seg
        c = lerp_color(stops[seg], stops[seg+1], t_local)
        pygame.draw.line(surf, c, (0, y), (WIDTH, y))
    _cached_sky[mode] = surf
    return surf

# ----------------------------- Atmospheric effects ---------------------------
def draw_god_rays(surf, cx, cy, t):
    """Subtle radiating light beams from the sun."""
    n_rays = 8
    for i in range(n_rays):
        angle = (t * 0.08 + i * math.pi * 2 / n_rays)
        length = random.uniform(180, 280)
        width_ang = math.pi / 60
        # Two points at end
        ax = cx + math.cos(angle - width_ang) * length
        ay = cy + math.sin(angle - width_ang) * length
        bx = cx + math.cos(angle + width_ang) * length
        by = cy + math.sin(angle + width_ang) * length
        pts = [(cx, cy), (int(ax), int(ay)), (int(bx), int(by))]
        ray_surf = pygame.Surface((WIDTH, HEIGHT//2+100), pygame.SRCALPHA)
        alpha = int(12 + 6 * math.sin(t * 0.4 + i))
        pygame.draw.polygon(ray_surf, (255, 245, 200, alpha), pts)
        surf.blit(ray_surf, (0, 0))

def draw_horizon_glow(surf, mode):
    """Atmospheric glow band at horizon."""
    gy = HEIGHT - GROUND_H - 80
    if mode == "day":
        col = (220, 200, 120)
        alpha_max = 35
    else:
        col = (30, 60, 120)
        alpha_max = 45
    for i in range(60):
        t_i = i / 59.0
        a = int(alpha_max * math.sin(t_i * math.pi))
        s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        s.fill((*col, a))
        surf.blit(s, (0, gy + i - 30))

def draw_sun_cinematic(surf, t, mode):
    """Sun/moon — soft corona, no harsh rays or lens flare."""
    drift_x = int(WIDTH * 0.72 + math.sin(t * 0.06) * 25)
    drift_y = int(75  + math.cos(t * 0.05) * 14)

    if mode == "day":
        # Soft corona layers only — no rays
        corona_data = [(70, 6), (55, 14), (44, 28), (34, 55)]
        # Brighter, more saturated yellow corona for daylight sun
        corona_cols = [(255,250,160), (255,245,130), (255,238,100), (255,225,70)]
        for (cr, ca), cc in zip(corona_data, corona_cols):
            csurf = pygame.Surface((cr*2, cr*2), pygame.SRCALPHA)
            pygame.draw.circle(csurf, (*cc, ca), (cr, cr), cr)
            surf.blit(csurf, (drift_x-cr, drift_y-cr))
        # Core (brighter yellow)
        pygame.draw.circle(surf, (255, 245, 120), (drift_x, drift_y), 22)
        pygame.draw.circle(surf, (255, 255, 200), (drift_x-5, drift_y-5), 9)

    else:
        # Moon glow
        for r, a in [(44, 14), (32, 30)]:
            ms = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(ms, (200, 215, 255, a), (r,r), r)
            surf.blit(ms, (drift_x-r, drift_y-r))
        pygame.draw.circle(surf, (235, 242, 255), (drift_x, drift_y), 22)
        # Craters
        pygame.draw.circle(surf, (210, 220, 245), (drift_x+7,  drift_y-5), 5)
        pygame.draw.circle(surf, (210, 220, 245), (drift_x-5,  drift_y+8), 3)
        pygame.draw.circle(surf, (210, 220, 245), (drift_x+2,  drift_y+10), 2)
        pygame.draw.circle(surf, (255, 255, 255), (drift_x-6,  drift_y-5), 6)

def draw_stars_cinematic(surf, t):
    """Stars with twinkle, color variation, and cluster density."""
    for sx, sy, br, phase, size in STARS:
        twinkle = 0.55 + 0.45 * math.sin(t * (1.2 + br) + phase)
        a = int(220 * br * twinkle)
        if a <= 0:
            continue
        r = size
        star_col = (220, 228, 255) if br > 0.6 else (200, 210, 240)
        s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*star_col, a), (r+1, r+1), r)
        if br > 0.75 and size >= 2:
            # Cross sparkle
            pygame.draw.line(s, (*star_col, a//2), (0, r+1), (r*2+2, r+1), 1)
            pygame.draw.line(s, (*star_col, a//2), (r+1, 0), (r+1, r*2+2), 1)
        surf.blit(s, (sx-r-1, sy-r-1))

    # Star cluster nebula wisps
    for cx, cy, br in STAR_CLUSTERS:
        s = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (160, 170, 220, int(18*br)), (0,0,40,20))
        surf.blit(s, (cx-20, cy-10))

def draw_aurora_cinematic(surf, t):
    """Multi-layer aurora with smoother bands."""
    palette = [
        (20, 240, 120), (40, 180, 255), (160, 50, 240),
        (50, 240, 170), (80, 210, 255), (200, 100, 255)
    ]
    for i in range(6):
        phase  = t * 0.35 + i * 1.1
        base_y = 45 + i * 38
        col    = palette[i % len(palette)]
        alpha  = int(22 + 14 * math.sin(t * 0.55 + i * 0.8))
        steps  = 24
        pts    = []
        for s in range(steps+1):
            px2 = int(s * WIDTH / steps)
            amp  = 30 + i * 18
            py2  = int(base_y + amp * math.sin(phase + s * 0.42))
            pts.append((px2, py2))
        pts += [(WIDTH, 0), (0, 0)]
        if len(pts) >= 3:
            asurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(asurf, (*col, alpha), pts)
            surf.blit(asurf, (0, 0))

# ----------------------------- Ground (cobblestone) --------------------------
# Pre-bake cobblestone tile pattern
_cobble_tile_w = 96
_cobble_tile_h = GROUND_H
_cobble_tile   = None

def _build_cobble_tile():
    global _cobble_tile
    surf = pygame.Surface((_cobble_tile_w, _cobble_tile_h))
    surf.fill(GROUND_COBBLE_A)
    rng = random.Random(42)  # deterministic
    stones = [
        (0,  4, 28, 22), (30, 4, 24, 20), (56, 4, 36, 22),
        (8,  26,32, 18), (42,26, 28, 20), (72,26, 22, 18),
        (2,  44,26, 16), (30,44, 30, 16), (62,44, 30, 14),
        (4,  58,40, 10), (46,58, 38, 10),
    ]
    for (sx, sy, sw, sh) in stones:
        shade = rng.randint(-12, 12)
        base  = GROUND_COBBLE_B
        c = (clamp(base[0]+shade,0,255), clamp(base[1]+shade,0,255), clamp(base[2]+shade+8,0,255))
        pygame.draw.rect(surf, c, (sx, sy, sw, sh), border_radius=3)
        pygame.draw.rect(surf, (c[0]-15, c[1]-15, c[2]-15), (sx,sy,sw,sh), 1, border_radius=3)
        # Highlight top-left edge
        pygame.draw.line(surf, (c[0]+20,c[1]+20,c[2]+20), (sx+1,sy+1), (sx+sw-2,sy+1), 1)
    _cobble_tile = surf

_build_cobble_tile()

# Grass tufts (pre-baked list of offsets + sizes)
_grass_tufts = [(i*17 % _cobble_tile_w, random.Random(i).randint(2,7))
                for i in range(12)]

def draw_ground_cinematic(surf, scroll_t):
    """Cobblestone ground with animated grass tufts and glow edge."""
    offset = int(scroll_t * BASE_PIPE_SPEED * 28) % _cobble_tile_w

    # Tile cobblestone
    for xi in range(-1, WIDTH // _cobble_tile_w + 2):
        tx = xi * _cobble_tile_w - offset
        surf.blit(_cobble_tile, (tx, HEIGHT - GROUND_H))

    # Grass strip on top
    grass_y = HEIGHT - GROUND_H
    pygame.draw.rect(surf, GROUND_GRASS_A, (0, grass_y, WIDTH, 8))
    pygame.draw.rect(surf, GROUND_GRASS_B, (0, grass_y+8, WIDTH, 4))

    # Animated grass tufts
    for ti, (tx_base, tuft_h) in enumerate(_grass_tufts):
        tx = (tx_base - offset) % WIDTH
        wave = math.sin(scroll_t * 3.5 + ti * 0.7) * 2
        pts = [
            (tx,     grass_y + 1),
            (tx - 2 + int(wave), grass_y - tuft_h),
            (tx + 3, grass_y + 1),
        ]
        pygame.draw.polygon(surf, GROUND_EDGE, pts)

    # Glow line at top of ground
    for off, alpha in [(0, 90), (1, 40), (2, 15)]:
        gs = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        gs.fill((120, 240, 80, alpha))
        surf.blit(gs, (0, grass_y - off))

    # Subtle shadow below grass edge
    for off, alpha in [(1, 60), (2, 30), (3, 12)]:
        gs = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
        gs.fill((0, 0, 0, alpha))
        surf.blit(gs, (0, grass_y + 12 + off))

def draw_background(surf, t, mode="day"):
    sky = get_sky_surface(mode)
    surf.blit(sky, (0, 0))
    if mode == "day":
        draw_sun_cinematic(surf, t, mode)
        draw_horizon_glow(surf, mode)
    else:
        draw_stars_cinematic(surf, t)
        draw_aurora_cinematic(surf, t)
        draw_sun_cinematic(surf, t, mode)
        draw_horizon_glow(surf, mode)

# ----------------------------- Cloud system (realistic) ----------------------
class CloudSprite:
    """Billowing, lit, multi-layer cloud with soft depth shading."""

    def __init__(self, x=None, layer=1, mode=None):
        self.x     = WIDTH + random.randint(0, 400) if x is None else float(x)
        self.y     = random.randint(25, HEIGHT // 2 - 50)
        self.scale = random.uniform(0.55, 1.8)
        self.layer = layer
        self.mode  = mode or selected_bg
        speeds     = {1: 0.22, 2: 0.50, 3: 0.92}
        self.speed = speeds.get(layer, 0.5) * random.uniform(0.85, 1.15)
        self.surface  = None
        self.shadow_s = None
        self._build()

    def _build(self):
        sc   = self.scale
        bsz  = int(24 * sc)
        cw   = int(bsz * 5.5)
        ch   = int(bsz * 3.0)
        surf = pygame.Surface((cw, ch), pygame.SRCALPHA)

        is_night = (self.mode == "night")
        lit_col   = (240, 248, 255) if not is_night else (140, 150, 195)
        mid_col   = (210, 220, 240) if not is_night else (100, 108, 148)
        dark_col  = (175, 185, 210) if not is_night else ( 65,  72, 110)
        rim_col   = (255, 255, 255) if not is_night else (185, 195, 230)

        cx = cw // 2
        cy = int(ch * 0.55)

        # Puff definitions: (dx, dy, radius, lit_factor)
        puffs = [
            (0,                   0,           bsz,        1.00),
            (int(bsz * 0.92),     int(-bsz*0.28), int(bsz*0.82), 0.95),
            (int(-bsz * 0.88),    int(-bsz*0.22), int(bsz*0.78), 0.90),
            (int(bsz * 0.42),     int(-bsz*0.72), int(bsz*0.65), 0.92),
            (int(-bsz * 0.35),    int(-bsz*0.62), int(bsz*0.60), 0.88),
            (int(bsz * 1.55),     int(-bsz*0.10), int(bsz*0.62), 0.85),
            (int(-bsz * 1.52),    int(-bsz*0.08), int(bsz*0.58), 0.82),
        ]

        # Draw bottom dark layer first (depth)
        for dx, dy, r, lf in puffs:
            dc = lerp_color(mid_col, dark_col, 0.5)
            pygame.draw.circle(surf, dc, (cx+dx, cy+dy + r//4), int(r * 0.88))

        # Draw main body
        for dx, dy, r, lf in puffs:
            body_col = lerp_color(dark_col, lit_col, lf * 0.6)
            pygame.draw.circle(surf, body_col, (cx+dx, cy+dy), r)

        # Lit top layer
        for dx, dy, r, lf in puffs:
            top_col = lerp_color(mid_col, lit_col, lf)
            pygame.draw.circle(surf, top_col, (cx+dx, cy+dy - r//6), int(r * 0.75))

        # Specular rim removed to avoid small white highlight circles

        self.surface = surf

        # Ground shadow (stretched ellipse under the cloud)
        sh_w = int(cw * 0.75)
        sh_h = max(4, int(bsz * 0.25))
        self.shadow_s = pygame.Surface((sh_w, sh_h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow_s, (0,0,0,14), (0,0,sh_w,sh_h))

    def update(self, global_speed=1.0):
        self.x -= self.speed * global_speed

    def draw(self, surf, t=0, mode=None):
        target_mode = self.mode if mode is None else mode
        if target_mode != self.mode:
            self.mode = target_mode
            self._build()
        if not self.surface:
            return
        sx = int(self.x) - self.surface.get_width()  // 2
        sy = int(self.y) - self.surface.get_height() // 2
        surf.blit(self.surface, (sx, sy))

    def offscreen(self):
        return self.x < -self.surface.get_width() - 20 if self.surface else self.x < -300

# ----------------------------- 3D Pipe (chrome/steel) -----------------------
def draw_pipe_cinematic(surf, x, top_h, bot_y, bot_h, cam_offset=(0,0), width=90, mode="normal", pulse=0.0):
    ox, oy = cam_offset
    rim     = 20
    overhang= 10

    def _pipe_body(rx, ry, rw, rh):
        if rh <= 0:
            return

        # Base gradient (left=dark, center=mid, right=slight light)
        for i in range(rw):
            t_x = i / max(1, rw - 1)
            if t_x < 0.15:
                c = lerp_color(PIPE_CHROME_C, PIPE_CHROME_B, t_x / 0.15)
            elif t_x < 0.45:
                c = lerp_color(PIPE_CHROME_B, PIPE_CHROME_A, (t_x-0.15)/0.30)
            elif t_x < 0.72:
                c = lerp_color(PIPE_CHROME_A, PIPE_SHINE, (t_x-0.45)/0.27)
            else:
                c = lerp_color(PIPE_SHINE, PIPE_CHROME_B, (t_x-0.72)/0.28)
            pygame.draw.line(surf, c, (rx+i+ox, ry+oy), (rx+i+ox, ry+rh-1+oy))

        # Horizontal banding (subtle "metal segment" lines)
        seg_spacing = 40
        for sy_off in range(seg_spacing, rh, seg_spacing):
            band_s = pygame.Surface((rw, 2), pygame.SRCALPHA)
            band_s.fill((0, 0, 0, 30))
            surf.blit(band_s, (rx+ox, ry+sy_off+oy))
            band_s2 = pygame.Surface((rw, 1), pygame.SRCALPHA)
            band_s2.fill((255,255,255,15))
            surf.blit(band_s2, (rx+ox, ry+sy_off+2+oy))

        # Rivets down the left and right edges
        rivet_col = PIPE_RIVET
        for riv_y in range(12, rh, 28):
            for riv_x in [5, rw-7]:
                pygame.draw.circle(surf, rivet_col, (rx+riv_x+ox, ry+riv_y+oy), 3)
                pygame.draw.circle(surf, (200,255,160), (rx+riv_x-1+ox, ry+riv_y-1+oy), 1)

        # Outline
        pygame.draw.rect(surf, PIPE_CHROME_C, (rx+ox, ry+oy, rw, rh), 1)

    def _pipe_cap(rx, ry, rw, rh):
        cap_x = rx - overhang + ox
        cap_y = ry + oy
        cap_w = rw + overhang * 2

        # Gradient across cap
        for i in range(cap_w):
            t_x = i / max(1, cap_w - 1)
            if t_x < 0.1:
                c = PIPE_CHROME_C
            elif t_x < 0.35:
                c = lerp_color(PIPE_CHROME_B, PIPE_RIM_A, (t_x-0.1)/0.25)
            elif t_x < 0.65:
                c = lerp_color(PIPE_RIM_A, PIPE_SHINE, (t_x-0.35)/0.30)
            else:
                c = lerp_color(PIPE_SHINE, PIPE_CHROME_B, (t_x-0.65)/0.35)
            pygame.draw.line(surf, c, (cap_x+i, cap_y), (cap_x+i, cap_y+rh-1))

        # Top highlight
        pygame.draw.rect(surf, (200, 255, 160), (cap_x, cap_y, cap_w, 2))
        # Bottom shadow
        pygame.draw.rect(surf, PIPE_RIM_B, (cap_x, cap_y+rh-3, cap_w, 3))
        # Outline
        pygame.draw.rect(surf, PIPE_CHROME_C, (cap_x, cap_y, cap_w, rh), 1)

        # Rivets on cap
        for riv_x in [8, cap_w - 10]:
            pygame.draw.circle(surf, PIPE_RIVET, (cap_x + riv_x, cap_y + rh//2), 3)
            pygame.draw.circle(surf, (200,255,160), (cap_x+riv_x-1, cap_y+rh//2-1), 1)

    if top_h > 0:
        _pipe_body(x, 0, width, top_h - rim)
        _pipe_cap(x, top_h - rim, width, rim)

    if bot_h > 0:
        _pipe_body(x, bot_y + rim, width, bot_h - rim)
        _pipe_cap(x, bot_y, width, rim)

    if mode == "extreme":
        glow_alpha = int(65 + 45 * (0.5 + 0.5 * math.sin(pulse)))
        glow_w = width + overhang * 2 + 14
        glow_x = x - overhang - 7 + ox
        for edge_y in (top_h - 4, bot_y - 4):
            glow = pygame.Surface((glow_w, 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 105, 105, glow_alpha), (0, 2, glow_w, 4), border_radius=3)
            pygame.draw.rect(glow, (255, 220, 220, min(220, glow_alpha + 35)), (4, 3, glow_w - 8, 2), border_radius=2)
            surf.blit(glow, (glow_x, edge_y + oy))

# ----------------------------- Bird (with trail support) ----------
class Bird:
    def __init__(self, key="yellow", trail_key=None, accessories=None):
        self.w = 48; self.h = 36
        self.x = int(WIDTH * 0.25)
        self.y = int(HEIGHT * 0.45)
        self.vy = 0.0
        self.immunity = 0; self.coin_boost = 0; self.point_boost = 0; self.slow_motion = 0
        self.key = key
        self.color = BIRD_COLORS.get(self.key, (245,200,60))
        self.shine = BIRD_SHINE.get(self.key, (255,240,160))
        self.trail_key = trail_key or selected_trail_key
        self.trail_color = resolve_trail_color(self.trail_key, self.color)
        self.image = None
        self.anim_time = 0
        self.blink_timer = random.randint(60,180)
        self.trail = deque(maxlen=8)
        self.frame_count = 0  # FIX: track frames alive to suppress early trail
        self.accessories = build_default_accessory_selection()
        self.set_accessories(accessories)

        fname = ASSETS.get(f"bird_{self.key}", "")
        if fname and os.path.exists(fname):
            try:
                img = pygame.image.load(fname).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (self.w, self.h))
            except Exception:
                self.image = None

    def set_accessories(self, accessories=None):
        source = current_accessory_selection() if accessories is None else accessories
        if not isinstance(source, dict):
            source = {}
        self.accessories = {}
        for category in ACCESSORY_CATEGORY_ORDER:
            key = source.get(category, ACCESSORY_DEFAULTS[category])
            self.accessories[category] = key if key in ACCESSORY_KEYS[category] else ACCESSORY_DEFAULTS[category]

    def accessory_key(self, category):
        return self.accessories.get(category, ACCESSORY_DEFAULTS[category])

    def wing_palette(self):
        base_fill = lerp_color(self.color, (255, 255, 255), 0.35)
        base_outline = lerp_color(self.color, (0, 0, 0), 0.45)
        palettes = {
            "classic": (base_fill, base_outline, None),
            "rose": ((255, 166, 194), (140, 48, 78), (255, 220, 232)),
            "frost": ((185, 235, 255), (65, 120, 175), (240, 250, 255)),
            "emerald": ((100, 245, 170), (28, 120, 72), (208, 255, 224)),
            "royal": ((255, 224, 112), (145, 90, 18), (255, 248, 192)),
            "shadow": ((110, 100, 150), (35, 30, 62), (182, 170, 225)),
        }
        return palettes.get(self.accessory_key("wings"), (base_fill, base_outline, None))

    def eye_palette(self):
        palettes = {
            "classic": (WHITE, (20, 20, 20), (20, 20, 20), None),
            "amber": (WHITE, (255, 188, 58), (60, 36, 0), None),
            "emerald": (WHITE, (78, 228, 145), (18, 60, 40), None),
            "ruby": (WHITE, (255, 90, 105), (70, 10, 18), None),
            "violet": (WHITE, (185, 120, 255), (48, 22, 78), None),
            "neon": ((235, 250, 255), (95, 255, 235), (18, 50, 54), (95, 255, 235)),
        }
        return palettes.get(self.accessory_key("eyes"), palettes["classic"])

    def draw_hat(self, bsurf, px, py):
        hat_key = self.accessory_key("hat")
        cx = px + self.w // 2 - 2
        top_y = py - 10
        if hat_key == "none":
            return
        if hat_key == "beanie":
            pygame.draw.ellipse(bsurf, (210, 70, 90), (cx - 13, top_y + 1, 26, 14))
            pygame.draw.rect(bsurf, (120, 30, 45), (cx - 14, top_y + 10, 28, 6), border_radius=4)
            pygame.draw.circle(bsurf, (255, 220, 225), (cx, top_y + 1), 4)
        elif hat_key == "cowboy":
            pygame.draw.ellipse(bsurf, (94, 56, 28), (cx - 18, top_y + 10, 36, 8))
            pygame.draw.rect(bsurf, (126, 75, 38), (cx - 10, top_y - 4, 20, 16), border_radius=5)
            pygame.draw.rect(bsurf, (235, 190, 88), (cx - 8, top_y + 4, 16, 3), border_radius=2)
        elif hat_key == "top_hat":
            pygame.draw.rect(bsurf, (16, 18, 34), (cx - 15, top_y + 11, 30, 6), border_radius=3)
            pygame.draw.rect(bsurf, (28, 32, 52), (cx - 10, top_y - 10, 20, 22), border_radius=4)
            pygame.draw.rect(bsurf, NEON_GOLD, (cx - 10, top_y + 2, 20, 4), border_radius=2)
        elif hat_key == "crown":
            crown_pts = [(cx - 14, top_y + 12), (cx - 10, top_y - 2), (cx - 4, top_y + 6), (cx, top_y - 6), (cx + 4, top_y + 6), (cx + 10, top_y - 2), (cx + 14, top_y + 12)]
            pygame.draw.polygon(bsurf, (255, 212, 70), crown_pts)
            pygame.draw.polygon(bsurf, (158, 112, 18), crown_pts, 2)
            for gem_x, gem_c in ((cx - 7, (255, 90, 120)), (cx, (95, 245, 255)), (cx + 7, (120, 255, 150))):
                pygame.draw.circle(bsurf, gem_c, (gem_x, top_y + 5), 2)
        elif hat_key == "propeller":
            pygame.draw.ellipse(bsurf, (255, 72, 72), (cx - 14, top_y + 4, 28, 12))
            pygame.draw.rect(bsurf, (235, 235, 255), (cx - 14, top_y + 10, 28, 4), border_radius=2)
            pygame.draw.line(bsurf, (55, 55, 55), (cx, top_y + 4), (cx, top_y - 7), 2)
            pygame.draw.line(bsurf, (80, 220, 255), (cx - 10, top_y - 8), (cx + 10, top_y - 2), 3)
            pygame.draw.line(bsurf, (255, 225, 90), (cx - 10, top_y - 2), (cx + 10, top_y - 8), 3)

    def draw_neckwear(self, bsurf, px, py):
        neck_key = self.accessory_key("neckwear")
        if neck_key == "none":
            return
        base_x = px + self.w - 8
        base_y = py + 24
        scarf_x = base_x
        if neck_key == "red_scarf":
            pygame.draw.rect(bsurf, (230, 66, 72), (scarf_x - 8, base_y, 18, 7), border_radius=3)
            pygame.draw.polygon(bsurf, (190, 42, 56), [(scarf_x + 6, base_y + 5), (scarf_x + 16, base_y + 10), (scarf_x + 8, base_y + 18)])
        elif neck_key == "sky_scarf":
            pygame.draw.rect(bsurf, (95, 220, 255), (scarf_x - 8, base_y, 18, 7), border_radius=3)
            pygame.draw.polygon(bsurf, (52, 165, 220), [(scarf_x + 3, base_y + 5), (scarf_x + 15, base_y + 13), (scarf_x + 5, base_y + 18)])
        elif neck_key == "bow_tie":
            pygame.draw.polygon(bsurf, (195, 38, 145), [(base_x - 8, base_y + 4), (base_x - 2, base_y), (base_x - 1, base_y + 8)])
            pygame.draw.polygon(bsurf, (195, 38, 145), [(base_x + 8, base_y + 4), (base_x + 2, base_y), (base_x + 1, base_y + 8)])
            pygame.draw.circle(bsurf, (255, 220, 120), (base_x, base_y + 4), 3)
        elif neck_key == "necktie":
            pygame.draw.rect(bsurf, (60, 110, 230), (base_x - 3, base_y, 6, 9), border_radius=2)
            pygame.draw.polygon(bsurf, (38, 76, 180), [(base_x - 4, base_y + 8), (base_x + 4, base_y + 8), (base_x, base_y + 20)])
        elif neck_key == "royal_scarf":
            pygame.draw.rect(bsurf, (110, 54, 180), (scarf_x - 10, base_y, 22, 8), border_radius=4)
            pygame.draw.rect(bsurf, (255, 214, 94), (scarf_x - 6, base_y + 1, 12, 2), border_radius=1)
            pygame.draw.polygon(bsurf, (86, 38, 145), [(scarf_x + 7, base_y + 5), (scarf_x + 18, base_y + 13), (scarf_x + 10, base_y + 21)])

    def draw_face_gear(self, bsurf, ex, ey):
        face_key = self.accessory_key("face")
        if face_key == "none":
            return
        face_x = ex + 8
        if face_key == "round_glasses":
            pygame.draw.circle(bsurf, (40, 40, 55), (face_x - 7, ey), 5, 2)
            pygame.draw.circle(bsurf, (40, 40, 55), (face_x + 3, ey), 5, 2)
            pygame.draw.line(bsurf, (40, 40, 55), (face_x - 2, ey), (face_x - 1, ey), 2)
        elif face_key == "monocle":
            pygame.draw.circle(bsurf, (230, 210, 110), (ex, ey), 6, 2)
            pygame.draw.line(bsurf, (230, 210, 110), (ex + 4, ey + 5), (ex + 7, ey + 12), 1)
        elif face_key == "sunglasses":
            pygame.draw.rect(bsurf, (20, 20, 28), (face_x - 13, ey - 4, 11, 8), border_radius=3)
            pygame.draw.rect(bsurf, (20, 20, 28), (face_x - 1, ey - 4, 11, 8), border_radius=3)
            pygame.draw.line(bsurf, (65, 65, 85), (face_x - 2, ey), (face_x - 1, ey), 2)
        elif face_key == "aviators":
            pygame.draw.ellipse(bsurf, (170, 210, 255), (face_x - 13, ey - 5, 10, 9))
            pygame.draw.ellipse(bsurf, (170, 210, 255), (face_x - 1, ey - 5, 10, 9))
            pygame.draw.ellipse(bsurf, (58, 88, 135), (face_x - 13, ey - 5, 10, 9), 2)
            pygame.draw.ellipse(bsurf, (58, 88, 135), (face_x - 1, ey - 5, 10, 9), 2)
            pygame.draw.line(bsurf, (58, 88, 135), (face_x - 3, ey - 1), (face_x - 1, ey - 1), 2)
        elif face_key == "visor":
            visor = pygame.Surface((22, 10), pygame.SRCALPHA)
            pygame.draw.rect(visor, (85, 245, 255, 170), (0, 0, 22, 10), border_radius=4)
            pygame.draw.rect(visor, (30, 110, 120, 220), (0, 0, 22, 10), 2, border_radius=4)
            bsurf.blit(visor, (ex - 11, ey - 5))

    def tail_anchor(self):
        return (self.x - 8, self.y + self.h * 0.45)

    def trail_anchor(self):
        return (self.x + 2, self.y + self.h * 0.5)

    def flap(self):
        # During slow motion gravity is halved, so flap needs to be stronger
        # to give the same effective upward movement.
        slow_mult = 0.8 if self.slow_motion > 0 else 1.0
        self.vy = FLAP_STRENGTH * slow_mult
        play_sound(SOUND_FLAP)
        # Only spawn flap particles if bird has been alive a bit (avoid startup burst)
        if self.frame_count > 5:
            tail_x, tail_y = self.tail_anchor()
            spawn_particles(tail_x, tail_y, (200,220,255), count=6, life=16, speed=2.0, glow=True)

    def update(self):
        gravity = GRAVITY * (0.55 if self.slow_motion > 0 else 1.0)
        self.vy += gravity
        self.y  += self.vy
        self.frame_count += 1
        # Only record trail after first several frames
        if self.frame_count > 10:
            self.trail.append(self.trail_anchor())
        self.anim_time += 1
        self.blink_timer -= 1
        if self.blink_timer <= 0:
            self.blink_timer = random.randint(120,240)
        if self.immunity  > 0: self.immunity  -= 1
        if self.coin_boost > 0: self.coin_boost -= 1
        if self.point_boost > 0: self.point_boost -= 1
        if self.slow_motion > 0: self.slow_motion -= 1

    def update_idle(self, base_y, t):
        self.y = base_y + math.sin(t * 3.6) * 7
        self.vy = math.cos(t * 3.6) * 0.45
        self.anim_time += 1
        self.blink_timer -= 1
        if self.blink_timer <= 0:
            self.blink_timer = random.randint(120,240)

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def collision_points(self):
        cx = self.x + self.w * 0.5
        cy = self.y + self.h * 0.5
        rx = self.w * BIRD_HITBOX_SCALE_X
        ry = self.h * BIRD_HITBOX_SCALE_Y
        angle = math.radians(clamp(-self.vy * 3, -45, 45))
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        def rotate_point(ox, oy):
            return (
                cx + ox * cos_a - oy * sin_a,
                cy + ox * sin_a + oy * cos_a,
            )

        points = [(cx, cy)]
        for idx in range(12):
            theta = idx * math.tau / 12.0
            points.append(rotate_point(math.cos(theta) * rx, math.sin(theta) * ry))
        for ox, oy in ((rx * 0.55, 0), (-rx * 0.55, 0), (0, ry * 0.55), (0, -ry * 0.55)):
            points.append(rotate_point(ox, oy))
        return points

    def collision_bounds(self):
        points = self.collision_points()
        xs = [pt[0] for pt in points]
        ys = [pt[1] for pt in points]
        return min(xs), min(ys), max(xs), max(ys)

    def draw(self, surf, cam_offset=(0,0)):
        ox, oy = cam_offset

        # Motion trail — only show after enough frames and if trail is not "none"
        if self.frame_count > 10 and self.trail_key != "none":
            trail_list = list(self.trail)
            n = max(1, len(trail_list))
            for i, (tx, ty) in enumerate(trail_list):
                frac = (i + 1) / n    # oldest = faintest, newest = strongest
                back_offset = (n - i - 1) * 6
                a = int(200 * frac)
                r = max(2, int(9 * frac))
                ts = pygame.Surface((r*2+1, r*2+1), pygame.SRCALPHA)
                pygame.draw.circle(ts, (*self.trail_color, a), (r, r), r)
                surf.blit(ts, (tx+ox-back_offset-r, ty+oy-r), special_flags=pygame.BLEND_RGBA_ADD)

        # Immunity glow
        if self.immunity > 0:
            pulse = 1.0 + 0.15*math.sin(self.anim_time*0.3)
            for r, a in [(int(36*pulse),25),(int(28*pulse),50),(int(22*pulse),80)]:
                gs = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
                pygame.draw.circle(gs, (255,255,120,a),(r,r),r)
                surf.blit(gs,(self.x+self.w//2+ox-r, self.y+self.h//2+oy-r))

        if self.image:
            bsurf = pygame.Surface((self.w+20, self.h+20), pygame.SRCALPHA)
            bsurf.blit(self.image, (10, 10))
            angle = clamp(-self.vy*3, -45, 45)
            rot = pygame.transform.rotate(bsurf, angle)
            r = rot.get_rect(center=(self.x+self.w//2+ox, self.y+self.h//2+oy))
            surf.blit(rot, r.topleft)
            return

        # -------- 3D-shaded procedural bird --------
        bx = self.x+ox; by = self.y+oy
        angle_deg = clamp(-self.vy*3,-45,45)

        bw, bh = self.w+20, self.h+20
        bsurf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        px, py = 10, 10

        # Tail (drawn behind the body) with outline
        tail_outline_color = (0, 0, 0)  # Black outline
        tail_main_color = lerp_color(self.color, (0,0,0), 0.15)
        # Draw outline first (around the tail)
        pygame.draw.lines(bsurf, tail_outline_color, True, [
            (px-8, py+16), (px+4, py+12), (px+4, py+24)
        ], 2)
        # Draw main tail on top
        pygame.draw.polygon(bsurf, tail_main_color, [
            (px-8, py+16), (px+4, py+12), (px+4, py+24)
        ])

        # Body
        pygame.draw.ellipse(bsurf, self.color, (px, py, self.w, self.h))

# Body outline — darker border around the whole bird
        outline_col = lerp_color(self.color, (0, 0, 0), 0.45)
        pygame.draw.ellipse(bsurf, outline_col, (px - 2, py - 2, self.w + 4, self.h + 4))
        # Body redrawn on top of outline
        pygame.draw.ellipse(bsurf, self.color, (px, py, self.w, self.h))

        # Wing (animated) — bright ellipse on top, no shadow
        wing_phase = math.sin(self.anim_time * 0.35)
        wh = int(14 + wing_phase * 8)
        wing_fill, wing_outline, _ = self.wing_palette()
        wing_rect = pygame.Rect(px + 10, py + 8, 22, wh)
        wing_key = self.accessory_key("wings")
        if wing_key in ("royal", "shadow"):
            glow_col = wing_fill if wing_key == "shadow" else (255, 238, 155)
            glow = pygame.Surface((wing_rect.w + 12, wing_rect.h + 12), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*glow_col, 50), (0, 0, glow.get_width(), glow.get_height()))
            bsurf.blit(glow, (wing_rect.x - 6, wing_rect.y - 5))
        pygame.draw.ellipse(bsurf, wing_outline, (px + 9, py + 7, 24, wh + 2))
        pygame.draw.ellipse(bsurf, wing_fill, wing_rect)
        self.draw_neckwear(bsurf, px, py)

        # Beak
        beak_col = (255,170,50)
        pygame.draw.polygon(bsurf, beak_col, [
            (px+self.w-4, py+16),
            (px+self.w+8, py+20),
            (px+self.w-4, py+24),
        ])
        pygame.draw.line(bsurf, (200,110,20),(px+self.w-4, py+20),(px+self.w+8, py+20),1)

        # Eye
        ex = px+self.w-14; ey = py+10
        sclera_col, iris_col, pupil_col, glow_col = self.eye_palette()
        pygame.draw.circle(bsurf, sclera_col, (ex, ey), 6)
        pygame.draw.circle(bsurf, (30,30,30), (ex, ey), 6, 1)
        if self.blink_timer < 10:
            pygame.draw.line(bsurf, BLACK, (ex-4, ey),(ex+4, ey), 2)
        else:
            if self.accessory_key("eyes") == "classic":
                pygame.draw.circle(bsurf, iris_col, (ex+1,ey),3)
                pygame.draw.circle(bsurf, (200,200,255),(ex+2,ey-1),1)
            else:
                if glow_col is not None:
                    glow = pygame.Surface((18, 18), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (*glow_col, 70), (9, 9), 8)
                    bsurf.blit(glow, (ex - 9, ey - 9))
                pygame.draw.circle(bsurf, iris_col, (ex+1, ey), 3)
                pygame.draw.circle(bsurf, pupil_col, (ex+1, ey), 1)
                pygame.draw.circle(bsurf, (245, 250, 255), (ex+2, ey-1), 1)

        self.draw_face_gear(bsurf, ex, ey)
        self.draw_hat(bsurf, px, py)

        rotated = pygame.transform.rotate(bsurf, angle_deg)
        rr = rotated.get_rect(center=(bx+self.w//2, by+self.h//2))
        surf.blit(rotated, rr.topleft)

# ----------------------------- Pipe class ------------------------------------
class Pipe:
    def __init__(self, x, mode="normal", intro_strength=0.0):
        self.x      = x
        self.width  = 90
        self.mode   = mode
        self.intro_strength = clamp(intro_strength, 0.0, 1.0)
        if mode == "extreme":
            intro_gap_bonus = int(36 * self.intro_strength)
            self.gap    = random.randint(EXTREME_GAP_MIN + intro_gap_bonus, EXTREME_GAP_MAX + intro_gap_bonus)
            self.top    = random.randint(96, HEIGHT - 340)
            self.bottom = HEIGHT - (self.top + self.gap)
            self.phase  = random.uniform(0, 2 * math.pi)
            self.amp    = random.randint(*EXTREME_TOP_SWING)
            self.gap_phase = random.uniform(0, 2 * math.pi)
            self.gap_amp = random.randint(*EXTREME_GAP_SWING)
            self.top_speed = random.uniform(1.15, 1.55)
            self.gap_speed = random.uniform(1.8, 2.35)
            if self.intro_strength > 0:
                ease = 1.0 - self.intro_strength * 0.45
                self.amp = int(self.amp * ease)
                self.gap_amp = int(self.gap_amp * ease)
        else:
            intro_gap_bonus = int(34 * self.intro_strength)
            self.gap    = random.randint(PIPE_GAP_MIN + intro_gap_bonus, PIPE_GAP_MAX + intro_gap_bonus)
            self.top    = random.randint(88, HEIGHT - 320)
            self.bottom = HEIGHT - (self.top + self.gap)
            self.phase  = 0
            self.amp    = 0
            self.gap_phase = 0
            self.gap_amp = 0
            self.top_speed = 0.0
            self.gap_speed = 0.0
        self.initial_top = self.top
        self.initial_gap = self.gap
        self.passed = False

    def update(self, speed, t):
        self.x -= speed
        if self.mode == "extreme":
            self.top = self.initial_top + math.sin(self.phase + t * self.top_speed) * self.amp
            gap_change = math.sin(self.gap_phase + t * self.gap_speed) * self.gap_amp
            self.gap = int(clamp(self.initial_gap + gap_change, 92, 225))
            top_limit = HEIGHT - GROUND_H - self.gap - 56
            self.top = int(clamp(self.top, 32, max(48, top_limit)))
            self.bottom = int(HEIGHT - (self.top + self.gap))

    def offscreen(self):
        return self.x + self.width < 0

    def rects(self):
        return (pygame.Rect(int(self.x), 0, self.width, self.top),
                pygame.Rect(int(self.x), HEIGHT - self.bottom, self.width, self.bottom))

    def collide(self, bird_rect):
        for r in self.rects():
            if bird_rect.colliderect(r):
                return True
        return False

    def draw(self, surf, t=0, cam_offset=(0,0)):
        draw_pipe_cinematic(surf, int(self.x), int(self.top), int(HEIGHT - self.bottom),
                            int(self.bottom), cam_offset=cam_offset, width=self.width,
                            mode=self.mode, pulse=self.gap_phase + t * max(1.0, self.gap_speed))

# ----------------------------- PowerUp (neon orb) ----------------------------
class PowerUp:
    TYPES       = ["immunity", "coin_boost", "point_boost", "slow_motion"]
    TYPE_WEIGHTS = [1.0, 1.0, 0.85, 1.0]
    NEON_COLORS = {
        "immunity":    (100, 255, 180),
        "coin_boost":  NEON_GOLD,
        "point_boost": (178, 96, 255),
        "slow_motion": (255, 140, 140)
    }
    ICONS = {"immunity": "★", "coin_boost": "2x", "point_boost": "2P", "slow_motion": "⏱"}

    def __init__(self, x):
        self.type   = random.choices(self.TYPES, weights=self.TYPE_WEIGHTS, k=1)[0]
        self.x      = float(x)
        self.y      = random.randint(80, HEIGHT - 120)
        self.size   = POWERUP_SIZE
        self.active = True
        self.spin   = 0.0
        self.t      = 0.0

    def update(self, speed):
        self.x    -= speed
        self.spin += 6.5
        self.t    += 1

    def offscreen(self):
        return self.x + self.size < -40

    def draw(self, surf, cam_offset=(0,0)):
        if not self.active:
            return
        ox, oy  = cam_offset
        col     = self.NEON_COLORS.get(self.type, (200, 200, 200))
        # Keep core radius fixed (no pulsing) so orb stays the smaller size
        core_r  = max(2, int(self.size / 2))
        cx      = int(self.x + self.size//2 + ox)
        cy      = int(self.y + self.size//2 + oy)

        # Glow effect - draw multiple circles with decreasing alpha
        for glow_r, alpha in [(core_r + 8, 30), (core_r + 6, 50), (core_r + 4, 80)]:
            glow_surf = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*col, alpha), (glow_r, glow_r), glow_r)
            surf.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # Orb
        orb_sz = core_r*2 + 4
        orb    = pygame.Surface((orb_sz, orb_sz), pygame.SRCALPHA)
        oc     = orb_sz // 2
        pygame.draw.circle(orb, col, (oc, oc), core_r)

        bright = lerp_color(col, (255,255,255), 0.3)
        pygame.draw.circle(orb, (*bright, 150), (oc, oc), core_r, 2)
        # Specular spot
        pygame.draw.circle(orb, (*bright, 200), (oc - core_r//3, oc - core_r//3), max(2, core_r//4))
        surf.blit(orb, (cx-oc, cy-oc))

# ----------------------------- UI helpers ------------------------------------
_glass_panel_cache = {}
_glow_text_cache = {}
_vignette_cache = {}
_preview_cache = {}

def _cache_guard(cache, limit=256):
    if len(cache) > limit:
        cache.clear()

def get_glass_panel_surface(w, h, alpha=40, border_col=(255,255,255,80), radius=14):
    key = (w, h, alpha, tuple(border_col), radius)
    panel = _glass_panel_cache.get(key)
    if panel is not None:
        return panel

    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (255,255,255,alpha), (0,0,w,h), border_radius=radius)
    pygame.draw.rect(panel, border_col, (0,0,w,h), 2, border_radius=radius)
    sheen_w = max(0, w - 4)
    if sheen_w:
        sheen = pygame.Surface((sheen_w, 10), pygame.SRCALPHA)
        pygame.draw.rect(sheen, (255,255,255,45), (0,0,sheen_w,10), border_radius=8)
        panel.blit(sheen, (2,2))
    _glass_panel_cache[key] = panel
    return panel

def draw_glass_panel(surf, x, y, w, h, alpha=40, border_col=(255,255,255,80), radius=14):
    surf.blit(get_glass_panel_surface(w, h, alpha, border_col, radius), (x, y))

def get_glow_text_surface(text, font, color, glow_color, glow_r=3):
    key = (id(font), text, tuple(color), tuple(glow_color), glow_r)
    cached = _glow_text_cache.get(key)
    if cached is not None:
        return cached

    rendered = font.render(text, True, color)
    glow_base = font.render(text, True, glow_color)
    pad = glow_r + 2
    surf = pygame.Surface((rendered.get_width() + pad * 2,
                           rendered.get_height() + pad * 2), pygame.SRCALPHA)
    for dx in range(-glow_r, glow_r + 1):
        for dy in range(-glow_r, glow_r + 1):
            if dx == 0 and dy == 0:
                continue
            dist = math.sqrt(dx * dx + dy * dy)
            alpha = int(80 * (1 - dist / max(1, glow_r + 1)))
            if alpha <= 0:
                continue
            glow = glow_base.copy()
            glow.set_alpha(alpha)
            surf.blit(glow, (pad + dx, pad + dy))
    surf.blit(rendered, (pad, pad))
    cached = (surf, rendered.get_width(), rendered.get_height(), pad)
    _cache_guard(_glow_text_cache)
    _glow_text_cache[key] = cached
    return cached

def draw_glow_text(surf, text, font, x, y, color, glow_color, center=True, glow_r=3):
    text_surf, text_w, text_h, pad = get_glow_text_surface(text, font, color, glow_color, glow_r)
    draw_x = x - text_w // 2 - pad if center else x - pad
    draw_y = y - text_h // 2 - pad
    surf.blit(text_surf, (draw_x, draw_y))

def get_vignette_surface(size):
    vignette = _vignette_cache.get(size)
    if vignette is not None:
        return vignette

    w, h = size
    sample_w = max(64, w // 8)
    sample_h = max(64, h // 8)
    pixels = bytearray(sample_w * sample_h * 4)
    cx = (sample_w - 1) / 2.0
    cy = (sample_h - 1) / 2.0

    for y in range(sample_h):
        ny = (y - cy) / max(1.0, cy)
        for x in range(sample_w):
            nx = (x - cx) / max(1.0, cx)
            dist = math.sqrt(nx * nx + ny * ny)
            t = clamp((dist - 0.72) / 0.45, 0.0, 1.0)
            alpha = int(82 * (t ** 1.8))
            idx = (y * sample_w + x) * 4
            pixels[idx + 3] = alpha

    small = pygame.image.frombuffer(bytes(pixels), (sample_w, sample_h), "RGBA")
    vignette = pygame.transform.smoothscale(small, (w, h))
    _vignette_cache[size] = vignette
    return vignette

def draw_vignette(surf):
    if not SETTINGS["vignette"]:
        return
    surf.blit(get_vignette_surface(surf.get_size()), (0, 0))

def get_bg_preview_surface(mode):
    preview = _preview_cache.get(mode)
    if preview is not None:
        return preview

    preview = pygame.Surface((196, 126))
    if mode == "day":
        for y in range(126):
            t_s = y / 125.0
            c2 = lerp_color(DAY_SKY_ZENITH, DAY_SKY_HAZE, t_s)
            pygame.draw.line(preview, c2, (0, y), (196, y))
        pygame.draw.circle(preview, (255, 240, 100), (155, 22), 12)
    else:
        rng = random.Random(7)
        for y in range(126):
            t_s = y / 125.0
            c2 = lerp_color(NIGHT_SKY_ZENITH, NIGHT_SKY_BOT, t_s)
            pygame.draw.line(preview, c2, (0, y), (196, y))
        pygame.draw.circle(preview, (230, 235, 255), (155, 22), 10)
        for _ in range(30):
            pygame.draw.circle(preview, (200, 210, 250),
                               (rng.randint(0, 196), rng.randint(0, 60)), 1)
    _preview_cache[mode] = preview
    return preview

def draw_fps_overlay(surf):
    if not SETTINGS["show_fps"]:
        return
    fps_text = TINY.render(f"{int(CLOCK.get_fps())} FPS", True, (220, 240, 255))
    badge_y = 8
    badge_h = 30
    fps_y = badge_y + badge_h + 4
    draw_glass_panel(surf, WIDTH - fps_text.get_width() - 22, fps_y,
                     fps_text.get_width() + 14, 20, alpha=36, radius=10)
    surf.blit(fps_text, (WIDTH - fps_text.get_width() - 15, fps_y + 5))

def draw_persistence_alert(surf, y=None):
    alert = active_persistence_alert()
    if not alert:
        return
    max_w = WIDTH - 36
    text = fit_text_to_width(alert["text"], SMALL, max_w - 20)
    text_surf = SMALL.render(text, True, alert["color"])
    panel_w = min(max_w, text_surf.get_width() + 20)
    panel_h = 28
    panel_x = WIDTH // 2 - panel_w // 2
    panel_y = HEIGHT - GROUND_H - 86 if y is None else y
    border = (*alert["color"], 110)
    draw_glass_panel(surf, panel_x, panel_y, panel_w, panel_h, alpha=52, border_col=border, radius=12)
    surf.blit(text_surf, (panel_x + (panel_w - text_surf.get_width()) // 2, panel_y + 6))
# Score pop animation
score_pops = []

def add_score_pop(x, y, amount):
    score_pops.append({"x":x,"y":float(y),"vy":-2.2,"alpha":255,"amount":amount,"timer":55})

def update_draw_score_pops(surf):
    dead = []
    for sp in score_pops:
        sp["y"]  += sp["vy"]
        sp["vy"] *= 0.93
        sp["alpha"] = max(0, sp["alpha"]-4.5)
        sp["timer"] -= 1
        if sp["timer"] <= 0:
            dead.append(sp); continue
        pop_text = f"+{sp['amount']}"
        # Golden glowing popup with black outline
        outline_color = (0, 0, 0)
        main_color = (255, 245, 90)
        # Draw outline by rendering text in black at offset positions
        for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
            outline_text = MED.render(pop_text, True, outline_color)
            outline_text.set_alpha(int(sp["alpha"]))
            surf.blit(outline_text, (int(sp["x"]) + dx, int(sp["y"]) + dy))
        # Draw main golden text on top
        t2 = MED.render(pop_text, True, main_color)
        t2.set_alpha(int(sp["alpha"]))
        surf.blit(t2, (int(sp["x"]), int(sp["y"])))
    for d in dead:
        try: score_pops.remove(d)
        except Exception: pass

# ----------------------------- Cinematic Button ------------------------------
class Button:
    def __init__(self, x, y, w, h, text, icon="", accent_col=None):
        self.rect       = pygame.Rect(x, y, w, h)
        self.text       = text
        self.icon       = icon
        self.accent_col = accent_col or NEON_GOLD
        self._hover     = False
        self._press_t   = 0
        self.selected   = False

    def draw(self, surf, t):
        mx, my      = pygame.mouse.get_pos()
        self._hover = self.rect.collidepoint(mx, my)
        floaty = int(math.sin(t * 1.3 + self.rect.y * 0.018) * 2)
        r      = self.rect.copy()
        r.y   += floaty

        # Shadow
        shd = pygame.Surface((r.w+10, r.h+10), pygame.SRCALPHA)
        pygame.draw.rect(shd, (0,0,0, 80 if self._hover or self.selected else 35), (5,5,r.w,r.h), border_radius=16)
        surf.blit(shd, (r.x-5, r.y-5))

        panel = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        if self._hover or self.selected:
            pygame.draw.rect(panel, (*self.accent_col, 55), (0,0,r.w,r.h), border_radius=16)
            # Neon border glow
            for bw, ba in [(3,100),(2,160),(1,220)]:
                pygame.draw.rect(panel, (*self.accent_col, ba), (0,0,r.w,r.h), bw, border_radius=16)
        else:
            pygame.draw.rect(panel, (255,255,255,28), (0,0,r.w,r.h), border_radius=16)
            pygame.draw.rect(panel, (255,255,255,90), (0,0,r.w,r.h), 1, border_radius=16)

        # Sheen
        sheen = pygame.Surface((r.w-8, 11), pygame.SRCALPHA)
        pygame.draw.rect(sheen, (255,255,255,50), (0,0,r.w-8,11), border_radius=8)
        panel.blit(sheen, (4,3))
        surf.blit(panel, r.topleft)

        # Text
        if self.text == "Extreme" and (self._hover or self.selected):
            text_col = (255, 100, 100)  # Bright red for Extreme button when hovered
        else:
            text_col = lerp_color((240,240,255), self.accent_col, 0.9) if self._hover or self.selected else (235,240,255)
        txt = FONT.render(self.text, True, text_col)
        surf.blit(txt, (r.centerx - txt.get_width()//2, r.centery - txt.get_height()//2))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# ----------------------------- Game State ------------------------------------
class GameState:
    def __init__(self, mode="normal"):
        global selected_bird_key, selected_bg, selected_trail_key
        particles.clear()
        score_pops.clear()
        self.mode        = mode
        self.bird        = Bird(selected_bird_key, trail_key=selected_trail_key)
        self.bg_mode     = current_bg_mode(mode)
        self.waiting_to_start = True
        self.run_started_at = None
        self.idle_bird_y = float(self.bird.y)
        self.pipes_spawned = 0
        first_pipe_x = WIDTH + int(PIPE_SPAWN_INTERVAL * FPS * (BASE_PIPE_SPEED * 1.5))
        self.pipes       = [self.make_pipe(first_pipe_x)]
        self.powerups    = []
        self.score       = 0
        self.spawn_timer = 0.0
        self.clouds      = (
            [CloudSprite(random.randint(0,WIDTH), layer=1, mode=self.bg_mode) for _ in range(3)] +
            [CloudSprite(random.randint(0,WIDTH), layer=2, mode=self.bg_mode) for _ in range(3)] +
            [CloudSprite(random.randint(0,WIDTH), layer=3, mode=self.bg_mode) for _ in range(2)]
        )
        self.paused      = False
        self.shake_timer = 0.0
        self.start_time  = time.time()
        self.scroll_t    = 0.0
        self.run_flaps   = 0
        self.run_powerups = 0
        self.run_coins   = 0

    def make_pipe(self, x):
        intro_strength = max(0.0, 1.0 - (self.pipes_spawned / max(1, START_PIPE_COUNT)))
        pipe = Pipe(x, self.mode, intro_strength=intro_strength)
        self.pipes_spawned += 1
        return pipe

    def start_run(self):
        if self.waiting_to_start:
            self.waiting_to_start = False
            self.run_started_at = time.time()

    def run_elapsed(self):
        if self.run_started_at is None:
            return 0.0
        return max(0.0, time.time() - self.run_started_at)

    def speed_scale(self):
        return lerp(START_SPEED_SCALE, 1.0, clamp(self.run_elapsed() / START_GRACE_SEC, 0.0, 1.0))

def sec_left(frames):
    return int(frames / FPS)

def current_bg_mode(mode="normal"):
    return "night" if mode == "extreme" else selected_bg

def draw_coin_badge(surf, x, y, coins=None, align_right=False):
    show_infinite = (coins is None and cheat_enabled("infinite_gold"))
    coin_text = "INF" if show_infinite else str(max(0, int(PLAYER_DATA.get("coins", 0) if coins is None else coins)))
    value = SMALL.render(coin_text, True, (255, 244, 180))
    panel_w = max(76, value.get_width() + 38)
    panel_h = 30
    if align_right:
        x -= panel_w

    draw_glass_panel(surf, x, y, panel_w, panel_h, alpha=58, border_col=(255, 220, 120, 110), radius=12)
    coin_center = (x + 15, y + panel_h // 2)
    pygame.draw.circle(surf, (180, 120, 20), coin_center, 8)
    pygame.draw.circle(surf, NEON_GOLD, coin_center, 6)
    pygame.draw.circle(surf, (255, 246, 180), (coin_center[0] - 2, coin_center[1] - 2), 2)
    surf.blit(value, (x + 28, y + panel_h // 2 - value.get_height() // 2 + 1))
    return pygame.Rect(x, y, panel_w, panel_h)

def progress_ratio(quest, daily=False):
    return clamp(get_quest_progress(quest, daily) / max(1, quest["goal"]), 0.0, 1.0)

def trigger_flap(gs):
    gs.start_run()
    gs.bird.flap()
    gs.run_flaps += 1

def finish_run(gs):
    refresh_daily_quests()
    duration = gs.run_elapsed()
    run_coins = gs.run_coins
    mode_games_key = "extreme_games_played" if gs.mode == "extreme" else "normal_games_played"
    mode_best_key = "best_extreme_score" if gs.mode == "extreme" else "best_normal_score"

    PLAYER_STATS["games_played"] += 1
    PLAYER_STATS[mode_games_key] += 1
    PLAYER_STATS["best_score"] = max(PLAYER_STATS["best_score"], gs.score)
    PLAYER_STATS[mode_best_key] = max(PLAYER_STATS[mode_best_key], gs.score)
    PLAYER_STATS["total_score"] += gs.score
    PLAYER_STATS["total_flaps"] += gs.run_flaps
    PLAYER_STATS["powerups_collected"] += gs.run_powerups
    PLAYER_STATS["longest_run_sec"] = max(PLAYER_STATS["longest_run_sec"], duration)
    PLAYER_STATS["total_run_time_sec"] += duration
    PLAYER_STATS["coins_earned"] += run_coins

    daily_stats = PLAYER_DATA["daily_stats"]
    daily_stats["games_played"] += 1
    daily_stats[mode_games_key] += 1
    daily_stats["best_score"] = max(daily_stats["best_score"], gs.score)
    daily_stats[mode_best_key] = max(daily_stats[mode_best_key], gs.score)
    daily_stats["total_score"] += gs.score
    daily_stats["flaps"] += gs.run_flaps
    daily_stats["powerups_collected"] += gs.run_powerups
    daily_stats["longest_run_sec"] = max(daily_stats["longest_run_sec"], duration)

    PLAYER_DATA["coins"] += run_coins
    rewards = complete_ready_quests()
    quest_bonus = sum(reward for _, reward, _ in rewards)

    save_stats()
    save_player_data()
    return run_coins, quest_bonus, len(rewards)

def get_item_status(category, key):
    if category == "bird":
        owned = key in PLAYER_DATA["owned_birds"]
        selected = key == selected_bird_key
        cost = BIRD_COSTS.get(key, 0)
    elif category == "background":
        owned = key in PLAYER_DATA["owned_backgrounds"]
        selected = key == selected_bg
        cost = BG_COSTS.get(key, 0)
    else:
        owned = key in PLAYER_DATA["owned_trails"]
        selected = key == selected_trail_key
        cost = TRAIL_COSTS.get(key, 0)

    if owned and selected:
        return "Equipped", NEON_GREEN
    if owned:
        return "Owned", (220, 235, 255)
    affordable = cheat_enabled("infinite_gold") or PLAYER_DATA["coins"] >= cost
    return f"{cost}c", NEON_GOLD if affordable else (255, 125, 125)

def buy_or_equip_item(category, key):
    global selected_bird_key, selected_bg, selected_trail_key

    if category == "bird":
        owned_key = "owned_birds"
        cost = BIRD_COSTS.get(key, 0)
        item_label = f"{key.capitalize()} skin"
    elif category == "background":
        owned_key = "owned_backgrounds"
        cost = BG_COSTS.get(key, 0)
        item_label = f"{key.capitalize()} mode"
    else:
        owned_key = "owned_trails"
        trail_name = next((label for trail_key, label, _ in TRAIL_OPTIONS if trail_key == key), key.capitalize())
        cost = TRAIL_COSTS.get(key, 0)
        item_label = f"{trail_name} trail"

    purchased = False
    used_infinite_gold = cheat_enabled("infinite_gold")
    if key not in PLAYER_DATA[owned_key]:
        if not used_infinite_gold and PLAYER_DATA["coins"] < cost:
            missing = cost - PLAYER_DATA["coins"]
            return False, f"Need {missing} more coins for {item_label}.", 0
        if not used_infinite_gold:
            PLAYER_DATA["coins"] -= cost
            PLAYER_STATS["coins_spent"] += cost
            PLAYER_DATA["daily_stats"]["coins_spent"] += cost
        PLAYER_DATA[owned_key].append(key)
        PLAYER_STATS["items_bought"] += 1
        PLAYER_DATA["daily_stats"]["items_bought"] += 1
        purchased = True

    if category == "bird":
        selected_bird_key = key
    elif category == "background":
        selected_bg = key
    else:
        selected_trail_key = key

    save_settings()
    rewards = complete_ready_quests()
    quest_bonus = sum(reward for _, reward, _ in rewards)
    save_stats()
    save_player_data()

    if purchased:
        if used_infinite_gold:
            message = f"Unlocked and equipped {item_label} with Infinite Gold."
        else:
            message = f"Bought and equipped {item_label}."
    else:
        message = f"Equipped {item_label}."
    if quest_bonus > 0:
        message += f" Quest bonus +{quest_bonus} coins."
    return True, message, quest_bonus

def get_accessory_status(category, key):
    owned_bucket = PLAYER_DATA.get("owned_accessories", {}).get(category, [ACCESSORY_DEFAULTS[category]])
    owned = key in owned_bucket
    selected = selected_accessories.get(category, ACCESSORY_DEFAULTS[category]) == key
    cost = ACCESSORY_COSTS[category].get(key, 0)

    if owned and selected:
        return "Equipped", NEON_GREEN
    if owned:
        return "Owned", (220, 235, 255)
    affordable = cheat_enabled("infinite_gold") or PLAYER_DATA["coins"] >= cost
    return f"{cost}c", NEON_GOLD if affordable else (255, 125, 125)

def buy_or_equip_accessory(category, key):
    used_infinite_gold = cheat_enabled("infinite_gold")
    owned_accessories = PLAYER_DATA.setdefault("owned_accessories", make_owned_accessories())
    owned_bucket = owned_accessories.setdefault(category, [ACCESSORY_DEFAULTS[category]])
    cost = ACCESSORY_COSTS[category].get(key, 0)
    item_suffix = {
        "hat": "hat",
        "neckwear": "neckwear",
        "face": "face gear",
        "wings": "wings",
        "eyes": "eyes",
    }
    item_label = f"{accessory_label(category, key)} {item_suffix.get(category, 'accessory')}"

    purchased = False
    if key not in owned_bucket:
        if not used_infinite_gold and PLAYER_DATA["coins"] < cost:
            missing = cost - PLAYER_DATA["coins"]
            return False, f"Need {missing} more coins for {item_label}.", 0
        if not used_infinite_gold:
            PLAYER_DATA["coins"] -= cost
            PLAYER_STATS["coins_spent"] += cost
            PLAYER_DATA["daily_stats"]["coins_spent"] += cost
        owned_bucket.append(key)
        PLAYER_STATS["items_bought"] += 1
        PLAYER_DATA["daily_stats"]["items_bought"] += 1
        purchased = True

    PLAYER_DATA["accessory_shop_unlocked"] = True
    selected_accessories[category] = key
    save_settings()
    rewards = complete_ready_quests()
    quest_bonus = sum(reward for _, reward, _ in rewards)
    save_stats()
    save_player_data()

    if purchased:
        if used_infinite_gold:
            message = f"Unlocked and equipped {item_label} with Infinite Gold."
        else:
            message = f"Bought and equipped {item_label}."
    else:
        message = f"Equipped {item_label}."
    if quest_bonus > 0:
        message += f" Quest bonus +{quest_bonus} coins."
    return True, message, quest_bonus

def unlock_accessory_shop():
    if PLAYER_DATA.get("accessory_shop_unlocked"):
        return True, "Accessories boutique is already open.", 0

    used_infinite_gold = cheat_enabled("infinite_gold")
    if not used_infinite_gold and PLAYER_DATA["coins"] < ACCESSORY_SHOP_UNLOCK_COST:
        missing = ACCESSORY_SHOP_UNLOCK_COST - PLAYER_DATA["coins"]
        return False, f"Need {missing} more coins to unlock Accessories.", 0

    if not used_infinite_gold:
        PLAYER_DATA["coins"] -= ACCESSORY_SHOP_UNLOCK_COST
        PLAYER_STATS["coins_spent"] += ACCESSORY_SHOP_UNLOCK_COST
        PLAYER_DATA["daily_stats"]["coins_spent"] += ACCESSORY_SHOP_UNLOCK_COST
    PLAYER_DATA["accessory_shop_unlocked"] = True
    PLAYER_STATS["items_bought"] += 1
    PLAYER_DATA["daily_stats"]["items_bought"] += 1

    save_settings()
    rewards = complete_ready_quests()
    quest_bonus = sum(reward for _, reward, _ in rewards)
    save_stats()
    save_player_data()

    if used_infinite_gold:
        message = "Unlocked the Accessories boutique with Infinite Gold."
    else:
        message = "Unlocked the Accessories boutique."
    if quest_bonus > 0:
        message += f" Quest bonus +{quest_bonus} coins."
    return True, message, quest_bonus

def draw_hud(surf, gs):
    # Score — large glowing number, no ring box
    score_str = str(gs.score)
    draw_glow_text(surf, score_str, BIG, WIDTH//2, 44, (255,255,255), (180,230,255), center=True, glow_r=5)
    live_coins = None if cheat_enabled("infinite_gold") else PLAYER_DATA.get("coins", 0) + gs.run_coins
    draw_coin_badge(surf, WIDTH - 8, 8, coins=live_coins, align_right=True)

    # Power-up bars
    y = 90
    for name, frames, col in [
        ("immunity",  gs.bird.immunity,    (50,220,80)),
        ("2x coins",  gs.bird.coin_boost,  NEON_GOLD),
        ("2x points", gs.bird.point_boost, (178, 96, 255)),
        ("slow_mo",   gs.bird.slow_motion, (255,80,80))
    ]:
        if frames <= 0:
            continue
        if name == "immunity" and cheat_enabled("infinite_immunity"):
            t_ratio = 1.0
            status_text = "immunity: DEV"
        else:
            t_ratio = clamp(frames / (POWERUP_DURATION_SEC * FPS), 0.0, 1.0)
            status_text = f"{name}: {sec_left(frames)}s"
        bw = 130
        draw_glass_panel(surf, 6, y-2, bw+20, 20, alpha=38)
        # Glow bar
        bar_surf = pygame.Surface((bw, 10), pygame.SRCALPHA)
        pygame.draw.rect(bar_surf, (*col,180), (0,0,int(bw*t_ratio),10), border_radius=4)
        pygame.draw.rect(bar_surf, (*col,80),  (0,0,bw,10), 1, border_radius=4)
        surf.blit(bar_surf, (14, y+2))
        lbl = TINY.render(status_text, True, (255,255,255))
        surf.blit(lbl, (14, y+1))
        y += 28

    cheat_labels = active_cheat_labels()
    if cheat_labels:
        cheat_text = TINY.render("DEV: " + "  |  ".join(cheat_labels), True, (255, 220, 180))
        draw_glass_panel(surf, 6, max(y, 90) - 2, cheat_text.get_width() + 18, 20, alpha=40, border_col=(255, 180, 120, 90), radius=10)
        surf.blit(cheat_text, (14, max(y, 90) + 1))

    update_draw_score_pops(surf)
    draw_persistence_alert(surf)
    draw_fps_overlay(surf)

def check_collision(bird, pipes, t):
    hit_points = bird.collision_points()
    for p in pipes:
        top_r, bot_r = p.rects()
        if bird.immunity <= 0 and any(top_r.collidepoint(px, py) or bot_r.collidepoint(px, py) for px, py in hit_points):
            return True
    _, min_y, _, max_y = bird.collision_bounds()
    if min_y < -10 or max_y > HEIGHT - GROUND_H:
        return True
    return False

def apply_camera_shake(gs):
    if not SETTINGS["screenshake"]:
        gs.shake_timer = 0.0
        return 0, 0
    if gs.shake_timer > 0:
        gs.shake_timer -= CLOCK.get_time() / 1000.0
        mag = CAMERA_SHAKE_MAG * (gs.shake_timer / SHAKE_DURATION)
        return int(random.uniform(-mag,mag)), int(random.uniform(-mag,mag))
    return 0, 0

# ----------------------------- Cinematic Main Menu ---------------------------
def draw_main_menu(gs, t, buttons, demo_bird, selected_button=0, quest_button=None, dev_button=None):
    # --- Background ---
    draw_background(SCREEN, t, mode=selected_bg)

    # --- Menu particle field (neon motes) ---
    if SETTINGS["particles"]:
        for mp in MENU_PARTICLES:
            mp.update(t)
            mp.draw(SCREEN, t)

    for c in sorted(gs.clouds, key=lambda c: c.layer):
        c.draw(SCREEN, t, selected_bg)

    draw_ground_cinematic(SCREEN, t)

    # --- Animated title ---
    title_str  = "FLAPPY"
    title2_str = "BIRD"
    # Wave each character
    for pass_i, (word, base_y, base_col, glow_col) in enumerate([
        (title_str,  68,  NEON_GOLD,  (160,100,0)),
        (title2_str, 120, NEON_CYAN,  (0, 110, 160)),
    ]):
        char_ws = [BIG.size(ch)[0] for ch in word]
        total_w = sum(char_ws)
        cx = WIDTH//2 - total_w//2
        for i, ch in enumerate(word):
            wave_y = int(math.sin(t*2.5 + i*0.5 + pass_i*1.2) * 5)
            hue_t  = math.sin(t*0.9 + i*0.35) * 0.5 + 0.5
            col    = lerp_color(base_col, (255,255,255), hue_t * 0.25)
            draw_glow_text(SCREEN, ch, BIG, cx, base_y + wave_y, col, glow_col,
                           center=False, glow_r=5)
            cx += char_ws[i]

    # --- Demo bird ---
    bird_cx = WIDTH//2
    bird_cy = 220

    # Orbiting mini-stars
    # Orbiting mini-stars removed (disabled per user request)

    # Demo bird
    demo_bird.x       = bird_cx - 24
    demo_bird.y       = int(bird_cy - 18 + math.sin(t * 2.0) * 8)
    demo_bird.anim_time  = int(t * 60)
    demo_bird.blink_timer= 60
    demo_bird.frame_count= 999
    demo_bird.draw(SCREEN)

    # --- Buttons ---
    if quest_button is not None:
        quest_button.draw(SCREEN, t)
        refresh_daily_quests()
        daily_done = len(PLAYER_DATA["claimed_daily"])
        quest_info_rect = pygame.Rect(12, 50, 112, 36)
        draw_glass_panel(SCREEN, quest_info_rect.x, quest_info_rect.y, quest_info_rect.w, quest_info_rect.h, alpha=46, border_col=(120, 255, 180, 90), radius=12)
        info_a = TINY.render("Daily Quests", True, (190, 255, 220))
        info_b = TINY.render(f"{daily_done}/5 done", True, (255, 255, 255))
        SCREEN.blit(info_a, (quest_info_rect.centerx - info_a.get_width() // 2, quest_info_rect.y + 6))
        SCREEN.blit(info_b, (quest_info_rect.centerx - info_b.get_width() // 2, quest_info_rect.y + 19))

    if dev_button is not None:
        dev_button.draw(SCREEN, t)
        cheat_labels = active_cheat_labels()
        dev_status = f"{len(cheat_labels)} active" if cheat_labels else "Code Required"
        status_surf = TINY.render(dev_status, True, (255, 230, 180))
        status_w = max(dev_button.rect.w, status_surf.get_width() + 20)
        status_x = max(12, min(WIDTH - 12 - status_w, dev_button.rect.centerx - status_w // 2))
        draw_glass_panel(
            SCREEN,
            status_x,
            dev_button.rect.y - 34,
            status_w,
            28,
            alpha=44,
            border_col=(255, 180, 120, 90),
            radius=12,
        )
        SCREEN.blit(status_surf, (status_x + (status_w - status_surf.get_width()) // 2, dev_button.rect.y - 26))

    draw_coin_badge(SCREEN, WIDTH - 8, 8, align_right=True)

    for i, b in enumerate(buttons):
        b.selected = (i == selected_button)
        b.draw(SCREEN, t)

    # Best score
    hs_data = load_json(HIGH_SCORES_FILE, {"normal": [], "extreme": []})
    if isinstance(hs_data, list):
        # Old format: convert to new format
        all_scores = hs_data
    else:
        # New format: dictionary
        all_scores = hs_data.get("normal", []) + hs_data.get("extreme", [])
    if all_scores:
        best = max(all_scores)
        pulse_col = lerp_color((255,210,60),(255,255,120), 0.5+0.5*math.sin(t*1.5))
        bt = SMALL.render(f"Best: {best}", True, pulse_col)
        SCREEN.blit(bt, (WIDTH//2 - bt.get_width()//2, HEIGHT-GROUND_H-62))

    # Hint text
    hint = TINY.render("↑↓ Navigate   ENTER Select   Quests top-left   Dev Tools bottom-left", True, (200,220,255))
    SCREEN.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT-GROUND_H-24))
    draw_persistence_alert(SCREEN, y=HEIGHT-GROUND_H-116)
    draw_fps_overlay(SCREEN)

# ----------------------------- Dev Tools Screen ------------------------------
def dev_tools_screen():
    PLAYER_DATA["dev_tools_unlocked"] = False
    run = True
    t0 = pygame.time.get_ticks()
    back_button = Button(20, 20, 60, 40, "<", accent_col=(255, 255, 255))
    code_input = ""
    message = "Enter the 4-digit developer code."
    message_color = (220, 235, 255)
    header_rect = pygame.Rect(16, 10, WIDTH - 32, 72)
    lock_rect = pygame.Rect(44, 108, WIDTH - 88, 128)
    code_box_w = 42
    code_box_h = 42
    code_box_gap = 14
    code_box_y = lock_rect.y + 74
    code_row_w = code_box_w * 4 + code_box_gap * 3
    code_row_x = WIDTH // 2 - code_row_w // 2
    digit_w = 78
    digit_h = 52
    digit_gap_x = 20
    digit_gap_y = 20
    keypad_top = lock_rect.bottom + 18
    keypad_row_w = digit_w * 3 + digit_gap_x * 2
    keypad_left = WIDTH // 2 - keypad_row_w // 2
    zero_y = keypad_top + (digit_h + digit_gap_y) * 3
    action_w = 104
    action_h = 42
    action_gap = 14
    action_row_w = action_w * 3 + action_gap * 2
    action_x = WIDTH // 2 - action_row_w // 2
    action_y = zero_y + digit_h + 18

    digit_buttons = []
    keypad = [
        ("1", keypad_left, keypad_top),
        ("2", keypad_left + digit_w + digit_gap_x, keypad_top),
        ("3", keypad_left + (digit_w + digit_gap_x) * 2, keypad_top),
        ("4", keypad_left, keypad_top + digit_h + digit_gap_y),
        ("5", keypad_left + digit_w + digit_gap_x, keypad_top + digit_h + digit_gap_y),
        ("6", keypad_left + (digit_w + digit_gap_x) * 2, keypad_top + digit_h + digit_gap_y),
        ("7", keypad_left, keypad_top + (digit_h + digit_gap_y) * 2),
        ("8", keypad_left + digit_w + digit_gap_x, keypad_top + (digit_h + digit_gap_y) * 2),
        ("9", keypad_left + (digit_w + digit_gap_x) * 2, keypad_top + (digit_h + digit_gap_y) * 2),
        ("0", WIDTH // 2 - digit_w // 2, zero_y),
    ]
    for label, x, y in keypad:
        digit_buttons.append((label, Button(x, y, digit_w, digit_h, label, accent_col=NEON_CYAN)))
    clear_button = Button(action_x, action_y, action_w, action_h, "Clear", accent_col=NEON_PINK)
    backspace_button = Button(action_x + action_w + action_gap, action_y, action_w, action_h, "Back", accent_col=(255, 170, 120))
    enter_button = Button(action_x + (action_w + action_gap) * 2, action_y, action_w, action_h, "Enter", accent_col=NEON_GREEN)

    def submit_code():
        nonlocal code_input, message, message_color
        if code_input == DEV_TOOLS_CODE:
            unlock_dev_tools()
            code_input = ""
            message = "Code accepted for this visit."
            message_color = (160, 255, 190)
        else:
            code_input = ""
            message = "Wrong code. Try 4 digits again."
            message_color = (255, 135, 135)

    while run:
        t = (pygame.time.get_ticks() - t0) / 1000.0
        unlocked = PLAYER_DATA.get("dev_tools_unlocked", False)
        draw_background(SCREEN, t, mode=selected_bg)
        draw_ground_cinematic(SCREEN, t)
        back_button.draw(SCREEN, t)
        draw_coin_badge(SCREEN, WIDTH - 8, 8, align_right=True)

        if not unlocked:
            draw_glass_panel(SCREEN, header_rect.x, header_rect.y, header_rect.w, header_rect.h, alpha=65)
            draw_glow_text(SCREEN, "Dev Tools", BIG, WIDTH//2, 48, (255,255,255), (255, 150, 80), glow_r=4)

            draw_glass_panel(SCREEN, lock_rect.x, lock_rect.y, lock_rect.w, lock_rect.h, alpha=56, border_col=(255, 180, 120, 90), radius=18)
            title = FONT.render("Access Locked", True, (255, 225, 180))
            body = SMALL.render("Type the 4-digit developer code to unlock the cheats menu.", True, (220, 230, 245))
            SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, lock_rect.y + 16))
            SCREEN.blit(body, (WIDTH//2 - body.get_width()//2, lock_rect.y + 46))

            for i in range(4):
                box_x = code_row_x + i * (code_box_w + code_box_gap)
                draw_glass_panel(SCREEN, box_x, code_box_y, code_box_w, code_box_h, alpha=62, border_col=(255, 255, 255, 90), radius=12)
                char = code_input[i] if i < len(code_input) else ""
                char_surf = MED.render(char, True, (255, 255, 255))
                SCREEN.blit(
                    char_surf,
                    (
                        box_x + code_box_w // 2 - char_surf.get_width() // 2,
                        code_box_y + code_box_h // 2 - char_surf.get_height() // 2,
                    ),
                )

            for _, button in digit_buttons:
                button.draw(SCREEN, t)
            clear_button.draw(SCREEN, t)
            backspace_button.draw(SCREEN, t)
            enter_button.draw(SCREEN, t)
        else:
            draw_glass_panel(SCREEN, header_rect.x, header_rect.y, header_rect.w, header_rect.h, alpha=65)
            draw_glow_text(SCREEN, "Developer Tools", BIG, WIDTH//2, 48, (255,255,255), (255, 150, 80), glow_r=4)

            summary = SMALL.render(
                "Unlocked for this visit - toggle cheats below",
                True,
                (255, 225, 180),
            )
            SCREEN.blit(summary, (WIDTH//2 - summary.get_width()//2, 92))

            row_rects = []
            row_y = 156
            for idx, cheat in enumerate(DEV_CHEAT_INFO):
                rect = pygame.Rect(28, row_y + idx * 102, WIDTH - 56, 84)
                row_rects.append((cheat["key"], rect))
                active = cheat_enabled(cheat["key"])
                accent = NEON_GREEN if active else NEON_PINK
                draw_glass_panel(SCREEN, rect.x, rect.y, rect.w, rect.h, alpha=58, border_col=(*accent, 110), radius=16)
                title = FONT.render(cheat["title"], True, (255, 255, 255))
                desc = SMALL.render(cheat["desc"], True, (215, 225, 240))
                status = MED.render("ON" if active else "OFF", True, accent)
                SCREEN.blit(title, (rect.x + 16, rect.y + 12))
                SCREEN.blit(desc, (rect.x + 16, rect.y + 42))
                SCREEN.blit(status, (rect.right - status.get_width() - 116, rect.y + 20))

                toggle_button = Button(rect.right - 96, rect.y + 18, 78, 40, "Toggle", accent_col=accent)
                toggle_button.draw(SCREEN, t)
                row_rects[-1] = (cheat["key"], rect, toggle_button)

            draw_glass_panel(SCREEN, 28, 380, WIDTH - 56, 92, alpha=48, border_col=(255, 190, 120, 90), radius=16)
            info_title = FONT.render("Cheat Notes", True, (255, 230, 180))
            info_a = SMALL.render("Infinite Gold keeps your coin badge at INF and removes shop costs.", True, (220, 230, 245))
            info_b = SMALL.render("Infinite Immunity keeps the immunity power-up active every frame.", True, (220, 230, 245))
            SCREEN.blit(info_title, (42, 394))
            SCREEN.blit(info_a, (42, 422))
            SCREEN.blit(info_b, (42, 446))

        draw_glass_panel(SCREEN, 20, HEIGHT-GROUND_H-58, WIDTH-40, 44, alpha=50)
        hint_text = message if not unlocked else "Click Toggle to turn cheats on or off. ESC returns to the menu."
        hint = SMALL.render(hint_text, True, message_color if not unlocked else BLACK)
        SCREEN.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT-GROUND_H-47))

        draw_vignette(SCREEN)
        draw_fps_overlay(SCREEN)
        pygame.display.update()
        CLOCK.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE or keybind_matches(ev, "hotkey_back"):
                    run = False
                elif not unlocked:
                    if pygame.K_0 <= ev.key <= pygame.K_9 and len(code_input) < 4:
                        code_input += pygame.key.name(ev.key)
                    elif pygame.K_KP0 <= ev.key <= pygame.K_KP9 and len(code_input) < 4:
                        code_input += pygame.key.name(ev.key).replace("[", "").replace("]", "")
                    elif ev.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        code_input = code_input[:-1]
                    elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        submit_code()
                else:
                    if ev.key == pygame.K_1:
                        toggle_dev_cheat("infinite_gold")
                    elif ev.key == pygame.K_2:
                        toggle_dev_cheat("infinite_immunity")
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if back_button.is_clicked((mx, my)):
                    run = False
                    continue
                if not unlocked:
                    for label, button in digit_buttons:
                        if button.is_clicked((mx, my)) and len(code_input) < 4:
                            code_input += label
                            break
                    if clear_button.is_clicked((mx, my)):
                        code_input = ""
                    elif backspace_button.is_clicked((mx, my)):
                        code_input = code_input[:-1]
                    elif enter_button.is_clicked((mx, my)):
                        submit_code()
                else:
                    for cheat_key, _, toggle_button in row_rects:
                        if toggle_button.is_clicked((mx, my)):
                            state = toggle_dev_cheat(cheat_key)
                            message = f"{next(item['title'] for item in DEV_CHEAT_INFO if item['key'] == cheat_key)} {'enabled' if state else 'disabled'}."
                            message_color = (160, 255, 190) if state else (255, 200, 160)
                            break
    PLAYER_DATA["dev_tools_unlocked"] = False

# ----------------------------- Quest Screen ----------------------------------
def quests_screen():
    run = True
    t0 = pygame.time.get_ticks()
    back_button = Button(20, 20, 60, 40, "<", accent_col=(255, 255, 255))
    selected_tab = "quests"
    selected_indices = {"quests": 0, "daily": 0}
    scroll_offsets = {"quests": 0, "daily": 0}
    tab_buttons = {
        "quests": Button(36, 92, 194, 42, "Quest List", accent_col=NEON_GREEN),
        "daily": Button(250, 92, 194, 42, "Daily Quests", accent_col=NEON_GOLD),
    }

    def current_quests():
        return QUEST_DEFINITIONS if selected_tab == "quests" else get_active_daily_quests()

    while run:
        refresh_daily_quests()
        t = (pygame.time.get_ticks() - t0) / 1000.0
        draw_background(SCREEN, t, mode=selected_bg)
        draw_ground_cinematic(SCREEN, t)
        back_button.draw(SCREEN, t)

        draw_glass_panel(SCREEN, 16, 10, WIDTH - 32, 72, alpha=65)
        draw_glow_text(SCREEN, "Quests", BIG, WIDTH//2, 48, (255,255,255), (80, 255, 160), glow_r=4)
        draw_coin_badge(SCREEN, WIDTH - 8, 8, align_right=True)

        for tab_name, tab_button in tab_buttons.items():
            tab_button.selected = (tab_name == selected_tab)
            tab_button.draw(SCREEN, t)

        quests = current_quests()
        if quests:
            selected_indices[selected_tab] = clamp(selected_indices[selected_tab], 0, len(quests) - 1)
        else:
            selected_indices[selected_tab] = 0
            scroll_offsets[selected_tab] = 0
        current_idx = selected_indices[selected_tab]
        if current_idx < scroll_offsets[selected_tab]:
            scroll_offsets[selected_tab] = current_idx

        if selected_tab == "daily":
            timer_text = SMALL.render(
                f"Refreshes in {format_countdown(seconds_until_daily_refresh())}",
                True,
                (255, 240, 160),
            )
            SCREEN.blit(timer_text, (WIDTH//2 - timer_text.get_width()//2, 140))

        row_rects = []
        row_y = 172 if selected_tab == "daily" else 146
        row_h = 74
        row_gap = 10
        content_bottom = HEIGHT - GROUND_H - 70
        visible_rows = max(1, (content_bottom - row_y + row_gap) // (row_h + row_gap))
        if current_idx >= scroll_offsets[selected_tab] + visible_rows:
            scroll_offsets[selected_tab] = current_idx - visible_rows + 1
        shown_quests = quests[scroll_offsets[selected_tab]:scroll_offsets[selected_tab] + visible_rows]
        completed_bucket = "claimed_daily" if selected_tab == "daily" else "claimed_quests"
        for row_idx, quest in enumerate(shown_quests):
            absolute_idx = scroll_offsets[selected_tab] + row_idx
            rect = pygame.Rect(28, row_y + row_idx * (row_h + row_gap), WIDTH - 56, row_h)
            row_rects.append((absolute_idx, rect))
            completed = quest["id"] in PLAYER_DATA[completed_bucket]
            accent = NEON_GREEN if completed else (255, 220, 120) if selected_tab == "daily" else NEON_CYAN

            draw_glass_panel(SCREEN, rect.x, rect.y, rect.w, rect.h, alpha=60 if absolute_idx == current_idx else 34)
            if absolute_idx == current_idx:
                pygame.draw.rect(SCREEN, accent, rect, 2, border_radius=14)

            title = FONT.render(quest["title"], True, (255, 255, 255))
            desc = SMALL.render(quest["desc"], True, (205, 220, 240))
            reward = MED.render(f"+{quest['reward']}", True, accent)
            status = "Completed" if completed else format_quest_progress(quest, daily=(selected_tab == "daily"))
            status_surf = SMALL.render(status, True, accent if completed else (235, 240, 255))

            SCREEN.blit(title, (rect.x + 14, rect.y + 10))
            SCREEN.blit(desc, (rect.x + 14, rect.y + 34))
            SCREEN.blit(reward, (rect.right - reward.get_width() - 14, rect.y + 8))
            SCREEN.blit(status_surf, (rect.right - status_surf.get_width() - 14, rect.y + 40))

            bar_x = rect.x + 14
            bar_y = rect.bottom - 14
            bar_w = rect.w - 28
            pygame.draw.rect(SCREEN, (255,255,255), (bar_x, bar_y, bar_w, 8), 1, border_radius=5)
            fill_w = int(bar_w * (1.0 if completed else progress_ratio(quest, selected_tab == "daily")))
            if fill_w > 0:
                pygame.draw.rect(SCREEN, accent, (bar_x, bar_y, fill_w, 8), border_radius=5)

        draw_glass_panel(SCREEN, 20, HEIGHT-GROUND_H-58, WIDTH-40, 44, alpha=50)
        hint = SMALL.render("TAB or ← → switch tabs  |  ↑ ↓ browse  |  mouse wheel scroll  |  ESC back", True, BLACK)
        SCREEN.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT-GROUND_H-47))

        draw_vignette(SCREEN)
        draw_fps_overlay(SCREEN)
        pygame.display.update()
        CLOCK.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE or keybind_matches(ev, "hotkey_back"):
                    run = False
                elif ev.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT):
                    selected_tab = "daily" if selected_tab == "quests" else "quests"
                elif ev.key == pygame.K_UP and quests:
                    selected_indices[selected_tab] = (current_idx - 1) % len(quests)
                elif ev.key == pygame.K_DOWN and quests:
                    selected_indices[selected_tab] = (current_idx + 1) % len(quests)
            if ev.type == pygame.MOUSEWHEEL and quests:
                selected_indices[selected_tab] = clamp(current_idx - ev.y, 0, len(quests) - 1)
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if back_button.is_clicked((mx, my)):
                    run = False
                for tab_name, tab_button in tab_buttons.items():
                    if tab_button.is_clicked((mx, my)):
                        selected_tab = tab_name
                        break
                for absolute_idx, rect in row_rects:
                    if rect.collidepoint(mx, my):
                        selected_indices[selected_tab] = absolute_idx
                        break

# ----------------------------- Cosmetics Screen ------------------------------
def cosmetics_room():
    global selected_bird_key, selected_bg, selected_trail_key
    run = True
    t0 = pygame.time.get_ticks()
    back_button = Button(20, 20, 60, 40, "<", accent_col=(255, 255, 255))
    preview_birds = {key: Bird(key, trail_key=selected_trail_key) for key in BIRD_KEYS}
    message = "Click a card to buy it or equip it."
    message_color = (220, 235, 255)
    message_until = 0

    def set_message(text, color):
        nonlocal message, message_color, message_until
        message = text
        message_color = color
        message_until = pygame.time.get_ticks() + 2800

    while run:
        t = (pygame.time.get_ticks() - t0) / 1000.0
        draw_background(SCREEN, t, mode=selected_bg)
        draw_ground_cinematic(SCREEN, t)
        back_button.draw(SCREEN, t)

        draw_glass_panel(SCREEN, 16, 10, WIDTH - 32, 72, alpha=65)
        draw_glow_text(SCREEN, "Cosmetics Shop", BIG, WIDTH//2, 48, (255,230,80), (180,140,0), glow_r=4)
        draw_coin_badge(SCREEN, WIDTH - 8, 8, align_right=True)

        bird_rects = []
        bg_rects = []
        trail_rects = []
        accessory_rect = pygame.Rect(30, 544, WIDTH - 60, 42)

        bird_lbl = FONT.render("Bird Skins", True, (255,255,255))
        SCREEN.blit(bird_lbl, (28, 96))
        bird_card_w = 92
        bird_card_h = 88
        bird_gap = 10
        bird_row_w = len(BIRD_KEYS) * bird_card_w + (len(BIRD_KEYS) - 1) * bird_gap
        bird_start_x = WIDTH // 2 - bird_row_w // 2
        for i, key in enumerate(BIRD_KEYS):
            rx = bird_start_x + i * (bird_card_w + bird_gap)
            ry = 122 + int(math.sin(t * 2 + i) * 4)
            rect = pygame.Rect(rx, ry, bird_card_w, bird_card_h)
            bird_rects.append((key, rect))
            draw_glass_panel(SCREEN, rect.x, rect.y, rect.w, rect.h, alpha=60 if key == selected_bird_key else 30)
            if key == selected_bird_key:
                pygame.draw.rect(SCREEN, (255,220,60), rect, 3, border_radius=14)
            if key not in PLAYER_DATA["owned_birds"]:
                lock_overlay = pygame.Surface((rect.w-4, rect.h-4), pygame.SRCALPHA)
                lock_overlay.fill((5, 10, 24, 74))
                SCREEN.blit(lock_overlay, (rect.x+2, rect.y+2))

            preview_bird = preview_birds[key]
            preview_bird.trail_key = selected_trail_key
            preview_bird.trail_color = resolve_trail_color(preview_bird.trail_key, preview_bird.color)
            preview_bird.set_accessories()
            preview_bird.x = rect.x + 22
            preview_bird.y = rect.y + 16
            preview_bird.anim_time = int(t * 60 + i * 30)
            preview_bird.blink_timer = 60
            preview_bird.frame_count = 999
            preview_bird.trail.clear()
            anchor_x, anchor_y = preview_bird.trail_anchor()
            for _ in range(4):
                preview_bird.trail.append((anchor_x, anchor_y))
            preview_bird.draw(SCREEN)

            name_text = TINY.render(key.capitalize(), True, (255,255,255))
            status_text, status_color = get_item_status("bird", key)
            status_surf = TINY.render(status_text, True, status_color)
            SCREEN.blit(name_text, (rect.centerx - name_text.get_width()//2, rect.y + 58))
            SCREEN.blit(status_surf, (rect.centerx - status_surf.get_width()//2, rect.y + 72))

        bg_lbl = FONT.render("Background Themes", True, (255,255,255))
        SCREEN.blit(bg_lbl, (28, 232))
        for bi, bname in enumerate(BG_OPTIONS):
            rect = pygame.Rect(30 + bi * 220, 260, 200, 140)
            bg_rects.append((bname, rect))
            draw_glass_panel(SCREEN, rect.x, rect.y, rect.w, rect.h, alpha=60 if bname == selected_bg else 30)
            if bname == selected_bg:
                pygame.draw.rect(SCREEN, (255,220,60), rect, 3, border_radius=14)
            SCREEN.blit(get_bg_preview_surface(bname), (rect.x + 2, rect.y + 2))
            if bname not in PLAYER_DATA["owned_backgrounds"]:
                lock_overlay = pygame.Surface((rect.w-4, rect.h-4), pygame.SRCALPHA)
                lock_overlay.fill((6, 10, 24, 84))
                SCREEN.blit(lock_overlay, (rect.x+2, rect.y+2))
            name_text = SMALL.render(bname.capitalize(), True, (255,255,255))
            status_text, status_color = get_item_status("background", bname)
            status_surf = SMALL.render(status_text, True, status_color)
            SCREEN.blit(name_text, (rect.centerx - name_text.get_width()//2, rect.y + 108))
            SCREEN.blit(status_surf, (rect.centerx - status_surf.get_width()//2, rect.y + 122))

        trail_lbl = FONT.render("Trail Colors", True, (255,255,255))
        SCREEN.blit(trail_lbl, (28, 426))
        trail_card_w = 56
        trail_card_h = 82
        trail_gap = 8
        trail_y = 454
        trail_row_w = len(TRAIL_OPTIONS) * trail_card_w + (len(TRAIL_OPTIONS) - 1) * trail_gap
        trail_start_x = WIDTH // 2 - trail_row_w // 2
        for ti, (trail_key, trail_label, trail_color) in enumerate(TRAIL_OPTIONS):
            tx = trail_start_x + ti * (trail_card_w + trail_gap)
            rect = pygame.Rect(tx, trail_y, trail_card_w, trail_card_h)
            trail_rects.append((trail_key, rect))
            draw_glass_panel(SCREEN, rect.x, rect.y, rect.w, rect.h, alpha=60 if trail_key == selected_trail_key else 30)
            if trail_key == selected_trail_key:
                pygame.draw.rect(SCREEN, (255,220,60), rect, 3, border_radius=14)
            if trail_key not in PLAYER_DATA["owned_trails"]:
                lock_overlay = pygame.Surface((rect.w-4, rect.h-4), pygame.SRCALPHA)
                lock_overlay.fill((6, 10, 24, 84))
                SCREEN.blit(lock_overlay, (rect.x+2, rect.y+2))

            preview_col = resolve_trail_color(trail_key, BIRD_COLORS.get(selected_bird_key, (245, 200, 60)))
            center_x = rect.centerx
            if preview_col is not None:
                for step in range(4):
                    frac = step / 3.0
                    radius = max(2, int(3 + frac * 4))
                    alpha = 70 + int(frac * 110)
                    dot = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(dot, (*preview_col, alpha), (radius, radius), radius)
                    SCREEN.blit(dot, (center_x - radius - 12 + step * 8, rect.y + 18 - radius + int(math.sin(t * 3 + ti + step) * 2)))
            else:
                draw_glow_text(SCREEN, "×", BIG, center_x, rect.y + 26, (180, 180, 180), (100, 100, 100), center=True, glow_r=2)

            trail_name = TINY.render(trail_label, True, (255,255,255))
            status_text, status_color = get_item_status("trail", trail_key)
            status_surf = TINY.render(status_text, True, status_color)
            SCREEN.blit(trail_name, (rect.centerx - trail_name.get_width()//2, rect.y + 52))
            SCREEN.blit(status_surf, (rect.centerx - status_surf.get_width()//2, rect.y + 66))

        accessories_open = PLAYER_DATA.get("accessory_shop_unlocked", False)
        accessory_border = (120, 255, 210, 120) if accessories_open else (255, 210, 110, 120)
        draw_glass_panel(SCREEN, accessory_rect.x, accessory_rect.y, accessory_rect.w, accessory_rect.h, alpha=56, border_col=accessory_border, radius=14)
        accessory_title = FONT.render("Accessories", True, (255, 255, 255))
        if accessories_open:
            accessory_desc = SMALL.render("Open hats, scarves, face gear, wings, and eye colors.", True, (205, 230, 245))
            accessory_status = SMALL.render("Open Shop", True, (120, 255, 190))
        else:
            accessory_desc = SMALL.render(f"Unlock the boutique for {ACCESSORY_SHOP_UNLOCK_COST} coins.", True, (255, 232, 180))
            accessory_status = SMALL.render(f"{ACCESSORY_SHOP_UNLOCK_COST}c", True, NEON_GOLD if cheat_enabled("infinite_gold") or PLAYER_DATA["coins"] >= ACCESSORY_SHOP_UNLOCK_COST else (255, 125, 125))
        SCREEN.blit(accessory_title, (accessory_rect.x + 14, accessory_rect.y + 4))
        SCREEN.blit(accessory_desc, (accessory_rect.x + 14, accessory_rect.y + 22))
        SCREEN.blit(accessory_status, (accessory_rect.right - accessory_status.get_width() - 14, accessory_rect.centery - accessory_status.get_height() // 2))

        draw_glass_panel(SCREEN, 20, HEIGHT-GROUND_H-58, WIDTH-40, 44, alpha=50)
        active_text = message if pygame.time.get_ticks() <= message_until else "Click a card to buy or equip it. ESC returns to the menu."
        active_color = message_color if pygame.time.get_ticks() <= message_until else BLACK
        hint = SMALL.render(active_text, True, active_color)
        SCREEN.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT-GROUND_H-47))

        draw_vignette(SCREEN)
        draw_fps_overlay(SCREEN)
        pygame.display.update()
        CLOCK.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE or keybind_matches(ev, "hotkey_back"):
                    run = False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if back_button.is_clicked((mx, my)):
                    run = False
                    continue
                if accessory_rect.collidepoint(mx, my):
                    if PLAYER_DATA.get("accessory_shop_unlocked", False):
                        accessories_room()
                    else:
                        ok, text, _ = unlock_accessory_shop()
                        set_message(text, NEON_GREEN if ok else (255, 125, 125))
                        if ok:
                            accessories_room()
                    continue
                handled = False
                for key, rect in bird_rects:
                    if rect.collidepoint(mx, my):
                        ok, text, _ = buy_or_equip_item("bird", key)
                        set_message(text, NEON_GREEN if ok else (255, 125, 125))
                        handled = True
                        break
                if handled:
                    continue
                for key, rect in bg_rects:
                    if rect.collidepoint(mx, my):
                        ok, text, _ = buy_or_equip_item("background", key)
                        set_message(text, NEON_GREEN if ok else (255, 125, 125))
                        handled = True
                        break
                if handled:
                    continue
                for key, rect in trail_rects:
                    if rect.collidepoint(mx, my):
                        ok, text, _ = buy_or_equip_item("trail", key)
                        set_message(text, NEON_GREEN if ok else (255, 125, 125))
                        break

def accessories_room():
    run = True
    t0 = pygame.time.get_ticks()
    back_button = Button(20, 20, 60, 40, "<", accent_col=(255, 255, 255))
    selected_category = ACCESSORY_CATEGORY_ORDER[0]
    tab_buttons = {}
    tab_w = 78
    tab_gap = 8
    tab_row_w = len(ACCESSORY_CATEGORY_ORDER) * tab_w + (len(ACCESSORY_CATEGORY_ORDER) - 1) * tab_gap
    tab_start_x = WIDTH // 2 - tab_row_w // 2
    for index, category in enumerate(ACCESSORY_CATEGORY_ORDER):
        tab_buttons[category] = Button(
            tab_start_x + index * (tab_w + tab_gap),
            228,
            tab_w,
            38,
            ACCESSORY_TAB_LABELS[category],
            accent_col=ACCESSORY_CATEGORY_ACCENTS[category],
        )

    message = "Pick a category, then buy or equip a look."
    message_color = (220, 235, 255)
    message_until = 0

    def set_message(text, color):
        nonlocal message, message_color, message_until
        message = text
        message_color = color
        message_until = pygame.time.get_ticks() + 2800

    while run:
        t = (pygame.time.get_ticks() - t0) / 1000.0
        accent = ACCESSORY_CATEGORY_ACCENTS[selected_category]
        draw_background(SCREEN, t, mode=selected_bg)
        draw_ground_cinematic(SCREEN, t)
        back_button.draw(SCREEN, t)

        draw_glass_panel(SCREEN, 16, 10, WIDTH - 32, 72, alpha=65)
        draw_glow_text(SCREEN, "Accessories", BIG, WIDTH//2, 48, (255,255,255), accent, glow_r=4)
        draw_coin_badge(SCREEN, WIDTH - 8, 8, align_right=True)

        preview_rect = pygame.Rect(28, 96, WIDTH - 56, 112)
        draw_glass_panel(SCREEN, preview_rect.x, preview_rect.y, preview_rect.w, preview_rect.h, alpha=58, border_col=(*accent, 110), radius=18)
        preview_bird = Bird(selected_bird_key, trail_key="none", accessories=current_accessory_selection())
        preview_bird.x = preview_rect.x + 46
        preview_bird.y = preview_rect.y + 34
        preview_bird.anim_time = int(t * 60)
        preview_bird.blink_timer = 60
        preview_bird.frame_count = 999
        preview_bird.draw(SCREEN)

        preview_title = FONT.render("Boutique Preview", True, (255, 255, 255))
        preview_body = SMALL.render(f"Current {ACCESSORY_CATEGORY_LABELS[selected_category].lower()}: {accessory_label(selected_category, selected_accessories[selected_category])}", True, (215, 228, 245))
        preview_body2 = SMALL.render("Accessories apply to menu, gameplay, and previews instantly.", True, (190, 210, 230))
        SCREEN.blit(preview_title, (preview_rect.x + 118, preview_rect.y + 18))
        SCREEN.blit(preview_body, (preview_rect.x + 118, preview_rect.y + 48))
        SCREEN.blit(preview_body2, (preview_rect.x + 118, preview_rect.y + 71))

        for category, button in tab_buttons.items():
            button.selected = (category == selected_category)
            button.draw(SCREEN, t)

        item_rects = []
        items = ACCESSORY_OPTIONS[selected_category]
        card_w = 128
        card_h = 132
        card_gap = 10
        row_gap = 12
        cards_row_w = card_w * 3 + card_gap * 2
        card_start_x = WIDTH // 2 - cards_row_w // 2
        card_start_y = 286
        for index, item in enumerate(items):
            col = index % 3
            row = index // 3
            rect = pygame.Rect(card_start_x + col * (card_w + card_gap), card_start_y + row * (card_h + row_gap), card_w, card_h)
            item_rects.append((item["id"], rect))
            equipped = selected_accessories.get(selected_category, ACCESSORY_DEFAULTS[selected_category]) == item["id"]
            draw_glass_panel(SCREEN, rect.x, rect.y, rect.w, rect.h, alpha=60 if equipped else 32, border_col=(*accent, 110) if equipped else (255, 255, 255, 80), radius=16)
            if item["id"] not in PLAYER_DATA["owned_accessories"][selected_category]:
                lock_overlay = pygame.Surface((rect.w - 4, rect.h - 4), pygame.SRCALPHA)
                lock_overlay.fill((6, 10, 24, 84))
                SCREEN.blit(lock_overlay, (rect.x + 2, rect.y + 2))

            preview_accessories = current_accessory_selection()
            preview_accessories[selected_category] = item["id"]
            card_bird = Bird(selected_bird_key, trail_key="none", accessories=preview_accessories)
            card_bird.x = rect.x + 33
            card_bird.y = rect.y + 24
            card_bird.anim_time = int(t * 60 + index * 18)
            card_bird.blink_timer = 60
            card_bird.frame_count = 999
            card_bird.draw(SCREEN)

            name_text = TINY.render(item["label"], True, (255, 255, 255))
            status_text, status_color = get_accessory_status(selected_category, item["id"])
            status_surf = TINY.render(status_text, True, status_color)
            SCREEN.blit(name_text, (rect.centerx - name_text.get_width() // 2, rect.y + 96))
            SCREEN.blit(status_surf, (rect.centerx - status_surf.get_width() // 2, rect.y + 112))

        draw_glass_panel(SCREEN, 20, HEIGHT-GROUND_H-58, WIDTH-40, 44, alpha=50)
        active_text = message if pygame.time.get_ticks() <= message_until else "Click a tab or card. ESC returns to the cosmetics shop."
        active_color = message_color if pygame.time.get_ticks() <= message_until else BLACK
        hint = SMALL.render(active_text, True, active_color)
        SCREEN.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT-GROUND_H-47))

        draw_vignette(SCREEN)
        draw_fps_overlay(SCREEN)
        pygame.display.update()
        CLOCK.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE or keybind_matches(ev, "hotkey_back"):
                    run = False
                elif ev.key == pygame.K_LEFT:
                    idx = (ACCESSORY_CATEGORY_ORDER.index(selected_category) - 1) % len(ACCESSORY_CATEGORY_ORDER)
                    selected_category = ACCESSORY_CATEGORY_ORDER[idx]
                elif ev.key == pygame.K_RIGHT or ev.key == pygame.K_TAB:
                    idx = (ACCESSORY_CATEGORY_ORDER.index(selected_category) + 1) % len(ACCESSORY_CATEGORY_ORDER)
                    selected_category = ACCESSORY_CATEGORY_ORDER[idx]
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if back_button.is_clicked((mx, my)):
                    run = False
                    continue
                tab_clicked = False
                for category, button in tab_buttons.items():
                    if button.is_clicked((mx, my)):
                        selected_category = category
                        tab_clicked = True
                        break
                if tab_clicked:
                    continue
                for item_id, rect in item_rects:
                    if rect.collidepoint(mx, my):
                        ok, text, _ = buy_or_equip_accessory(selected_category, item_id)
                        set_message(text, NEON_GREEN if ok else (255, 125, 125))
                        break

def settings_room():
    run = True
    selected_tab = "sound_visuals"
    selected_indices = {"sound_visuals": 0, "hotkeys": 0}
    binding_action = None
    t0 = pygame.time.get_ticks()
    back_button = Button(20, 20, 60, 40, "<", accent_col=(255, 255, 255))
    tab_rows = {
        "sound_visuals": [
            {"key": "music", "label": "Music", "type": "bool", "accent": NEON_GOLD},
            {"key": "music_volume", "label": "Music Volume", "type": "volume", "accent": NEON_GOLD},
            {"key": "sfx", "label": "SFX", "type": "bool", "accent": NEON_CYAN},
            {"key": "sfx_volume", "label": "SFX Volume", "type": "volume", "accent": NEON_CYAN},
            {"key": "screenshake", "label": "Screen Shake", "type": "bool", "accent": NEON_PINK},
            {"key": "particles", "label": "Particles", "type": "bool", "accent": NEON_GREEN},
            {"key": "vignette", "label": "Vignette", "type": "bool", "accent": (220, 200, 255)},
            {"key": "show_fps", "label": "Show FPS", "type": "bool", "accent": (255, 255, 255)},
        ],
        "hotkeys": [
            {"key": "hotkey_flap", "label": "Flap Hotkey", "type": "key", "accent": (255, 215, 110)},
            {"key": "hotkey_cosmetics", "label": "Cosmetics Hotkey", "type": "key", "accent": (180, 120, 255)},
            {"key": "hotkey_settings", "label": "Settings Hotkey", "type": "key", "accent": NEON_CYAN},
            {"key": "hotkey_high_scores", "label": "High Scores Hotkey", "type": "key", "accent": NEON_GOLD},
            {"key": "hotkey_stats", "label": "Stats Hotkey", "type": "key", "accent": (170, 240, 255)},
            {"key": "hotkey_extreme", "label": "Extreme Mode Hotkey", "type": "key", "accent": (255, 110, 110)},
            {"key": "hotkey_back", "label": "Back / Leave Hotkey", "type": "key", "accent": (255, 150, 150)},
        ],
    }
    tab_order = ["sound_visuals", "hotkeys"]
    tab_buttons = {
        "sound_visuals": Button(36, 92, 194, 42, "Sound / Visuals", accent_col=NEON_CYAN),
        "hotkeys": Button(250, 92, 194, 42, "Hotkeys", accent_col=(255, 150, 150)),
    }

    def get_rows():
        return tab_rows[selected_tab]

    def switch_tab(tab_name):
        nonlocal selected_tab, binding_action
        selected_tab = tab_name
        binding_action = None

    def format_value(row):
        value = SETTINGS[row["key"]]
        if row["type"] == "volume":
            return f"{int(round(value * 100))}%"
        if row["type"] == "key":
            return "PRESS A KEY..." if binding_action == row["key"] else get_keybind_label(row["key"])
        return "On" if value else "Off"

    def change_setting(row, direction):
        key = row["key"]
        if row["type"] == "bool":
            SETTINGS[key] = not SETTINGS[key]
            if key == "particles" and not SETTINGS[key]:
                particles.clear()
        else:
            SETTINGS[key] = clamp(round(SETTINGS[key] + direction * 0.1, 2), 0.0, 1.0)
        apply_audio_settings()
        save_settings()

    while run:
        t = (pygame.time.get_ticks() - t0) / 1000.0
        rows = get_rows()
        current_idx = min(selected_indices[selected_tab], len(rows) - 1)
        selected_indices[selected_tab] = current_idx
        draw_background(SCREEN, t, mode=selected_bg)
        draw_ground_cinematic(SCREEN, t)
        back_button.draw(SCREEN, t)

        draw_glass_panel(SCREEN, 16, 10, WIDTH - 32, 72, alpha=65)
        draw_glow_text(SCREEN, "Settings", BIG, WIDTH//2, 48, (255,255,255), (90,180,255), glow_r=4)

        for tab_name in tab_order:
            tab_button = tab_buttons[tab_name]
            tab_button.selected = (tab_name == selected_tab)
            tab_button.draw(SCREEN, t)

        row_rects = []
        row_y = 154
        row_gap = 52
        row_h = 42
        for i, row in enumerate(rows):
            y = row_y + i * row_gap
            rect = pygame.Rect(34, y, WIDTH - 68, row_h)
            row_rects.append(rect)
            draw_glass_panel(SCREEN, rect.x, rect.y, rect.w, rect.h,
                             alpha=60 if i == current_idx else 34)
            if i == current_idx:
                pygame.draw.rect(SCREEN, row["accent"], rect, 2, border_radius=14)

            label = FONT.render(row["label"], True, (235, 240, 255))
            value = MED.render(format_value(row), True, row["accent"])
            SCREEN.blit(label, (rect.x + 14, rect.y + 6))
            SCREEN.blit(value, (rect.right - value.get_width() - 14, rect.y + 18))

            if row["type"] == "volume":
                bar_w = 150
                bar_x = rect.right - bar_w - 110
                bar_y = rect.y + 15
                fill_w = int(bar_w * SETTINGS[row["key"]])
                pygame.draw.rect(SCREEN, (255,255,255), (bar_x, bar_y, bar_w, 10), 1, border_radius=5)
                if fill_w > 0:
                    pygame.draw.rect(SCREEN, row["accent"], (bar_x, bar_y, fill_w, 10), border_radius=5)

        draw_glass_panel(SCREEN, 20, HEIGHT-GROUND_H-58, WIDTH-40, 44, alpha=50)
        if binding_action:
            hint_text = "Press the key you want to use now"
        elif selected_tab == "hotkeys":
            hint_text = "TAB switch section  |  ↑ ↓ select  |  ENTER rebind  |  ESC back"
        else:
            hint_text = "TAB switch section  |  ↑ ↓ select  |  ← → change  |  ENTER toggle"
        hint = SMALL.render(hint_text, True, BLACK)
        SCREEN.blit(hint, (WIDTH//2-hint.get_width()//2, HEIGHT-GROUND_H-47))

        draw_vignette(SCREEN)
        draw_fps_overlay(SCREEN)
        pygame.display.update()
        CLOCK.tick(FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if binding_action:
                if ev.type == pygame.KEYDOWN:
                    SETTINGS[binding_action] = pygame.key.name(ev.key).lower()
                    save_settings()
                    binding_action = None
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    binding_action = None
                continue
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE or keybind_matches(ev, "hotkey_back"):
                    run = False
                elif ev.key == pygame.K_TAB:
                    tab_idx = (tab_order.index(selected_tab) + 1) % len(tab_order)
                    switch_tab(tab_order[tab_idx])
                elif ev.key == pygame.K_UP:
                    selected_indices[selected_tab] = (current_idx - 1) % len(rows)
                elif ev.key == pygame.K_DOWN:
                    selected_indices[selected_tab] = (current_idx + 1) % len(rows)
                elif ev.key == pygame.K_LEFT:
                    if rows[current_idx]["type"] == "volume":
                        change_setting(rows[current_idx], -1)
                elif ev.key == pygame.K_RIGHT:
                    if rows[current_idx]["type"] == "volume":
                        change_setting(rows[current_idx], 1)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if rows[current_idx]["type"] == "key":
                        binding_action = rows[current_idx]["key"]
                    else:
                        change_setting(rows[current_idx], 1)
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if back_button.is_clicked((mx, my)):
                    run = False
                for tab_name in tab_order:
                    if tab_buttons[tab_name].is_clicked((mx, my)):
                        switch_tab(tab_name)
                        break
                for i, rect in enumerate(row_rects):
                    if rect.collidepoint(mx, my):
                        selected_indices[selected_tab] = i
                        if rows[i]["type"] == "key":
                            binding_action = rows[i]["key"]
                        else:
                            direction = -1 if mx < rect.centerx and rows[i]["type"] == "volume" else 1
                            change_setting(rows[i], direction)
                        break

def high_scores_screen():
    run=True; t0=pygame.time.get_ticks()
    back_button = Button(20, 20, 60, 40, "<", accent_col=(255, 255, 255))
    while run:
        t=(pygame.time.get_ticks()-t0)/1000.0
        draw_background(SCREEN,t,mode=selected_bg)
        draw_ground_cinematic(SCREEN,t)
        
        # Draw back button
        back_button.draw(SCREEN, t)
        
        draw_glass_panel(SCREEN,16,10,WIDTH-32,72,alpha=65)
        draw_glow_text(SCREEN,"High Scores",BIG,WIDTH//2,50,(255,220,80),(180,120,0),glow_r=4)
        hs_data=load_json(HIGH_SCORES_FILE,{"normal": [], "extreme": []})
        if isinstance(hs_data, list):
            # Old format: treat as normal mode scores
            normal_scores = hs_data
            extreme_scores = []
        else:
            # New format: dictionary
            normal_scores = hs_data.get("normal", [])
            extreme_scores = hs_data.get("extreme", [])
        medal_cols=[(255,215,80),(220,220,220),(205,127,50),(255,255,255)]
        
        # Normal Mode Scores (left side)
        draw_glass_panel(SCREEN,WIDTH//4-100,130,200,40,alpha=55)
        draw_glow_text(SCREEN,"Normal",MED,WIDTH//4,150,(255,255,255),(100,150,255),glow_r=2)
        for i,s in enumerate(normal_scores[:8]):
            y2=180+i*32
            draw_glass_panel(SCREEN,WIDTH//4-80,y2-2,160,24,alpha=35)
            col=medal_cols[min(i,3)]
            row=FONT.render(f"#{i+1} {s}",True,col)
            SCREEN.blit(row,(WIDTH//4-row.get_width()//2,y2+4))
        
        # Extreme Mode Scores (right side)
        draw_glass_panel(SCREEN,3*WIDTH//4-100,130,200,40,alpha=55)
        draw_glow_text(SCREEN,"Extreme",MED,3*WIDTH//4,150,(255,100,100),(150,50,50),glow_r=2)
        for i,s in enumerate(extreme_scores[:8]):
            y2=180+i*32
            draw_glass_panel(SCREEN,3*WIDTH//4-80,y2-2,160,24,alpha=35)
            col=medal_cols[min(i,3)]
            row=FONT.render(f"#{i+1} {s}",True,col)
            SCREEN.blit(row,(3*WIDTH//4-row.get_width()//2,y2+4))
        draw_glass_panel(SCREEN,20,HEIGHT-GROUND_H-46,WIDTH-40,36,alpha=50)
        hint=SMALL.render("ENTER to return",True,BLACK)
        SCREEN.blit(hint,(WIDTH//2-hint.get_width()//2,HEIGHT-GROUND_H-36))
        draw_vignette(SCREEN)
        draw_fps_overlay(SCREEN)
        pygame.display.update(); CLOCK.tick(FPS)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_RETURN or keybind_matches(ev, "hotkey_back"):
                    run=False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if back_button.is_clicked((mx, my)):
                    run = False

def stats_screen():
    run=True; t0=pygame.time.get_ticks()
    back_button = Button(20, 20, 60, 40, "<", accent_col=(255, 255, 255))
    while run:
        t=(pygame.time.get_ticks()-t0)/1000.0
        draw_background(SCREEN,t,mode=selected_bg)
        draw_ground_cinematic(SCREEN,t)
        
        # Draw back button
        back_button.draw(SCREEN, t)
        
        draw_glass_panel(SCREEN,16,10,WIDTH-32,72,alpha=65)
        draw_glow_text(SCREEN,"Statistics",BIG,WIDTH//2,50,(100,220,255),(0,120,200),glow_r=4)
        draw_coin_badge(SCREEN, WIDTH - 8, 8, align_right=True)
        stats = PLAYER_STATS
        items=[
            ("Games Played", stats.get("games_played",0),      (180,230,255)),
            ("Best Score",   stats.get("best_score",0),        (255,220,80)),
            ("Total Score",  stats.get("total_score",0),       (180,255,180)),
            ("Power-Ups",    stats.get("powerups_collected",0),(170,240,255)),
            ("Coins Earned", stats.get("coins_earned",0),      NEON_GOLD),
            ("Items Bought", stats.get("items_bought",0),      (255,170,220)),
        ]
        for i,(lbl,val,col) in enumerate(items):
            y2=114+i*58
            draw_glass_panel(SCREEN,WIDTH//2-170,y2,340,56,alpha=50)
            lsurf=FONT.render(lbl,True,(200,210,235))
            vsurf=MED.render(str(val),True,col)
            SCREEN.blit(lsurf,(WIDTH//2-160,y2+8))
            SCREEN.blit(vsurf,(WIDTH//2+160-vsurf.get_width(),y2+26))
        draw_glass_panel(SCREEN,20,HEIGHT-GROUND_H-46,WIDTH-40,36,alpha=50)
        hint=SMALL.render("ENTER to return",True,BLACK)
        SCREEN.blit(hint,(WIDTH//2-hint.get_width()//2,HEIGHT-GROUND_H-36))
        draw_vignette(SCREEN)
        draw_fps_overlay(SCREEN)
        pygame.display.update(); CLOCK.tick(FPS)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_RETURN or keybind_matches(ev, "hotkey_back"):
                    run=False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if back_button.is_clicked((mx, my)):
                    run = False

# ----------------------------- Game Over Screen ------------------------------
def show_game_over(score, run_coins=0, quest_bonus=0, quest_count=0):
    alpha=0; t0=pygame.time.get_ticks()
    back_button = Button(20, 20, 60, 40, "<", accent_col=(255, 255, 255))
    while True:
        t=(pygame.time.get_ticks()-t0)/1000.0
        CLOCK.tick(FPS)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit(0)
            if ev.type==pygame.KEYDOWN:
                if ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return "retry"
                if ev.key == pygame.K_ESCAPE or keybind_matches(ev, "hotkey_back"):
                    return "menu"
            if ev.type == pygame.MOUSEBUTTONDOWN:
                return "menu"
        if alpha<235: alpha=min(235,alpha+7)
        overlay=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        overlay.fill((5,4,18,alpha)); SCREEN.blit(overlay,(0,0))

        back_button.draw(SCREEN, t)
        draw_coin_badge(SCREEN, WIDTH - 8, 8, align_right=True)

        panel_h = 250 if quest_count or run_coins else 220
        py2=HEIGHT//2-panel_h//2
        draw_glass_panel(SCREEN,WIDTH//2-190,py2,380,panel_h,alpha=80,radius=20)

        neon_line=pygame.Surface((380,2),pygame.SRCALPHA)
        neon_line.fill((*NEON_PINK,200))
        SCREEN.blit(neon_line,(WIDTH//2-190,py2))

        shake_x=int(math.sin(t*16)*4*(max(0,0.5-t)/0.5)) if t<0.5 else 0
        draw_glow_text(SCREEN,"GAME OVER",BIG,WIDTH//2+shake_x,HEIGHT//2-65,
                       (255,90,90),(200,0,0),glow_r=7)

        div=pygame.Surface((260,1),pygame.SRCALPHA)
        div.fill((*NEON_PINK,120))
        SCREEN.blit(div,(WIDTH//2-130,HEIGHT//2-28))

        sc_surf=MED.render(f"Score: {score}",True,(255,240,160))
        SCREEN.blit(sc_surf,(WIDTH//2-sc_surf.get_width()//2,HEIGHT//2-24))

        if run_coins:
            coins_surf = FONT.render(f"Coins this run: +{run_coins}", True, NEON_GOLD)
            SCREEN.blit(coins_surf, (WIDTH//2-coins_surf.get_width()//2, HEIGHT//2+12))
        if quest_count:
            bonus_surf = SMALL.render(
                f"Quest bonus: +{quest_bonus} coins from {quest_count} quest{'s' if quest_count != 1 else ''}",
                True,
                (170, 255, 190),
            )
            SCREEN.blit(bonus_surf, (WIDTH//2-bonus_surf.get_width()//2, HEIGHT//2+38))

        blink=math.sin(t*3.2)>0
        if blink:
            hint=SMALL.render("SPACE retry  ·  CLICK or ESC to menu",True,(200,220,255))
            SCREEN.blit(hint,(WIDTH//2-hint.get_width()//2,HEIGHT//2+72))

        draw_persistence_alert(SCREEN, y=HEIGHT//2+102)
        draw_vignette(SCREEN)
        draw_fps_overlay(SCREEN)
        pygame.display.update()

# ----------------------------- Pause Overlay ---------------------------------
def draw_pause_overlay(surf, t):
    ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
    ov.fill((6,8,22,170)); surf.blit(ov,(0,0))
    draw_glass_panel(surf,WIDTH//2-145,HEIGHT//2-65,290,118,alpha=75,radius=18)
    # Neon top line
    nl=pygame.Surface((290,2),pygame.SRCALPHA)
    nl.fill((*NEON_CYAN,200))
    surf.blit(nl,(WIDTH//2-145,HEIGHT//2-65))
    draw_glow_text(surf,"PAUSED",BIG,WIDTH//2,HEIGHT//2-16,(255,255,180),(200,180,0),glow_r=5)
    hint=SMALL.render("P to resume  ·  ESC to menu",True,(200,220,255))
    surf.blit(hint,(WIDTH//2-hint.get_width()//2,HEIGHT//2+38))
    draw_fps_overlay(surf)

def draw_start_overlay(surf):
    flap_key = SETTINGS.get("hotkey_flap", "space").upper()
    panel_w = 334
    panel_h = 74
    panel_x = WIDTH // 2 - panel_w // 2
    panel_y = HEIGHT - GROUND_H - 156
    draw_glass_panel(surf, panel_x, panel_y, panel_w, panel_h, alpha=70, border_col=(140, 220, 255, 110), radius=18)
    title = SMALL.render(f"{flap_key} or click to launch", True, (235, 245, 255))
    subtitle = TINY.render("The first few pipes open wider so the run eases in.", True, (180, 225, 255))
    surf.blit(title, (panel_x + (panel_w - title.get_width()) // 2, panel_y + 18))
    surf.blit(subtitle, (panel_x + (panel_w - subtitle.get_width()) // 2, panel_y + 42))

# ----------------------------- Main Loop -------------------------------------
def main_loop():
    global selected_bird_key, selected_bg, selected_trail_key
    refresh_daily_quests()
    complete_ready_quests()
    gs       = GameState()
    in_menu  = True
    menu_t   = 0.0
    selected_button = 0

    try:
        if os.path.exists(ASSETS.get("bg_music","")):
            pygame.mixer.music.play(-1)
    except Exception:
        pass

    btn_y_start = 248
    btn_gap     = 54
    btn_w, btn_h= 285, 48
    btn_x       = WIDTH//2 - btn_w//2

    btn_quests = Button(12, 12, 104, 34, "Quests", accent_col=NEON_GREEN)
    btn_dev   = Button(20, HEIGHT - 46, 108, 34, "Dev Tools", accent_col=(255, 150, 80))
    btn_play  = Button(btn_x, btn_y_start,            btn_w, btn_h, "Play",         accent_col=NEON_GOLD)
    btn_cos   = Button(btn_x, btn_y_start+btn_gap,    btn_w, btn_h, "Cosmetics",    accent_col=(180,120,255))
    btn_set   = Button(btn_x, btn_y_start+btn_gap*2,  btn_w, btn_h, "Settings",     accent_col=NEON_CYAN)
    btn_high  = Button(btn_x, btn_y_start+btn_gap*3,  btn_w, btn_h, "High Scores",  accent_col=NEON_GOLD)
    btn_stats = Button(btn_x, btn_y_start+btn_gap*4,  btn_w, btn_h, "Stats",        accent_col=NEON_CYAN)
    btn_extreme = Button(btn_x, btn_y_start+btn_gap*5, btn_w, btn_h, "Extreme",      accent_col=(255,100,100))
    menu_buttons = [btn_play, btn_cos, btn_set, btn_high, btn_stats, btn_extreme]

    demo_bird = Bird(selected_bird_key, trail_key=selected_trail_key)

    while True:
        dt     = CLOCK.tick(FPS) / 1000.0
        menu_t += dt
        t      = time.time() - gs.start_time

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if in_menu:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_SPACE or ev.key == pygame.K_RETURN:
                        if selected_button == 0:
                            particles.clear(); score_pops.clear()
                            in_menu=False; gs=GameState()
                        elif selected_button == 1:
                            cosmetics_room(); demo_bird=Bird(selected_bird_key, trail_key=selected_trail_key)
                        elif selected_button == 2:
                            settings_room()
                        elif selected_button == 3:
                            high_scores_screen()
                        elif selected_button == 4:
                            stats_screen()
                        elif selected_button == 5:
                            particles.clear(); score_pops.clear()
                            in_menu=False; gs=GameState("extreme")
                    elif ev.key == pygame.K_UP:
                        selected_button = (selected_button - 1) % len(menu_buttons)
                    elif ev.key == pygame.K_DOWN:
                        selected_button = (selected_button + 1) % len(menu_buttons)
                    elif ev.key == pygame.K_t:
                        quests_screen()
                    elif ev.key == pygame.K_F1:
                        dev_tools_screen()
                    elif ev.key == pygame.K_c:
                        cosmetics_room(); demo_bird=Bird(selected_bird_key, trail_key=selected_trail_key)
                    elif keybind_matches(ev, "hotkey_cosmetics"):
                        cosmetics_room(); demo_bird=Bird(selected_bird_key, trail_key=selected_trail_key)
                    elif ev.key == pygame.K_o:
                        settings_room()
                    elif keybind_matches(ev, "hotkey_settings"):
                        settings_room()
                    elif ev.key == pygame.K_h: high_scores_screen()
                    elif keybind_matches(ev, "hotkey_high_scores"):
                        high_scores_screen()
                    elif ev.key == pygame.K_s: stats_screen()
                    elif keybind_matches(ev, "hotkey_stats"):
                        stats_screen()
                    elif keybind_matches(ev, "hotkey_extreme"):
                        particles.clear(); score_pops.clear()
                        in_menu=False; gs=GameState("extreme")
                    elif ev.key == pygame.K_q: pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mx,my=ev.pos
                    if btn_quests.is_clicked((mx,my)):
                        quests_screen()
                    elif btn_dev.is_clicked((mx,my)):
                        dev_tools_screen()
                    elif btn_play.is_clicked((mx,my)):
                        particles.clear(); score_pops.clear()
                        in_menu=False; gs=GameState()
                    elif btn_cos.is_clicked((mx,my)):
                        cosmetics_room(); demo_bird=Bird(selected_bird_key, trail_key=selected_trail_key)
                    elif btn_set.is_clicked((mx,my)): settings_room()
                    elif btn_high.is_clicked((mx,my)): high_scores_screen()
                    elif btn_stats.is_clicked((mx,my)): stats_screen()
                    elif btn_extreme.is_clicked((mx,my)):
                        particles.clear(); score_pops.clear()
                        in_menu=False; gs=GameState("extreme")
            else:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_p:
                        gs.paused = not gs.paused
                    elif ev.key == pygame.K_ESCAPE or keybind_matches(ev, "hotkey_back"):
                        gs.paused = False
                        in_menu = True
                    elif not gs.paused and (ev.key in (pygame.K_SPACE, pygame.K_UP) or
                                            keybind_matches(ev, "hotkey_flap")):
                        trigger_flap(gs)
                if ev.type == pygame.MOUSEBUTTONDOWN and not gs.paused:
                    trigger_flap(gs)

        if in_menu:
            gs.bg_mode = selected_bg
            gs.scroll_t += dt
            for c in list(gs.clouds):
                c.update(0.25)
                if c.offscreen():
                    gs.clouds.remove(c)
                    gs.clouds.append(CloudSprite(WIDTH+40, layer=c.layer, mode=selected_bg))
            draw_main_menu(gs, menu_t, menu_buttons, demo_bird, selected_button, btn_quests, btn_dev)
            pygame.display.update()
            continue

        if gs.paused:
            apply_live_cheats(gs)
            bg_mode = current_bg_mode(gs.mode)
            draw_background(SCREEN, t, mode=bg_mode)
            for c in sorted(gs.clouds,key=lambda c:c.layer): c.draw(SCREEN,t,bg_mode)
            for p in gs.pipes: p.draw(SCREEN,t)
            for pu in gs.powerups: pu.draw(SCREEN)
            gs.bird.draw(SCREEN)
            draw_ground_cinematic(SCREEN, gs.scroll_t)
            draw_persistence_alert(SCREEN)
            draw_pause_overlay(SCREEN, t)
            draw_vignette(SCREEN)
            pygame.display.update()
            continue

        gs.scroll_t += dt

        # Cloud parallax
        for c in list(gs.clouds):
            c.update(0.8)
            if c.offscreen():
                gs.clouds.remove(c)
                gs.clouds.append(CloudSprite(WIDTH+random.randint(0,120), layer=c.layer,
                                             mode=current_bg_mode(gs.mode)))

        if gs.waiting_to_start:
            apply_live_cheats(gs)
            bg_mode = current_bg_mode(gs.mode)
            gs.bird.update_idle(gs.idle_bird_y, t)
            draw_background(SCREEN, t, mode=bg_mode)
            for c in sorted(gs.clouds, key=lambda c: c.layer):
                c.draw(SCREEN, t, bg_mode)
            for p in gs.pipes:
                p.draw(SCREEN, t)
            gs.bird.draw(SCREEN)
            draw_ground_cinematic(SCREEN, gs.scroll_t)
            draw_hud(SCREEN, gs)
            draw_start_overlay(SCREEN)
            draw_vignette(SCREEN)
            pygame.display.update()
            continue

        # Update pipes
        pipe_speed = BASE_PIPE_SPEED * (0.6 if gs.bird.slow_motion > 0 else 1.8) * gs.speed_scale()

        # Spawn pipes
        gs.spawn_timer += dt
        # Adjust spawn interval based on speed to maintain consistent spacing
        speed_ratio = max(0.45, pipe_speed / (BASE_PIPE_SPEED * 1.8))
        effective_interval = PIPE_SPAWN_INTERVAL / speed_ratio
        if gs.spawn_timer > effective_interval:
            gs.spawn_timer = 0.0
            # Use fixed spacing based on normal speed
            normal_speed = BASE_PIPE_SPEED * 1.8
            spacing = PIPE_SPAWN_INTERVAL * FPS * normal_speed
            spawn_x = WIDTH + spacing
            gs.pipes.append(gs.make_pipe(spawn_x))
            if random.random() < 0.28:
                gs.powerups.append(PowerUp(spawn_x + 100))

        rem = []
        for p in gs.pipes:
            p.update(pipe_speed, t)
            if p.offscreen(): rem.append(p)
            if not p.passed and p.x + p.width < gs.bird.x:
                p.passed = True
                point_gain = 2 if gs.bird.point_boost > 0 else 1
                gs.score += point_gain
                base_coin_gain = 2 if gs.mode == "extreme" else 1
                coin_gain = base_coin_gain * (2 if gs.bird.coin_boost > 0 else 1)
                gs.run_coins += coin_gain
                # spawn_particles(gs.bird.x+12, gs.bird.y+6,
                #                 (255,255,200), count=12, life=22, glow=True, fade_exp=1.5)
                # if selected_bg != "night":
                #     spawn_embers(gs.bird.x+gs.bird.w//2, gs.bird.y+gs.bird.h//2, NEON_GOLD, count=8)
                add_score_pop(gs.bird.x+gs.bird.w+8, gs.bird.y, coin_gain)
                play_sound(SOUND_SCORE)
        for r in rem:
            try: gs.pipes.remove(r)
            except Exception: pass

        # Update powerups
        pu_speed = BASE_PIPE_SPEED * (0.6 if gs.bird.slow_motion > 0 else 1.0)
        for pu in list(gs.powerups):
            pu.update(pu_speed)
            if pu.offscreen():
                try: gs.powerups.remove(pu)
                except Exception: pass
            if pu.active and gs.bird.rect().colliderect(
                    pygame.Rect(int(pu.x),int(pu.y),pu.size,pu.size)):
                pu.active = False
                if   pu.type=="immunity":    gs.bird.immunity   =POWERUP_DURATION_SEC*FPS
                elif pu.type=="coin_boost":  gs.bird.coin_boost =POWERUP_DURATION_SEC*FPS
                elif pu.type=="point_boost": gs.bird.point_boost=POWERUP_DURATION_SEC*FPS
                elif pu.type=="slow_motion": gs.bird.slow_motion=POWERUP_DURATION_SEC*FPS
                gs.run_powerups += 1
                pickup_col = PowerUp.NEON_COLORS.get(pu.type, (255,220,100))
                spawn_particles(pu.x+pu.size//2, pu.y+pu.size//2,
                                pickup_col, count=24, life=36, glow=True, fade_exp=0.8)
                play_sound(SOUND_POWER)

        gs.bird.update()
        apply_live_cheats(gs)

        # Update particles
        alive = deque()
        for p in particles:
            p.update()
            if p.life > 0:
                alive.append(p)
        particles.clear()
        particles.extend(alive)

        # Collision
        hit = check_collision(gs.bird, gs.pipes, t)
        if hit:
            gs.shake_timer = SHAKE_DURATION
            spawn_particles(gs.bird.x+gs.bird.w//2, gs.bird.y+gs.bird.h//2,
                            (255,80,80), count=45, life=45, glow=True, fade_exp=0.7)
            spawn_embers(gs.bird.x+gs.bird.w//2, gs.bird.y+gs.bird.h//2,
                         (255,140,40), count=16)
            play_sound(SOUND_HIT)
            run_coins, quest_bonus, quest_count = finish_run(gs)
            hs = load_json(HIGH_SCORES_FILE, {"normal": [], "extreme": []})
            if isinstance(hs, list):
                # Convert old format to new format
                hs = {"normal": hs, "extreme": []}
            hs[gs.mode].append(gs.score)
            hs[gs.mode] = sorted(hs[gs.mode], reverse=True)[:8]
            save_json(HIGH_SCORES_FILE, hs)
            next_action = show_game_over(gs.score, run_coins, quest_bonus, quest_count)
            restart_mode = gs.mode
            gs = GameState(restart_mode)
            in_menu = next_action != "retry"
            continue

        cam = apply_camera_shake(gs)

        # ---- Draw frame ----
        bg_mode = current_bg_mode(gs.mode)
        draw_background(SCREEN, t, mode=bg_mode)

        # Clouds (all layers behind pipes)
        for c in sorted(gs.clouds, key=lambda c: c.layer):
            c.draw(SCREEN, t, bg_mode)

        # Pipes
        for p in gs.pipes:
            p.draw(SCREEN, t, cam)

        # PowerUps, Particles, Bird
        for pu in gs.powerups:
            if pu.active:
                pu.draw(SCREEN, cam)
        for p in list(particles):
            p.draw(SCREEN, cam)

        gs.bird.draw(SCREEN, cam)

        draw_ground_cinematic(SCREEN, gs.scroll_t)
        draw_hud(SCREEN, gs)
        draw_vignette(SCREEN)
        pygame.display.update()

# ----------------------------- Entry point -----------------------------------
if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:
        pygame.quit()
        print("Error:", e)
        raise

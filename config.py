import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTOPAY_TOKEN = os.getenv("CRYPTOPAY_TOKEN")
ADMIN_IDS = eval(os.getenv("ADMIN_IDS", "[]"))

# config.py
BOT_TOKEN = "7920504352:AAG8CNg_vo_3UQfPFPU7kazBODDi2QONVKQ"
BOT_USERNAME = "Botsplitsbot"

# ← СПИСОК АДМИНОВ
ADMIN_IDS = [8325018951, 6081238549]  # ← ТВОИ ID

SUPPORT_USERNAME = "FrontMan_work"

# === СПЛИТЫ ===
PRICES = {
    "Гретый": {
        "10000": 10,
        "15000": 15,
        "20000": 25,
        "30000": 45,
        "50000": 75,
        "75000": 120,
        "100000": 140,
        "120000": 155
    },
    "Не Гретый": {
        "10000": 7,
        "20000": 15,
        "30000": 20,
        "50000": 25,
        "75000": 40,
        "100000": 55
    }
}

# === eSIM — НОВАЯ КАТЕГОРИЯ ===
ESIM_OPERATORS = ["МТС", "БИЛАЙН", "МЕГАФОН", "ЙОТА"]
ESIM_PRICE = 7  # $


CRYPTOPAY_TOKEN = "479474:AAl7Z2zO3AGjRQLlUvJ0KIjgE3Kl5N0tJdt"

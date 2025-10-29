# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import PRICES, ESIM_OPERATORS
from database import get_available_count

def format_size(size: str) -> str:
    size = size.lstrip("0") or "0"
    if len(size) <= 3: return size
    return f"{size[:-3]}.{size[-3:]}"

def main_menu():
    kb = [
        [KeyboardButton(text="Купить Гретый Сплит"), KeyboardButton(text="Купить Не Гретый Сплит")],
        [KeyboardButton(text="Продажа eSIM")],
        [KeyboardButton(text="Мои покупки"), KeyboardButton(text="Поддержка")],
        [KeyboardButton(text="Отзывы")]  # ← БЕЗ РЕФЕРАЛКИ
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def category_menu(category: str):
    kb = []
    for size in PRICES[category]:
        base_price = PRICES[category][size]
        count = get_available_count(category, size)
        status = f" ({count} шт)" if count > 0 else " (нет)"
        display = format_size(size)
        kb.append([InlineKeyboardButton(text=f"{display} сплита — {base_price}$ {status}", callback_data=f"buy_{category}_{size}")])
    kb.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def esim_menu():
    kb = []
    for op in ESIM_OPERATORS:
        count = get_available_count("eSIM", op)
        status = f" ({count} шт)" if count > 0 else " (нет)"
        kb.append([InlineKeyboardButton(text=f"{op} — 7$ {status}", callback_data=f"buy_esim_{op}")])
    kb.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def review_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="отзывы", url="https://t.me/FrontMan_Shop_rep")]

    ])

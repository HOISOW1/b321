# bot.py
import asyncio
import platform
import os
import sqlite3
import logging

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS, PRICES, SUPPORT_USERNAME, BOT_USERNAME, ESIM_OPERATORS, ESIM_PRICE
from database import *
from cryptobot import create_invoice, check_invoice
from keyboards import main_menu, category_menu, esim_menu, review_button, format_size

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

init_db()
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class AddPackage(StatesGroup):
    category = State()
    size = State()
    accounts = State()

@dp.message(Command("start"))
async def start(m: types.Message):
    save_user(m.from_user.id, m.from_user.username or "NoName")
    await m.answer_photo(FSInputFile("start.jpg"), "*Магазин Сплит-Аккаунтов*\n\nВыберите действие:", reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(F.text == "Отзывы")
async def reviews(m: types.Message):
    await m.answer("Оставьте отзыв о покупке:", reply_markup=review_button())

@dp.message(F.text == "Продажа eSIM")
async def esim_start(m: types.Message):
    await m.answer_photo(FSInputFile("esim.jpg"), "*Продажа eSIM*\n\nВыберите оператора:", reply_markup=esim_menu(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_esim_"))
async def buy_esim(call: types.CallbackQuery):
    operator = call.data.split("_")[2]
    if operator not in ESIM_OPERATORS:
        return await call.answer("Ошибка оператора", show_alert=True)

    pkg = get_available_package("eSIM", operator)
    if not pkg:
        return await call.answer("Нет в наличии!", show_alert=True)

    final_price = round(ESIM_PRICE * 1.06, 2)

    inv, url = await create_invoice(final_price, f"eSIM {operator}")
    if not inv:
        return await call.answer("Ошибка оплаты", show_alert=True)

    add_purchase(call.from_user.id, call.from_user.username or "NoName", pkg["id"], inv, None)
    await call.message.answer_photo(
        FSInputFile("esim.jpg"),
        f"*Оплата eSIM*\n\n"
        f"Оператор: *{operator}*\n"
        f"Цена: *{ESIM_PRICE}$* USDT\n\n"
        f"[Оплатить здесь]({url})",
        parse_mode="Markdown", disable_web_page_preview=True
    )
    await call.message.answer("После оплаты: */check*", reply_markup=review_button())
    await call.message.delete()

@dp.message(F.text == "Купить Гретый Сплит")
async def buy_warm(m: types.Message):
    await m.answer_photo(FSInputFile("warm.jpg"), "*Пакет Гретый Сплит:*", reply_markup=category_menu("Гретый"), parse_mode="Markdown")

@dp.message(F.text == "Купить Не Гретый Сплит")
async def buy_cold(m: types.Message):
    await m.answer_photo(FSInputFile("cold.jpg"), "*Пакет Не Гретый Сплит:*", reply_markup=category_menu("Не Гретый"), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_split(call: types.CallbackQuery):
    _, cat, size = call.data.split("_")
    base_price = PRICES[cat][size]
    final_price = round(base_price * 1.06, 2)

    pkg = get_available_package(cat, size)
    if not pkg: return await call.answer("Нет в наличии!", show_alert=True)

    inv, url = await create_invoice(final_price, f"{cat} {format_size(size)}")
    if not inv: return await call.answer("Ошибка оплаты", show_alert=True)

    add_purchase(call.from_user.id, call.from_user.username or "NoName", pkg["id"], inv, None)
    await call.message.answer(
        f"*Оплата*\n\n"
        f"Пакет: *{cat} — {format_size(size)}*\n"
        f"Цена: *{base_price}$* USDT\n\n"
        f"[Оплатить здесь]({url})",
        parse_mode="Markdown", disable_web_page_preview=True
    )
    await call.message.answer("После оплаты: */check*", reply_markup=review_button())
    await call.message.delete()

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer_photo(FSInputFile("start.jpg"), "*Магазин Сплит-Аккаунтов*", reply_markup=main_menu(), parse_mode="Markdown")

@dp.message(Command("add"))
async def add_start(m: types.Message, state: FSMContext):
    if m.from_user.id not in ADMIN_IDS:
        return await m.answer("Нет доступа.")
    await m.answer("Категория (гретый / не гретый / esim):")
    await state.set_state(AddPackage.category)

@dp.message(AddPackage.category)
async def add_cat(m: types.Message, state: FSMContext):
    cat = m.text.strip().lower()
    if cat == "гретый": cat = "Гретый"
    elif cat == "не гретый": cat = "Не Гретый"
    elif cat == "esim": cat = "eSIM"
    else: return await m.answer("Только: гретый / не гретый / esim")
    
    if cat == "eSIM":
        await m.answer("Оператор (МТС / БИЛАЙН / МЕГАФОН / ЙОТА):")
        await state.update_data(category=cat)
        await state.set_state(AddPackage.size)
    else:
        await state.update_data(category=cat)
        await m.answer("Размер (например: 100000):")
        await state.set_state(AddPackage.size)

@dp.message(AddPackage.size)
async def add_size(m: types.Message, state: FSMContext):
    data = await state.get_data()
    cat = data["category"]
    
    if cat == "eSIM":
        operator = m.text.strip().upper()
        if operator not in ESIM_OPERATORS:
            return await m.answer("Только: МТС / БИЛАЙН / МЕГАФОН / ЙОТА")
        await state.update_data(size=operator)
        await m.answer("Количество (например: 10):")
    else:
        size = m.text.strip()
        if not size.isdigit(): return await m.answer("Только цифры!")
        await state.update_data(size=size)
        await m.answer("Аккаунты (по одному на строку):\n`логин-пароль-код`")
    await state.set_state(AddPackage.accounts)

@dp.message(AddPackage.accounts)
async def add_accs(m: types.Message, state: FSMContext):
    data = await state.get_data()
    cat = data["category"]
    size = data["size"]

    if cat == "eSIM":
        count = m.text.strip()
        if not count.isdigit() or int(count) <= 0:
            return await m.answer("Введите число больше 0")
        for _ in range(int(count)):
            add_package(cat, size, ["dummy"])
        await m.answer(f"Добавлено {count} eSIM {size}")
    else:
        lines = [l.strip() for l in m.text.split("\n") if l.strip()]
        valid = []
        for line in lines:
            parts = line.split("-", 2)
            if len(parts) == 3 and all(p.strip() for p in parts):
                valid.append(f"{parts[0].strip()}-{parts[1].strip()}-{parts[2].strip()}")
        if not valid: return await m.answer("Неверный формат!")
        
        if cat not in PRICES or size not in PRICES[cat]:
            return await m.answer(f"Ошибка: размер {size} не найден")
        pid = add_package(cat, size, valid)
        await m.answer(f"Пакет #{pid} добавлен! Сплита: {len(valid)}")
    await state.clear()

@dp.message(Command("check"))
async def check(m: types.Message):
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM purchases WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1", (m.from_user.id,))
    p = c.fetchone()
    conn.close()
    if not p: return await m.answer("Нет заказов.")

    status = await check_invoice(p[4])
    if status != "paid":
        return await m.answer("Не оплачено. /check позже.")

    pkg = get_package_by_id(p[3])
    if not pkg or pkg["status"] == "sold":
        return await m.answer("Пакет уже выдан.")

    mark_package_sold(p[3])

    if pkg["category"] == "eSIM":
        await m.answer(
            "*Оплачено!*\n\n"
            "eSIM будет выдан вручную.\n\n"
            "Напишите @FrontMan_work",
            parse_mode="Markdown",
            reply_markup=review_button()
        )
    else:
        accs = [a for a in pkg["accounts"].split("\n") if a.strip() and a != "dummy"]
        text = f"*Оплачено!*\n\n"
        text += f"Пакет: {pkg['category']} — {format_size(pkg['package_type'])}\n"
        text += f"Сплита: {len(accs)}\n\n"
        text += "*Аккаунты:*\n"
        for a in accs:
            login, pwd, code = a.split("-", 2)
            text += f"`{login}`\n`{pwd}`\n`{code}`\n\n"

        await m.answer(
            "*Внимание* : Аккаунты выдаются в формате «Логин:Пароль:Кодовое слово»\n\n"
            "В случае если лимит не верный обратитесь в поддержку",
            parse_mode="Markdown"
        )

        photo_path = "delivery.jpg"
        if os.path.exists(photo_path):
            await m.answer_photo(FSInputFile(photo_path), text, parse_mode="Markdown", reply_markup=review_button())
        else:
            await m.answer(text, parse_mode="Markdown", reply_markup=review_button())

    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    c.execute("UPDATE purchases SET status='paid' WHERE id=?", (p[0],))
    conn.commit()
    conn.close()

@dp.message(F.text == "Поддержка")
async def support(m: types.Message): await m.answer(f"Поддержка: @{SUPPORT_USERNAME}")

@dp.message(F.text == "Мои покупки")
async def my_purchases(m: types.Message):
    p = get_user_purchases(m.from_user.id)
    if not p: return await m.answer("У вас нет покупок.")
    text = "*Ваши покупки:*\n\n"
    for i in p:
        status = "Оплачено" if i['status'] == 'paid' else "Ожидает"
        if i['category'] == 'eSIM':
            text += f"• eSIM {i['package_type']} — {status}\n"
        else:
            text += f"• {i['category']} — {format_size(i['package_type'])} — {status}\n"
    await m.answer(text, parse_mode="Markdown")

async def main():
    log.info("БОТ ЗАПУЩЕН!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())  # ← dp.start_polling(bot)

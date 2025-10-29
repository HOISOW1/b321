# cryptobot.py
import aiohttp
from config import CRYPTOPAY_TOKEN

async def create_invoice(amount: float, description: str):
    print(f"[CRYPTOPAY] Создаю счёт: {amount}$ | {description}")
    url = "https://pay.crypt.bot/api/createInvoice"
    payload = {
        "token": CRYPTOPAY_TOKEN,
        "amount": int(amount * 1),  # в центах
        "asset": "USDT",
        "description": description,
        "payload": "split_sale"
    }
    headers = {"Crypto-Pay-API-Token": CRYPTOPAY_TOKEN}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                print(f"[CRYPTOPAY] Ответ: {data}")
                if data.get("ok"):
                    result = data["result"]
                    return result["invoice_id"], result["pay_url"]
                else:
                    print(f"[CRYPTOPAY] Ошибка: {data}")
                    return None, None
    except Exception as e:
        print(f"[CRYPTOPAY] Исключение: {e}")
        return None, None

async def check_invoice(invoice_id: str):
    print(f"[CRYPTOPAY] Проверяю счёт: {invoice_id}")
    url = "https://pay.crypt.bot/api/getInvoices"
    payload = {"token": CRYPTOPAY_TOKEN, "invoice_ids": [invoice_id]}
    headers = {"Crypto-Pay-API-Token": CRYPTOPAY_TOKEN}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                print(f"[CRYPTOPAY] Статус: {data}")
                if data.get("ok") and data["result"]["items"]:
                    return data["result"]["items"][0]["status"]
                return "pending"  # ← ВАЖНО! НЕ None
    except Exception as e:
        print(f"[CRYPTOPAY] Ошибка проверки: {e}")
        return "pending"  # ← И ЗДЕСЬ!
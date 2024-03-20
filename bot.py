import os
from pyrogram import Client, filters
from dotenv import load_dotenv
from pyrogram.enums import ParseMode
import logging
import pymongo


load_dotenv()
TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
PAYMENT_CARD = os.getenv("PAYMENT_CARD")

app = Client(TELEGRAM_SESSION, api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH)

logging.basicConfig(filename="logs/bot.log", level=logging.INFO)

connection = pymongo.MongoClient("mongodb://localhost:27017/")
db = connection["shop"]

users_db = db["users"]
areas_db = db["areas"]
products_db = db["products"]
@app.on_message(filters.command("start", prefixes="/"))
def start(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.chat.id})

        if user:
            msg.reply_text("Ваш статус: Whitelist")

            areas = areas_db.find()

            if areas:
                text = "Выберите подходящий район Киева"
                for area in areas:
                    text = text + f"\n`/area {area['id']}` - {area['name']}"

                msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

            else:
                msg.reply_text("No areas")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("area", prefixes="/"))
def area(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.chat.id})

        if user:
            area = msg.text.split()[1]
            products = products_db.find({"area": area})

            products_weight = []

            for product in products:
                products_weight.append(product["weight"])

            products_weight = set(products_weight)

            text = "Выберите подходящий район Киева"

            for weight in products_weight:
                text = text + f"\n`/product {weight} {area}` - {weight}г"

            msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("product", prefixes="/"))
def product(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.chat.id})

        if user:
            weight = msg.text.split()[1]
            area = msg.text.split()[2]
            product = products_db.find_one({"weight": weight, "area": area})

            msg.reply_text(f"Шиш {product['weight']}г\nРайон: {product['area']}\nЦена: {product['price']}")
            msg.reply_text(f"Оплатите `{product['price']}`грн на карту `{PAYMENT_CARD}` в течение 20 минут", parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("me", prefixes="/"))
def me(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.chat.id})

        if user:
            msg.reply_text(f"Привет, {user['name']}\nТвой айди: `{user['id']}`",
                           parse_mode=ParseMode.MARKDOWN)

            products = products_db.find({"buyer": user["id"]}).sort("buy_time", 1)

            for product in products:
                area = areas_db.find_one({"id": product["area"]})
                msg.reply_text(
                    f"`{product['id']}` Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['buy_time'].strftime("%m-%d-%y %H:%M")}",
                    parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


if __name__ == "__main__":
    app.run()

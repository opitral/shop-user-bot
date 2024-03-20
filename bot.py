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
BOT_ADMIN_ID = int(os.getenv("BOT_ADMIN_ID"))

app = Client(TELEGRAM_SESSION, api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH)

logging.basicConfig(filename="logs/bot.log", level=logging.INFO)

connection = pymongo.MongoClient("mongodb://localhost:27017/")
db = connection["shop"]

users_db = db["users"]
areas_db = db["areas"]
products_db = db["products"]


@app.on_message(filters.command("start", prefixes="/") & filters.me)
def start_admin(_, msg):
    try:
        logging.info(msg)

        areas = areas_db.find({"visible": True})

        if areas:
            text = "Доступные районы"

            for area in areas:
                text += f"\n`/area {area['id']}` - {area['name']}"

            msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

        else:
            msg.reply_text("No areas")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("area", prefixes="/") & filters.me)
def area_admin(_, msg):
    try:
        logging.info(msg)

        area = int(msg.text.split()[1])
        products = products_db.find({"area": area})

        products_weight = []

        for product in products:
            products_weight.append(product["weight"])

        products_weight = set(products_weight)

        text = "Доступные товары"

        for weight in products_weight:
            text += f"\n`/product {area} {weight}` - Шиш {weight}г"

        msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("product", prefixes="/") & filters.me)
def product_admin(_, msg):
    try:
        logging.info(msg)

        area = int(msg.text.split()[1])
        weight = int(msg.text.split()[2])
        products = products_db.find({"weight": weight, "area": area, "visible": True})

        for product in products:
            area = areas_db.find_one({"id": product['area']})
            msg.reply_text(f"Шиш {product['weight']}г {area['name']} {product['price']}грн\n{product['photo']}")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("users", prefixes="/") & filters.me)
def users_admin(_, msg):
    try:
        logging.info(msg)

        users = users_db.find({"visible": True})

        text = "Whitelist"

        for user in users:
            text += f"\n`/user {user['id']}` - {user['username']}"

        msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("user", prefixes="/") & filters.me)
def user_admin(_, msg):
    try:
        _id = int(msg.text.split()[1])
        user = users_db.find_one({"id": _id})
        products = list(products_db.find({"buyer": _id}))
        add_time = user['add_time'].strftime("%m-%d-%y %H:%M")

        msg.reply_text(
            f"id: `{user['id']}`\nname: {user['name']}\nusername: {user['username']}\ncount of products: {len(products)}\nadd time: {add_time}",
            parse_mode=ParseMode.MARKDOWN)

        for product in products:
            area = areas_db.find_one({"id": product["area"]})
            msg.reply_text(
                f"`{product['id']}` Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['buy_time'].strftime("%m-%d-%y %H:%M")}",
                parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("start", prefixes="/"))
def start(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.chat.id})

        if user:
            areas = areas_db.find({"visible": True})

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
            area = int(msg.text.split()[1])
            products = products_db.find({"area": area})

            if products:
                products_weight = []

                for product in products:
                    products_weight.append(product["weight"])

                products_weight = set(products_weight)

                text = "Выберите товар"

                for weight in products_weight:
                    text += f"\n`/product {area} {weight}` - Шиш {weight}г"

                msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

        else:
            msg.reply_text("No products")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("product", prefixes="/"))
def product(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.chat.id})

        if user:
            area = int(msg.text.split()[1])
            weight = int(msg.text.split()[2])
            product = products_db.find_one({"weight": weight, "area": area, "visible": True})

            if product:
                area = areas_db.find_one({"id": product['area']})

                msg.reply_text(f"Шиш {product['weight']}г\nРайон: {area['name']}\nЦена: {product['price']}грн")
                msg.reply_text(f"Оплатите `{product['price']}`грн на карту `{PAYMENT_CARD}` в течение 20 минут",
                               parse_mode=ParseMode.MARKDOWN)

                app.send_message(BOT_ADMIN_ID,
                                 f"Новый заказ от {user['username']}\nШиш {product['weight']}г {product['area']} {product['price']}грн\n\n`/give {product['area']} {weight} {user['id']}`",
                                 parse_mode=ParseMode.MARKDOWN)

            else:
                msg.reply_text("No product")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("me", prefixes="/"))
def me(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.chat.id})

        if user:
            products = list(products_db.find({"buyer": user["id"]}).sort("buy_time", 1))

            msg.reply_text(
                f"Привет, {user['name']}\nТвой статус: Whitelist\nТвой айди: `{user['id']}`\nВсего покупок: {len(products)}",
                parse_mode=ParseMode.MARKDOWN)

            for product in products:
                area = areas_db.find_one({"id": product["area"]})
                msg.reply_text(
                    f"`{product['id']}` Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['buy_time'].strftime("%m-%d-%y %H:%M")}",
                    parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


if __name__ == "__main__":
    app.run()

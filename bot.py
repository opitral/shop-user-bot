import os
import telebot
from dotenv import load_dotenv
import logging
import pymongo

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ADMIN_ID = int(os.getenv("BOT_ADMIN_ID"))
PAYMENT_CARD = os.getenv("PAYMENT_CARD")

bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(filename="logs/bot.log", level=logging.INFO)

connection = pymongo.MongoClient("mongodb://localhost:27017/")
db = connection["shop"]

users_db = db["users"]
areas_db = db["areas"]
products_db = db["products"]


@bot.message_handler(commands=["start"])
def start_message(message):
    logging.info(message)
    try:
        if message.chat.id == BOT_ADMIN_ID:
            areas = areas_db.find({"visible": True})

            if areas:
                text = "Доступные районы"
                for area in areas:
                    text = text + f"\n`/area {area['id']}` - {area['name']}"

                bot.send_message(message.chat.id, text, parse_mode="Markdown")

            else:
                bot.send_message(message.chat.id, "No areas")

    except Exception as ex:
        logging.error(ex)


@bot.message_handler(commands=["area"])
def area_message(message):
    logging.info(message)
    try:
        if message.chat.id == BOT_ADMIN_ID:
            area = int(message.text.split()[1])
            products = products_db.find({"area": area})

            products_weight = []

            for product in products:
                products_weight.append(product["weight"])

            products_weight = set(products_weight)

            text = "Доступные товары"

            for weight in products_weight:
                text += f"\n`/product {area} {weight}` - Шиш {weight}г"

            bot.send_message(message.chat.id, text, parse_mode="Markdown")

    except Exception as ex:
        logging.error(ex)


@bot.message_handler(commands=["product"])
def product_message(message):
    logging.info(message)
    try:
        if message.chat.id == BOT_ADMIN_ID:
            area = int(message.text.split()[1])
            weight = int(message.text.split()[2])
            products = products_db.find({"weight": weight, "area": area, "visible": True})

            for product in products:
                area = areas_db.find_one({"id": product['area']})
                bot.send_message(message.chat.id,
                             f"Шиш {product['weight']}г {area['name']} {product['price']}грн\n{product['photo']}")

    except Exception as ex:
        logging.error(ex)


@bot.message_handler(commands=["users"])
def users_message(message):
    logging.info(message)
    try:
        if message.chat.id == BOT_ADMIN_ID:
            users = users_db.find({"visible": True})

            text = "Whitelist"

            for user in users:
                text += f"\n`/user {user['id']}` - {user['username']}"

            bot.send_message(message.chat.id, text, parse_mode="Markdown")

    except Exception as ex:
        logging.error(ex)


@bot.message_handler(commands=["user"])
def user_message(message):
    logging.info(message)
    try:
        if message.chat.id == BOT_ADMIN_ID:
            _id = int(message.text.split()[1])
            user = users_db.find_one({"id": _id})
            products = list(products_db.find({"buyer": _id}))
            add_time = user['add_time'].strftime("%m-%d-%y %H:%M")

            bot.send_message(message.chat.id, f"id: `{user['id']}`\nname: {user['name']}\nusername: {user['username']}\ncount of products: {len(products)}\nadd time: {add_time}", parse_mode="Markdown")

            for product in products:
                area = areas_db.find_one({"id": product["area"]})
                bot.send_message(message.chat.id, f"`{product['id']}` Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['buy_time'].strftime("%m-%d-%y %H:%M")}", parse_mode="Markdown")

    except Exception as ex:
        print(ex)
        logging.error(ex)


bot.infinity_polling()

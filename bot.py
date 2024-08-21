import os
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from dotenv import load_dotenv
import logging
import pymongo
import pyimgur

load_dotenv()
TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
PAYMENT_CARD = os.getenv("PAYMENT_CARD")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CLIENT_ID = os.getenv("IMGUR_ID")
CLIENT_SECRET = os.getenv("IMGUR_SECRET")
DB_STRING = os.getenv("DB_STRING")

app = Client(TELEGRAM_SESSION, api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH)

logging.basicConfig(filename="bot.log", level=logging.INFO)

connection = pymongo.MongoClient(DB_STRING)
db = connection["shop"]

users_db = db["users"]
areas_db = db["areas"]
products_db = db["products"]

im = pyimgur.Imgur(CLIENT_ID)

with app:
    app.send_message(ADMIN_ID, "бот запущен")


@app.on_message(filters.command("notify", prefixes="/"))
def notify(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            users = list(users_db.find({"visible": True}))

            if len(users) > 0:
                message = msg.text.replace("/notify ", "")
                ok_msgs = 0
                for user in users:
                    try:
                        app.send_message(user["id"], message, parse_mode=ParseMode.MARKDOWN)
                        ok_msgs += 1

                    except:
                        continue

                msg.reply_text(f"было отправлено {ok_msgs}/{len(users)} сообщений")

            else:
                msg.reply_text("no users")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("users", prefixes="/"))
def users(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            users = users_db.find({"visible": True})

            text = "Whitelist"

            for user in users:
                text += f"\n`/user {user['id']}` - {user['username']}"

            msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("user", prefixes="/"))
def user(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            _id = int(msg.text.split()[1])
            user = users_db.find_one({"id": _id})
            products = list(products_db.find({"buyer": _id}))
            add_time = user['add_time'].strftime("%m-%d-%y %H:%M")

            msg.reply_text(
                f"id: `{user['id']}`\nname: {user['name']}\nusername: {user['username']}\nbalance: {user['balance']}грн\ncount of products: {len(products)}\nadd time: {add_time}",
                parse_mode=ParseMode.MARKDOWN)

            for product in products:
                area = areas_db.find_one({"id": product["area"]})
                msg.reply_text(f"Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['buy_time'].strftime('%m-%d-%y %H:%M')}", parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("give", prefixes="/"))
def give(_, msg):
    try:
        if msg.from_user.id == ADMIN_ID:
            area = int(msg.text.split()[1])
            weight = int(msg.text.split()[2])
            user_id = int(msg.text.split()[3])

            product = products_db.find_one({"area": area, "weight": weight, "visible": True})

            products_db.update_one({"_id": product["_id"]},
                                   {"$set": {"buyer": user_id, "buy_time": datetime.now(), "visible": False}})

            product = products_db.find_one({"_id": product["_id"]})
            area = areas_db.find_one({"id": area})

            text = f"Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['buy_time'].strftime('%m-%d-%y %H:%M')}"

            app.send_message(user_id, text, parse_mode=ParseMode.MARKDOWN)
            app.send_message(ADMIN_ID, text, parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("start", prefixes="/"))
def start(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            areas = list(areas_db.find({"visible": True}))

            if len(areas) > 0:
                text = "Доступные районы"

                for area in areas:
                    text += f"\n`/area {area['id']}` - {area['name']}"

                msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

            else:
                msg.reply_text("No areas")

        else:
            user = users_db.find_one({"id": msg.from_user.id, "visible": True})

            if user:
                areas = areas_db.find({"visible": True})

                if areas:
                    text = "Выберите подходящий район Киева"
                    for area in areas:
                        text = text + f"\n`/area {area['id']}` - {area['name']}"

                    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

                else:
                    msg.reply_text("No areas")

            else:
                users_db.insert_one(
                    {
                        "id": msg.from_user.id,
                        "name": msg.from_user.first_name,
                        "username": "@" + msg.from_user.username,
                        "add_time": datetime.now(),
                        "visible": True
                    }
                )

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("area", prefixes="/"))
def area(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            area = int(msg.text.split()[1])
            products = list(products_db.find({"area": area, "visible": True}))

            if len(products) > 0:
                products_weight = []

                for product in products:
                    products_weight.append(product["weight"])

                products_weight = set(products_weight)

                text = "Доступные товары"

                for weight in products_weight:
                    text += f"\n`/product {area} {weight}` - Шиш {weight}г"

                msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

            else:
                msg.reply_text("No products")

        else:
            user = users_db.find_one({"id": msg.from_user.id, "visible": True})

            if user:
                area = int(msg.text.split()[1])
                products = list(products_db.find({"area": area, "visible": True}))

                if len(products) > 0:
                    products_data = {}

                    for product in products:
                        products_data[product["weight"]] = product["price"]

                    text = "Выберите товар"

                    for product in products_data:
                        text += f"\n`/product {area} {product}` - Шиш {product}г {products_data[product]}грн"

                    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

                else:
                    msg.reply_text("No products")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("product", prefixes="/"))
def product(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            area = int(msg.text.split()[1])
            weight = int(msg.text.split()[2])
            products = list(products_db.find({"weight": weight, "area": area, "visible": True}))

            if len(products) > 0:
                for product in products:
                    area = areas_db.find_one({"id": product['area']})
                    msg.reply_text(f"Шиш {product['weight']}г {area['name']} {product['price']}грн\n{product['photo']}")

            else:
                msg.reply_text("No products")

        else:
            user = users_db.find_one({"id": msg.from_user.id, "visible": True})

            if user:
                area = int(msg.text.split()[1])
                weight = int(msg.text.split()[2])
                product = products_db.find_one({"weight": weight, "area": area, "visible": True})

                if product:
                    area = areas_db.find_one({"id": product['area'], "visible": True})
                    msg.reply_text(
                        f"Шиш {product['weight']}г\nРайон: {area['name']}\nЦена: {product['price']}грн\nБаланс: {user['balance']}")

                    if user['balance'] >= product['price']:
                        users_db.update_one({"id": msg.from_user.id},
                                            {"$set": {"balance": user['balance'] - product['price']}})

                        products_db.update_one({"_id": product['_id']}, {
                            "$set": {"buyer": user['id'], "buy_time": datetime.now(), "visible": False}})

                        product = products_db.find_one({"_id": product['_id']})

                        text = f"Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['buy_time'].strftime('%m-%d-%y %H:%M')}"

                        app.send_message(msg.from_user.id, text)
                        app.send_message(ADMIN_ID, text, parse_mode=ParseMode.MARKDOWN)

                    else:
                        msg.reply_text(
                            f"Оплатите `{product['price'] - user['balance']}`грн на карту `{PAYMENT_CARD}` в течение 20 минут",
                            parse_mode=ParseMode.MARKDOWN)

                        app.send_message(ADMIN_ID,
                                         f"Новый заказ от {user['username']}\nШиш {product['weight']}г {product['area']} {product['price'] - user['balance']}грн\n\n`/give {product['area']} {weight} {user['id']}`",
                                         parse_mode=ParseMode.MARKDOWN)

                else:
                    msg.reply_text("No product")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("me", prefixes="/"))
def me(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.from_user.id, "visible": True})

        if user:
            products = list(products_db.find({"buyer": user["id"]}).sort("buy_time", 1))

            msg.reply_text(
                f"Привет, {user['name']}\nТвой статус: Whitelist\nТвой айди: `{user['id']}`\nБаланс: {user['balance']}грн\nВсего покупок: {len(products)}",
                parse_mode=ParseMode.MARKDOWN)

            for product in products:
                area = areas_db.find_one({"id": product["area"]})
                msg.reply_text(
                    f"Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['buy_time'].strftime('%m-%d-%y %H:%M')}",
                    parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("balance", prefixes="/"))
def balance(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            amount = int(msg.text.split()[1])
            user_id = int(msg.text.split()[2])

            user = users_db.find_one({"id": user_id})
            users_db.update_one({"id": user_id}, {"$set": {"balance": user['balance'] + amount}})
            user = users_db.find_one({"id": user_id})

            msg.reply_text(
                f"id: `{user['id']}`\nname: {user['name']}\nusername: {user['username']}\nbalance: {user['balance']}грн",
                parse_mode=ParseMode.MARKDOWN)

            app.send_message(user_id, f"Ваш баланс пополнен на {amount}грн\nБаланс: {user['balance']}грн")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("help", prefixes="/"))
def help(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            text = f"`/me` - Личный кабинет\n`/start` - Получить доступные районы\n`/area n` - Получить доступные товары на районе\n`/product n m` - Перейти к оплате товара\n`/oper` - Позвать опера\n`/help` - Помощь\n`/users` - Получить доступных клиентов\n`/user n` - Получить данные пользователя\n`/give n m i` - Выдать продукт пользователю\n`/balance n m` - Изменить баланс пользователя\n`/notify n` - Уведомление для всех клиентов"
            msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

        else:
            user = users_db.find_one({"id": msg.from_user.id, "visible": True})

            if user:
                text = f"`/me` - Личный кабинет\n`/start` - Получить доступные районы\n`/area n` - Получить доступные товары на районе\n`/product n m` - Перейти к оплате товара\n`/oper` - Позвать опера\n`/help` - Помощь"
                msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.command("oper", prefixes="/"))
def oper(_, msg):
    try:
        logging.info(msg)

        user = users_db.find_one({"id": msg.from_user.id, "visible": True})

        if user:
            app.send_message(ADMIN_ID, f"Вызов от {user['username']}")
            msg.reply_text("Запрос отправлен")

    except Exception as ex:
        logging.error(ex)


@app.on_message(filters.photo)
def photo(_, msg):
    try:
        logging.info(msg)

        if msg.from_user.id == ADMIN_ID:
            photo = msg.download()
            uploaded_image = im.upload_image(photo)
            os.remove(photo)

            weight = int(msg.caption.split()[0])
            area = int(msg.caption.split()[1])
            price = int(msg.caption.split()[2])

            product = products_db.insert_one(
                {
                    "weight": weight,
                    "area": area,
                    "price": price,
                    "photo": uploaded_image.link,
                    "add_time": datetime.now(),
                    "visible": True
                }
            )

            product = products_db.find_one({"_id": product.inserted_id})
            area = areas_db.find_one({"id": product['area']})

            msg.reply_text("Товар добавлен")

            msg.reply_text(
                f"Шиш {product['weight']}г {area['name']} - {product['photo']}\n\n{product['add_time'].strftime('%m-%d-%y %H:%M')}",
                parse_mode=ParseMode.MARKDOWN)

    except Exception as ex:
        logging.error(ex)


if __name__ == "__main__":
    app.run()

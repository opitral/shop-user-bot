import os
from datetime import datetime

from pyrogram import Client, filters
from dotenv import load_dotenv
from pyrogram.enums import ParseMode

from repository import user_repo, product_repo

load_dotenv()
TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

app = Client(TELEGRAM_SESSION, api_id=TELEGRAM_API_ID, api_hash=TELEGRAM_API_HASH)


@app.on_message(filters.command("start", prefixes="/"))
def start(_, msg):
    user = user_repo.get_by_id(msg.chat.id)

    if user:
        products = product_repo.get_all()

        if products:
            text = ""

            for product in products:
                text += f"\n`id{product['id']}` {product['name']}"

            msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

        else:
            msg.reply_text("No products")


@app.on_message(filters.command("buy", prefixes="/"))
def buy(_, msg):
    pass


@app.on_message(filters.command("me", prefixes="/"))
def me(_, msg):
    user = user_repo.get_by_id(msg.chat.id)

    if user:
        msg.reply_text(f"Hello, {user['name']}\nYour id: `{user['id']}`\nBalance: {user['balance']}", parse_mode=ParseMode.MARKDOWN)

        for product in product_repo.get_by_user(user['id']):
            msg.reply_text(f"`id{product['id']}` {product['name']} - {product['photo']}\n\n{product['buy_time'].strftime("%m-%d-%y %H:%M")}", parse_mode=ParseMode.MARKDOWN)



if __name__ == "__main__":
    app.run()

import os
from pyrogram import Client, filters
from dotenv import load_dotenv

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
                text += f"\n{product['id']}. {product['name']}"

            msg.reply_text(text)

        else:
            msg.reply_text("No products")


@app.on_message(filters.command("buy", prefixes="/") & filters.me)
def buy(_, msg):
    pass


if __name__ == "__main__":
    app.run()

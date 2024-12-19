from aiogram import F, Router, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

import config
import db
import text
import new_langchain_utils

dp = Dispatcher(storage=MemoryStorage())
router = Router()
bot = Bot(token=config.BOT_TOKEN)


@router.message(Command("start"))
async def start_handler(msg: Message):
    chat_id = msg.chat.id
    await msg.answer(text.first_message)
    db.save_message_to_db(chat_id, text.first_message, "ai")


@router.message(F.content_type == "text")
async def message_handler(msg: Message):
    await bot.send_chat_action(chat_id=msg.chat.id, action="typing")
    chat_id = msg.chat.id
    answer = await new_langchain_utils.run_llm(chat_id, msg.text)
    await msg.answer(answer, disable_web_page_preview=True)

from aiogram.dispatcher.middlewares import BaseMiddleware

from bot import dp
from logger import message_logger, format_name


class Middleware(BaseMiddleware):
    async def on_process_message(self, message, data):
        message_logger.info(
            f'[message from {format_name(message.from_user)}] {message.text}')

    async def on_callback_query(self, query):
        print(query.data)


dp.middleware.setup(Middleware())

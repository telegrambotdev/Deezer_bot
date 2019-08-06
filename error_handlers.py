from aiogram import exceptions

from bot import dp


@dp.errors_handler(exceptions.InvalidQueryID)
async def invalid_query(exc):
    print('query is too long', exc)
    return True

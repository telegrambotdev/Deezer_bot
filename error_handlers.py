from aiogram import exceptions

from bot import dp


@dp.errors_handler(exception=Exception)
async def invalid_query(exc):
    print('Exception', exc)
    return True

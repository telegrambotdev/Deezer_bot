from aiogram import exceptions

from bot import dp


@dp.errors_handler(exception=Exception)
async def invalid_query(data, exc):
    print('Exception', data, exc)
    return True

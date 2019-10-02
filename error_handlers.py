import traceback
from aiogram import exceptions

from bot import dp


@dp.errors_handler(exception=exceptions.MessageNotModified)
@dp.errors_handler(exception=exceptions.MessageCantBeDeleted)
@dp.errors_handler(exception=exceptions.InvalidQueryID)
async def ignore(data, exc):
    return True


@dp.errors_handler(exception=Exception)
async def invalid_query(data, exc):
    print(''.join(traceback.format_tb(exc.__traceback__)))
    print('Exception', exc)
    return True

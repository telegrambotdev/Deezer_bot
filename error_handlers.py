import traceback

from bot import dp


@dp.errors_handler(exception=Exception)
async def invalid_query(data, exc):
    print(''.join(traceback.format_tb(exc.__traceback__)))
    print('Exception', exc)
    return True

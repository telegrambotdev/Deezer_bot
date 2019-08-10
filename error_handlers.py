import traceback

from bot import dp


@dp.errors_handler(exception=Exception)
async def invalid_query(data, exc):
    print('Exception', exc)
    print(''.join(traceback.format_tb(exc.__traceback__)))
    return True

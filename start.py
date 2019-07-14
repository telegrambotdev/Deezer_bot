#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import suppress
import asyncio
import shutil

from aiogram.utils import executor

from bot import dp, register_handlers
from var import var
import handlers
import inline_handlers
import callback_handlers
from deezer import handlers as dz_handlers
from spotify import handlers as sp_handlers
from vk import handlers as vk_handlers
from logger import update_logging_files

loop = asyncio.get_event_loop()


async def close():
    var.db.commit()
    var.db.close()
    var.conn.close()
    logging.cancel()
    await var.session.close()


if __name__ == '__main__':
    with suppress(FileNotFoundError):
        shutil.rmtree('downloads')
    register_handlers(
        dp, handlers, inline_handlers, callback_handlers,
        dz_handlers, sp_handlers, vk_handlers)
    logging = asyncio.ensure_future(update_logging_files())
    executor.start_polling(dp, loop=loop)
    loop.run_until_complete(close())
    loop.close()

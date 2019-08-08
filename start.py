#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import suppress
import asyncio
import shutil

from aiohttp import web

from bot import app
from var import var
from logger import update_logging_files

loop = asyncio.get_event_loop()


def import_handlers():
    from deezer import handlers, callback_handlers
    from spotify import handlers
    from vk import handlers, callback_handlers
    from soundcloud import handlers, callback_handlers
    import handlers
    import inline_handlers
    import callback_handlers
    import error_handlers


async def close():
    var.db.commit()
    var.db.close()
    await var.conn.close()
    logging.cancel()
    await var.session.close()


if __name__ == '__main__':
    with suppress(FileNotFoundError):
        shutil.rmtree('downloads')
    logging = asyncio.ensure_future(update_logging_files())
    import_handlers()
    web.run_app(app, port=8081)
    loop.run_until_complete(close())
    loop.close()

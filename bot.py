#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging

import aiohttp
import aioredis
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import get_new_configured_app

import config
from sql import database
from var import var

loop = asyncio.get_event_loop()
WEBHOOK_HOST = 'static.138.197.203.116.clients.your-server.de/deezer'
WEBHOOK_URL_PATH = f'/webhook/{config.bot_token}'

WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_URL_PATH}"


async def on_startup(app):
    webhook = await bot.get_webhook_info()
    if webhook.url != WEBHOOK_URL:
        if not webhook.url:
            await bot.delete_webhook()

        await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(app):
    var.db.commit()
    var.db.close()
    await var.conn.close()
    logging.cancel()
    await var.session.close()
    await asyncio.sleep(0)


try:
    bot = var.bot = Bot(token=config.bot_token, loop=loop)
    storage = MemoryStorage()
    dp = var.dp = Dispatcher(bot, storage=storage)
    app = get_new_configured_app(dp, WEBHOOK_URL_PATH)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    var.downloading = {}
    var.vk_tracks = {}
    var.session = aiohttp.ClientSession(raise_for_status=True)
    print('created session')
    var.CSRFToken = None
    var.spotify_token = None
    var.loop = loop

    var.db = database('db.sqlite')
    var.conn = loop.run_until_complete(aioredis.create_connection(
        ('localhost', 6379), encoding='utf-8', db=4, loop=loop))
    print('datebase connected')


except Exception as e:
    print(e)

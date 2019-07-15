#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio

import aiohttp
import aioredis
from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

import config
from sql import database
from var import var

loop = asyncio.get_event_loop()


try:
    bot = Bot(token=config.bot_token, loop=loop)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    var.downloading = {}
    var.vk_tracks = {}
    var.session = aiohttp.ClientSession(raise_for_status=True)
    print('created session')
    var.CSRFToken = None
    var.loop = loop

    from spotify import Spotify_API
    var.spot = Spotify_API(
        config.spotify_client, config.spotify_secret)
    var.db = database('db.sqlite')
    var.conn = loop.run_until_complete(aioredis.create_connection(
        ('localhost', 6379), encoding='utf-8', db=4, loop=loop))
    print('datebase connected')

except Exception as e:
    print(e)

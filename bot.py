#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import re
from sys import argv

import aiohttp
import aioredis
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

import config
import utils
import filters
from middlewares import Middleware
from sql import database
from var import var

loop = asyncio.get_event_loop()


def register_handlers(dp, handlers, inline_handlers, callback_handlers, dz_handlers, sp_handlers):
    if '-a' in argv:
        dp.register_message_handler(handlers.only_admin_handler)
    dp.register_message_handler(
        handlers.audio_file_handler,
        content_types=[types.ContentType.AUDIO])
    dp.register_message_handler(
        handlers.soundcloud_link_handler,
        lambda m: 'soundcloud.com' in m.text)
    dp.register_callback_query_handler(
        callback_handlers.soundcloud_handler,
        lambda c: c.data.startswith('sc_track'))
    dp.register_message_handler(handlers.start_command_handler, commands=['start'])
    dp.register_message_handler(handlers.quality_setting_handler, commands=['quality'])
    dp.register_message_handler(
        handlers.getstats_handler, commands=['stats'])	
    dp.register_message_handler(
        handlers.today_stats_handler, commands=['today'])	
    dp.register_message_handler(
        dz_handlers.redownload_handler, commands=['re', 'redownload'])
    dp.register_message_handler(
        dz_handlers.artist_search_handler, commands=['a', 'artist'])
    dp.register_message_handler(dz_handlers.diskography_handler, commands=['d'])
    dp.register_message_handler(
        sp_handlers.spotify_album_handler, filters.SpotifyAlbumFilter)
    dp.register_message_handler(
        sp_handlers.spotify_artist_handler, filters.SpotifyArtistFilter)
    dp.register_message_handler(
        sp_handlers.spotify_playlist_handler, filters.SpotifyPlaylistFilter)
    dp.register_message_handler(
        sp_handlers.spotify_handler, filters.SpotifyFilter)
    dp.register_message_handler(
        dz_handlers.artist_handler, filters.DeezerArtistFilter)
    dp.register_message_handler(
        dz_handlers.album_handler, filters.DeezerAlbumFilter)
    dp.register_message_handler(
        dz_handlers.playlist_handler, filters.DeezerPlaylistFilter)
    dp.register_message_handler(
        dz_handlers.track_handler, filters.DeezerFilter)
    dp.register_message_handler(
        handlers.search_handler, lambda m: m.chat.type == 'private')
    dp.register_inline_handler(
        inline_handlers.artist_search_inline_handler,
        lambda q: '.ar' in q.query)
    dp.register_inline_handler(inline_handlers.inline_handler)
    dp.register_callback_query_handler(
        callback_handlers.quality_setting_hanlder,
        lambda d: d.data.startswith('quality'))
    dp.register_callback_query_handler(
        callback_handlers.finish_download_handler,
        lambda d: d.data == 'finish_download')
    dp.register_callback_query_handler(
        callback_handlers.large_file_handler,
        lambda d: 'big_file' in d.data)
    dp.register_callback_query_handler(
        callback_handlers.pages_handler,
        lambda d: 'page' in d.data)
    dp.register_callback_query_handler(
        callback_handlers.stats_callback_handler,
        lambda d: d.data == 'stats')
    dp.register_callback_query_handler(
        callback_handlers.today_stats_callback_handler,
        lambda d: d.data == 'today')
    dp.register_callback_query_handler(
        callback_handlers.sc_artist_callback_handler,
        lambda d: 'sc_artist' in d.data)
    dp.register_callback_query_handler(
        callback_handlers.sc_callback_handler,
        lambda d: 'soundcloud' in d.data)
    dp.register_callback_query_handler(
        callback_handlers.artist_callback_handler,
        lambda d: 'artist' in d.data)
    dp.register_callback_query_handler(callback_handlers.callback_handler)
    dp.register_chosen_inline_handler(inline_handlers.finish_download_handler)
    dp.middleware.setup(Middleware())


try:
    global session
    bot = Bot(token=config.bot_token, loop=loop)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    var.downloading = {}
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

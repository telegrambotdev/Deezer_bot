import re
from asyncio import sleep
from datetime import date
from glob import iglob

import soundcloud.methods as sc_methods
from aiogram import types
from aiogram.dispatcher.handler import SkipHandler
from soundcloud import keyboards as sc_keyboards
from soundcloud import soundcloud_api

import config
import db_utils
import inline_keyboards
import methods
import utils
from bot import bot
from deezer import deezer_api
from deezer import keyboards as dz_keyboards
from logger import error_logger
from var import var


async def only_admin_handler(message: types.Message):
    if message.chat.id in config.admins:
        raise SkipHandler()


async def quality_setting_handler(message: types.Message):
    if message.chat.id in config.admins:
        current_setting = await db_utils.get_quality_setting(message.chat.id)
        return await bot.send_message(
            message.chat.id, 'Select quality',
            reply_markup=inline_keyboards.quality_settings_keyboard(current_setting))


async def soundcloud_link_handler(message: types.Message):
    url = utils.clear_link(message)
    result = await soundcloud_api.resolve(url)
    if result.kind == 'track':
        await sc_methods.send_soundcloud_track(message.chat.id, result)
    elif result.kind == 'user':
        await sc_methods.send_soundcloud_artist(message.chat.id, result)
    elif result.kind == 'playlist':
        await sc_methods.send_soundcloud_playlist(message.chat.id, result)



async def audio_file_handler(message: types.Message):
    if message.caption and message.chat.id in config.admins:
        await db_utils.add_track(int(message.caption), message.audio.file_id)
    else:
        print(message.audio.file_id)


async def start_command_handler(message: types.Message):
    db_utils.add_user(message.from_user)
    await bot.send_message(
        chat_id=message.chat.id,
        text=config.start_message,
        disable_web_page_preview=True,
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=inline_keyboards.start_keyboard)


async def getstats_handler(message):
    sc_tracks_count = await var.conn.execute('get', 'tracks:soundcloud:total')
    dz_tracks_count = await var.conn.execute('get', 'tracks:deezer:total')
    all_users_count = db_utils.get_users_count()
    await bot.send_message(
        chat_id=message.chat.id,
        text=f'users: {all_users_count}\n\n'
            f'Deezer tracks: {dz_tracks_count}\n\nSoundCloud tracks: {sc_tracks_count}',
        reply_markup=inline_keyboards.stats_keyboard)


async def today_stats_handler(message):
    stats = utils.get_today_stats()
    await bot.send_message(
        chat_id=message.chat.id,
        text=f'Downloaded tracks: {stats.downloaded_tracks}\n\n'
        f'Sent tracks: {stats.sent_tracks}\n\n'
        f'Received messages: {stats.received_messages}',
        reply_markup=inline_keyboards.today_stats_keyboard)


async def search_handler(message):
    search_results = await deezer_api.search(q=message.text)
    if not len(search_results):
        await bot.send_message(
            chat_id=message.chat.id,
            text=message.text + ':',
            reply_markup=sc_keyboards.search_results_keyboard(search_results, 1))

    await bot.send_message(
        chat_id=message.chat.id,
        text=message.text + ':',
        reply_markup=dz_keyboards.search_results_keyboard(search_results, 1))
    db_utils.add_user(message.from_user)

from aiogram import types
from aiogram.dispatcher.handler import SkipHandler
from aiogram.dispatcher.filters import Command, CommandStart

import config
import db_utils
import inline_keyboards
import utils
from bot import bot, dp
from deezer import deezer_api, keyboards as dz_keyboards
from soundcloud import soundcloud_api, keyboards as sc_keyboards
from vk import vk_api, keyboards as vk_keyboards
from var import var


@dp.message_handler(content_types=[types.ContentType.AUDIO])
async def audio_file_handler(message: types.Message):
    if message.caption and message.chat.id in config.admins:
        await db_utils.add_track(int(message.caption), message.audio.file_id)
    else:
        print(message.audio.file_id)


@dp.message_handler(CommandStart())
async def start_command_handler(message: types.Message):
    db_utils.add_user(message.from_user)
    await bot.send_message(
        chat_id=message.chat.id,
        text=config.start_message,
        disable_web_page_preview=True,
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=inline_keyboards.start_keyboard)


@dp.message_handler(Command('stats'))
async def getstats_handler(message):
    sc_tracks_count = await var.conn.execute('get', 'tracks:soundcloud:total')
    dz_tracks_count = await var.conn.execute('get', 'tracks:deezer:total')
    all_users_count = db_utils.get_users_count()
    await bot.send_message(
        chat_id=message.chat.id,
        text=f'users: {all_users_count}\n\n'
        f'Deezer tracks: {dz_tracks_count}\n\n'
        f'SoundCloud tracks: {sc_tracks_count}',
        reply_markup=inline_keyboards.stats_keyboard)


@dp.message_handler(Command('today'))
async def today_stats_handler(message):
    stats = utils.get_today_stats()
    await bot.send_message(
        chat_id=message.chat.id,
        text=f'Downloaded tracks: {stats.downloaded_tracks}\n\n'
        f'Sent tracks: {stats.sent_tracks}\n\n'
        f'Received messages: {stats.received_messages}',
        reply_markup=inline_keyboards.today_stats_keyboard)


@dp.message_handler(Command('quality'))
async def quality_setting_handler(message: types.Message):
    if message.chat.id in config.admins or \
            message.chat.id in config.donated_users:
        current = await db_utils.get_quality_setting(message.chat.id)
        return await bot.send_message(
            message.chat.id, 'Select quality (applies only for Deezer)',
            reply_markup=dz_keyboards.quality_settings_keyboard(current))


@dp.message_handler(Command('donate'))
async def donate(message: types.Message):
    return await bot.send_message(
        message.chat.id, config.donate_message, parse_mode='markdown')


@dp.edited_message_handler(types.ChatType.is_private)
@dp.message_handler(types.ChatType.is_private)
async def search_handler(message):
    search_results = await deezer_api.search(message.text)
    if not search_results:
        search_results = await soundcloud_api.search(message.text)
        if not search_results:
            search_results = vk_api.search(message.text)
            return await bot.send_message(
                chat_id=message.chat.id,
                text=message.text + ':',
                reply_markup=vk_keyboards.search_results_keyboard(search_results, 1))
        return await bot.send_message(
            chat_id=message.chat.id,
            text=message.text + ':',
            reply_markup=sc_keyboards.search_results_keyboard(search_results, 1))
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=message.text + ':',
            reply_markup=dz_keyboards.search_results_keyboard(search_results, 1))
    db_utils.add_user(message.from_user)

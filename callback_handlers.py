from contextlib import suppress

from aiogram import exceptions, types
from aiogram.dispatcher.filters import Text

from bot import bot, dp
import utils
import db_utils
from deezer import deezer_api, keyboards as dz_keyboards
from soundcloud import soundcloud_api, keyboards as sc_keyboards
from vk import vk_api, keyboards as vk_keyboards
import inline_keyboards
from utils import parse_callback
from var import var


@dp.callback_query_handler(text='delete')
async def close_keyboard(callback: types.CallbackQuery):
    await callback.answer()
    if callback.message.reply_to_message:
        await callback.message.reply_to_message.delete()
    await callback.message.delete()


@dp.callback_query_handler(text='close')
async def close_keyboard(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_reply_markup()


@dp.callback_query_handler(text='finish_download')
async def finish_download_handler(data):
    await data.answer('please wait, downloading track...', show_alert=True)


@dp.callback_query_handler(Text(startswith='quality'))
async def quality_setting_hanlder(callback):
    _, setting = parse_callback(callback.data)
    await db_utils.set_quality_setting(callback.from_user.id, setting)
    await callback.answer(f'quality set to {setting}')
    with suppress(exceptions.MessageNotModified):
        await bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=dz_keyboards.quality_settings_keyboard(setting))


@dp.callback_query_handler(Text(startswith='page'))
@dp.callback_query_handler(Text(startswith='sc_page'))
@dp.callback_query_handler(Text(startswith='vk_page'))
async def pages_handler(callback):
    mode, page = parse_callback(callback.data)
    q = callback.message.text[:-1]
    await callback.answer()
    if mode == 'page':
        search_results = await deezer_api.search(q=q)
        keyboard = dz_keyboards.search_results_keyboard(
            search_results, int(page), 7)
    elif mode == 'sc_page':
        await callback.answer()
        search_results = await soundcloud_api.search(q=q)
        keyboard = sc_keyboards.search_results_keyboard(
            search_results, int(page), 7)
    elif mode == 'vk_page':
        await callback.answer()
        search_results = await vk_api.search(q)
        keyboard = vk_keyboards.search_results_keyboard(
            search_results, int(page), 7)

    with suppress(exceptions.MessageNotModified):
        return await bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=keyboard)


@dp.callback_query_handler(text='stats')
async def stats_callback_handler(callback):
    await callback.answer()
    sc_tracks_count = await var.conn.execute('get', 'tracks:soundcloud:total')
    dz_tracks_count = await var.conn.execute('get', 'tracks:deezer:total')
    vk_tracks_count = await var.conn.execute('get', 'tracks:vk:total')
    all_users_count = db_utils.get_users_count()
    with suppress(exceptions.MessageNotModified):
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f'users: {all_users_count}\n\n'
            f'Deezer tracks: {dz_tracks_count}\n\n'
            f'SoundCloud tracks: {sc_tracks_count}\n\n'
            f'VK tracks: {vk_tracks_count}',
            reply_markup=inline_keyboards.stats_keyboard)


@dp.callback_query_handler(text='today')
async def today_stats_callback_handler(callback):
    await callback.answer()
    stats = utils.get_today_stats()
    message_text = (
        f'Downloaded tracks: {stats.downloaded_tracks}\n\n'
        f'Sent tracks: {stats.sent_tracks}\n\n'
        f'Received messages: {stats.received_messages}')
    with suppress(exceptions.MessageNotModified):
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=message_text,
            reply_markup=inline_keyboards.today_stats_keyboard)

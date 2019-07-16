from time import time
import shutil

from aiogram import exceptions
from aiogram.utils.markdown import escape_md

import db_utils
from bot import bot
from userbot import post_large_track
from utils import already_downloading, get_album_cover_url
from var import var
from logger import sent_message_logger, format_name
import config

from . import keyboards


async def send_track(track, chat, Redownload=False):
    quality = await db_utils.get_quality_setting(chat.id)
    if not already_downloading(track.id):
        var.downloading[track.id] = int(time())
    else:
        return
    if not Redownload:
        if (await check_and_forward(track, chat, quality)):
            return

    try:
        if quality == 'mp3':
            path = await track.download('MP3_320')
        elif quality == 'flac':
            path = await track.download('FLAC')
    except ValueError as e:
        print(e)
        raise
        return await bot.send_message(
            chat.id,
            f"🚫This track is not available ({track.artist.name} - {track.title})")

    await bot.send_chat_action(chat.id, 'upload_audio')

    thumb = await track.get_thumb()
    await post_large_track(path, track, quality, thumb=thumb)
    file_id = await db_utils.get_track(track.id, quality)
    await bot.send_audio(chat.id, file_id)
    shutil.rmtree(path.rsplit('/', 1)[0])
    var.downloading.pop(track.id)
    sent_message_logger.info(
        f'[send track {track.id} to {format_name(chat)}] {track}')


async def send_album(album, chat, pic=True, send_all=False):
    if pic:
        if not send_all:
            tracks = await album.get_tracks()
            markup = keyboards.album_keyboard(
                album, tracks, chat.id in config.admins)
        else:
            markup = None
        try:
            await bot.send_photo(
                chat.id,
                album.cover_xl,
                caption=f'{escape_md(album.artist.name)} \u2013 {escape_md(album.title)}',
                reply_markup=markup)
        except exceptions.TelegramAPIError:
            await bot.send_photo(
                chat.id,
                await get_album_cover_url(album.id),
                caption=f'{escape_md(album.artist.name)} \u2013 {escape_md(album.title)}',
                reply_markup=markup)
    if send_all:
        for track in await album.get_tracks():
            print(track.title)
            await send_track(track, chat)


async def send_artist(artist, chat_id):
    await bot.send_photo(
        chat_id=chat_id,
        photo=artist.picture_xl,
        caption=f'[{escape_md(artist.name)}]({artist.share})',
        parse_mode='markdown',
        reply_markup=keyboards.artist_keyboard(artist))


async def check_and_forward(track, chat, quality='mp3'):
    file_id = await db_utils.get_track(track.id, quality)
    if not file_id:
        return False
    await bot.send_audio(
        chat_id=chat.id, audio=file_id, title=track.title,
        performer=track.artist.name, duration=track.duration)
    sent_message_logger.info(
        f'[send track {track.id} to {format_name(chat)}] {track}')
    return True


async def cache(track):
    file_id = await db_utils.get_track(track.id)
    if not file_id:
        path = await track.download()
        await post_large_track(path, track)
        shutil.rmtree(path.rsplit('/', 1)[0])
        print(f'cached track {track.artist.name} - {track.title}')
    else:
        print(
            f'skipping track {track.artist.name} - {track.title} - {file_id}')

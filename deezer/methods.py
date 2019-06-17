from asyncio import sleep
from time import time
import os
import shutil

import db_utils
from bot import bot
from userbot import post_large_track
from utils import already_downloading, upload_track
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

    if quality == 'mp3':
        path = await track.download('MP3_320')
    elif quality == 'flac':
        path = await track.download('FLAC')

    await bot.send_chat_action(chat.id, 'upload_audio')

    if (os.path.getsize(path) >> 20) > 50:
        msg = await bot.send_message(
            chat_id=chat.id,
            text='File is larger than 50 MB, uploading can take a while, please wait')
        await post_large_track(path, track, quality)
        await sleep(1)
        file_id = await db_utils.get_track(track.id, quality)
        await bot.send_audio(chat.id, file_id)
        await msg.delete()
    else:
        msg = await upload_track(bot, path, track.title, track.artist.name, track.duration)
        await msg.forward(chat.id)
        await db_utils.add_track(track.id, msg.audio.file_id, quality)
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
        await bot.send_photo(
            chat.id,
            album.cover_xl,
            caption=f'{album["artist"]["name"]} \u2013 {album.title}',
            reply_markup=markup)
    if send_all:
        for track in await album.get_tracks():
            print(track.title)
            await send_track(track, chat)


async def send_artist(artist, chat_id):
    await bot.send_photo(
        chat_id=chat_id,
        photo=artist.picture_xl,
        caption=f'[{artist.name}]({artist.share})',
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
        if (os.path.getsize(path) >> 20) > 50:
            await post_large_track(path, track)
        else:
            msg = await upload_track(bot, path, track.title, track.artist.name, track.duration)
            await db_utils.add_track(track.id, msg.audio.file_id)
        shutil.rmtree(path.rsplit('/', 1)[0])
        print(f'cached track {track.artist.name} - {track.title}')
    else:
        print(
            f'skipping track {track.artist.name} - {track.title} - {file_id}')

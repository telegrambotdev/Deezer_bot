from time import time
import random
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
import server_methods

from . import keyboards


async def send_track(track, chat, Redownload=False):
    quality = await db_utils.get_quality_setting(chat.id)
    if not already_downloading(track.id):
        var.downloading[track.id] = int(time())
    else:
        return
    if not Redownload:
        file_id = await db_utils.get_track(track.id, quality)
        if file_id:
            await bot.send_audio(chat.id, file_id)
            var.downloading.pop(track.id)
            sent_message_logger.info(
                f'[send track {track.id} to {format_name(chat)}] {track}')
            return True

    if chat.id in config.admins or chat.id in config.donated_users \
            or bool(random.randint(0, 5)):
        print(
            f'[Deezer_server] Start downloading: {track.id} |'
            f' {track.artist.name} - {track.title} ')
        await server_methods.send_track(track, chat.id)
        var.downloading.pop(track.id)
        print(
            f'[Deezer_server] Finished downloading: {track.id} '
            f'| {track.artist.name} - {track.title} ')
        sent_message_logger.info(
            f'[send track {track.id} to {format_name(chat)}] {track}')
        return True

    try:
        if quality == 'mp3':
            path = await track.download('MP3_320')
        elif quality == 'flac':
            path = await track.download('FLAC')
    except ValueError as e:
        print(e)
        return await bot.send_message(
            chat.id,
            ("🚫This track is not available "
             f"({track.artist.name} - {track.title})"))

    await bot.send_chat_action(chat.id, 'upload_audio')

    thumb = await track.get_thumb()
    await post_large_track(path, track, quality, thumb=thumb)
    file_id = await db_utils.get_track(track.id, quality)
    await bot.send_audio(chat.id, file_id)
    shutil.rmtree(path.rsplit('/', 1)[0])
    var.downloading.pop(track.id)
    sent_message_logger.info(
        f'[send track {track.id} to {format_name(chat)}] {track}')
    return True


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
                caption=(f'{escape_md(album.artist.name)} '
                         f'\u2013 {escape_md(album.title)}'),
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


async def send_playlist(playlist, tracks, chat_id):
    try:
        await bot.send_photo(
            chat_id=chat_id, photo=playlist.picture_xl, caption=playlist.title,
            reply_markup=keyboards.playlist_keyboard(tracks, playlist.id))
    except exceptions.TelegramAPIError:
        await bot.send_photo(
            chat_id=chat_id,
            photo='AgADBAADjKkxG2SUZVFzIAqSalXHJZnn-RkABIP8pp76pJdTqbwFAAEC',
            caption=playlist.title,
            reply_markup=keyboards.playlist_keyboard(tracks, playlist.id))


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

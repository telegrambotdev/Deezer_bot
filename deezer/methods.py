from aiogram import exceptions
from aiogram.utils.markdown import escape_md

from var import bot
from utils import get_album_cover_url
from var import var
import db_utils
import config

from . import keyboards


async def send_track(chat_id, track, Redownload=False):
    quality = await db_utils.get_quality_setting(chat_id)
    file_id = await db_utils.get_track(track.id, quality)
    if file_id:
        return await bot.send_audio(chat_id, file_id)
    await var.session.post(
        'http://localhost:8082/deezer/send.track',
        json={'track': track.data, 'chat_id': chat_id})


async def send_album(chat_id, album, pic=True, send_all=False):
    if pic:
        if not send_all:
            tracks = await album.get_tracks()
            markup = keyboards.album_keyboard(
                album, tracks, chat_id in config.admins)
        else:
            markup = None
        try:
            await bot.send_photo(
                chat_id,
                album.cover_xl,
                caption=f'{escape_md(album.artist.name)} \u2013 {escape_md(album.title)}',
                reply_markup=markup)
        except exceptions.TelegramAPIError:
            await bot.send_photo(
                chat_id,
                await get_album_cover_url(album.id),
                caption=(f'{escape_md(album.artist.name)} '
                         f'\u2013 {escape_md(album.title)}'),
                reply_markup=markup)
    if send_all:
        tracks = await album.get_tracks()
        await var.session.post(
            'http://localhost:8082/deezer/send.tracks',
            json={
                'tracks': [track.data for track in tracks],
                'chat_id': chat_id})


async def send_artist(chat_id, artist):
    await bot.send_photo(
        chat_id=chat_id,
        photo=artist.picture_xl,
        caption=f'[{escape_md(artist.name)}]({artist.share})',
        parse_mode='markdown',
        reply_markup=keyboards.artist_keyboard(artist))


async def send_playlist(chat_id, playlist, tracks):
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

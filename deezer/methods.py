from aiorgam import exceptions
from aiogram.utils.markdown import escape_md

from bot import bot
from utils import get_album_cover_url
from var import var
import config

from . import keyboards


async def send_track(track, chat_id, Redownload=False):
    var.session.post(
        'localhost:8082/deezer/send.track', json={
            'track_id': track.id, 'chat_id': chat_id
        })


async def send_album(album, chat_id, pic=True, send_all=False):
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
        var.session.post(
            'localhost:8082/deezer/send.album', json={
                'album_id': album.id, 'chat_id': chat_id
            })


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

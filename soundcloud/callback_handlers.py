from asyncio import sleep

from aiogram.dispatcher.filters import Text

from . import soundcloud_api
from . import keyboards
from . import methods
from bot import bot, dp
from utils import parse_callback, already_downloading


@dp.callback_query_handler(Text(startswith='sc_artist'))
async def soundcloud_artist(callback):
    await callback.answer()
    _, obj_id, method = parse_callback(callback.data)
    artist = await soundcloud_api.get_artist(obj_id)

    if method == 'main':
        keyboard = keyboards.artist_keyboard(artist)

    elif method == 'tracks':
        tracks = await artist.get_tracks()
        keyboard = keyboards.artist_tracks_keyboard(tracks, artist.id)

    elif method == 'playlists':
        playlists = await artist.get_playlists()
        keyboard = keyboards.artist_playlists_keyboard(playlists, artist.id)

    elif method == 'likes':
        likes = await artist.get_likes()
        keyboard = keyboards.likes_keyboard(likes, artist.id)

    elif method == 'download':
        tracks = await artist.get_tracks()
        for track in tracks:
            await methods.send_soundcloud_track(
                callback.message.chat.id, track)
            await sleep(.3)
        return

    elif method == 'likes_download':
        likes = await artist.get_likes()
        for track in tracks:
            await methods.send_soundcloud_track(
                callback.message.chat.id, track)
            await sleep(.3)
        return

    return await bot.edit_message_reply_markup(
        callback.message.chat.id,
        callback.message.message_id,
        reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='sc_playlist'))
async def soundcloud_playlist(callback):
    await callback.answer()
    _, obj_id, method = parse_callback(callback.data)
    playlist = await soundcloud_api.get_playlist(obj_id)

    if method == 'send':
        return await methods.send_soundcloud_playlist(
            callback.message.chat.id, playlist)

    elif method == 'download':
        return await methods.send_soundcloud_playlist(
            callback.message.chat.id, playlist, pic=False, send_all=True)

    elif method == 'post':
        return await methods.send_soundcloud_playlist(
            -1001171972924, playlist, send_all=True)


@dp.callback_query_handler(Text(startswith='sc_track'))
async def soundcloud_track(callback):
    await callback.answer()
    _, obj_id, method = parse_callback(callback.data)

    if already_downloading(int(obj_id)):
        return await callback.answer('already downloading, please wait...')
    else:
        await callback.answer('downloading...')
        track = await soundcloud_api.get_track(obj_id)
        await methods.send_soundcloud_track(
            callback.message.chat.id, track)

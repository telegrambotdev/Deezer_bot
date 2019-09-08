from contextlib import suppress

from aiogram import exceptions
from aiogram.dispatcher.filters import Text

from . import deezer_api, keyboards, methods
from bot import bot, dp
from utils import parse_callback, already_downloading, query_answer
from var import var


@dp.callback_query_handler(Text(startswith='dz_playlist'))
async def deezer_playlist(callback):
    _, obj_id, method = parse_callback(callback.data)
    if method == 'download':
        with suppress(exceptions.MessageNotModified):
            await callback.message.edit_reply_markup()
        await query_answer(
            callback, 'Playlist download started', show_alert=True)
        tracks = await deezer_api.getplaylist_tracks(obj_id)
        await var.session.post(
            'http://localhost:8082/deezer/send.tracks',
            json={'tracks': [track.data for track in tracks], 'chat_id': callback.message.chat.id})


@dp.callback_query_handler(Text(startswith='dz_artist'))
async def deezer_artist(callback):
    await query_answer(callback)
    _, obj_id, method = parse_callback(callback.data)

    artist = await deezer_api.getartist(obj_id)
    if method == 'top10':
        top = await artist.top(10)
        keyboard = keyboards.top10_keyboard(artist, top)

    elif method == 'albums':
        albums = await artist.albums()
        keyboard = keyboards.albums_keyboard(artist, albums)

    elif method == 'related':
        related = await artist.related()
        keyboard = keyboards.related_artists_keyboard(related, artist.id)

    elif method == 'radio':
        radio = await artist.radio()
        keyboard = keyboards.artist_radio_keyboard(radio, artist.id)

    elif method == 'main':
        keyboard = keyboards.artist_keyboard(artist)

    elif method == 'send':
        return await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=artist.picture_xl,
            caption=f'[{artist.name}]({artist.share})',
            parse_mode='markdown',
            reply_markup=keyboards.artist_keyboard(artist))

    elif method == 'wiki':
        artist = await deezer_api.getartist(obj_id)
        r = await bot.session.get(
            f'https://wikipedia.org/w/index.php?search={artist.name}')
        return await bot.send_message(
            callback.message.chat.id, r.url)

    return await bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith='dz_album'))
async def deezer_album(callback):
    _, obj_id, method = parse_callback(callback.data)

    if method == 'download':
        await query_answer(callback)
        album = await deezer_api.getalbum(obj_id)
        return await methods.send_album(
            callback.message.chat.id, album, pic=False, send_all=True)

    elif method == 'post':
        await query_answer(callback)
        album = await deezer_api.getalbum(obj_id)
        await methods.send_album(-1001171972924, album, send_all=True)

    elif method == 'send':
        await query_answer(callback, 'downloading')
        album = await deezer_api.getalbum(obj_id)
        return await methods.send_album(callback.message.chat.id, album)


@dp.callback_query_handler(Text(startswith='dz_track'))
async def deezer_track(callback):
    obj_id = parse_callback(callback.data)[1]
    if already_downloading(int(obj_id)):
        return await query_answer(callback, 'already downloading, please wait...')
    else:
        await query_answer(callback, 'downloading...')
        track = await deezer_api.gettrack(obj_id)
        await methods.send_track(callback.message.chat.id, track)

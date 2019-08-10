from asyncio import sleep
from contextlib import suppress

from aiogram import exceptions
from aiogram.dispatcher.filters import Text

from . import deezer_api, keyboards, methods
from bot import bot, dp
from utils import parse_callback, already_downloading
from var import var


@dp.callback_query_handler(Text(startswith='dz_playlist'))
async def deezer_playlist(callback):
    _, obj_id, method = parse_callback(callback.data)
    if method == 'download':
        with suppress(exceptions.MessageNotModified):
            await callback.message.edit_reply_markup()
        await callback.answer('Playlist download started', show_alert=True)
        var.session.post(
            'localhost:8082/deezer/send.playlist', json={
                'playlist_id': obj_id, 'chat_id': callback.message.chat.id
            })


@dp.callback_query_handler(Text(startswith='dz_artist'))
async def deezer_artist(callback):
    await callback.answer()
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
        await callback.answer()
        album = await deezer_api.getalbum(obj_id)
        return await methods.send_album(
            album, callback.message.chat, pic=False, send_all=True)

    elif method == 'post':
        await callback.answer()
        album = await deezer_api.getalbum(obj_id)
        chat = await bot.get_chat(-1001171972924)
        await methods.send_album(album, chat, send_all=True)

    elif method == 'send':
        await callback.answer('downloading')
        album = await deezer_api.getalbum(obj_id)
        return await methods.send_album(album, callback.message.chat)


@dp.callback_query_handler(Text(startswith='dz_track'))
async def deezer_track(callback):
    obj_id = parse_callback(callback.data)[1]
    if already_downloading(int(obj_id)):
        return await callback.answer('already downloading, please wait...')
    else:
        await callback.answer('downloading...')
        track = await deezer_api.gettrack(obj_id)
        await methods.send_track(track, callback.message.chat.id)

import asyncio

from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.webhook import SendMessage

from bot import dp, bot
from AttrDict import AttrDict
from deezer import methods
from genius import genius_api
from .keyboards import current_track_keyboard, auth_keyboard
from . import spotify_api
from utils import query_answer, request_get, request_post, \
    print_traceback, split_string


@dp.callback_query_handler(Text(startswith='spotify:download_track'))
async def download_track(query: types.CallbackQuery):
    await query_answer(query)
    track_id = query.data.split(':')[2]
    track = await spotify_api.match_track(track_id)
    if track:
        await methods.send_track(query.message.chat.id, track)
    else:
        return SendMessage(
            query.message.chat.id,
            'Track is not found on Deezer, try manual search')


@dp.callback_query_handler(Text(startswith='spotify:album'))
async def get_album(query: types.CallbackQuery):
    await query_answer(query)
    album_id = query.data.split(':')[2]
    album = await spotify_api.match_album(album_id)
    if album:
        await methods.send_album(query.message.chat.id, album)
    else:
        return SendMessage(
            query.message.chat.id,
            'Album is not found on Deezer, try manual search')


@dp.callback_query_handler(Text(startswith='spotify:artist'))
async def get_artist(query: types.CallbackQuery):
    await query_answer(query)
    artist_id = query.data.split(':')[2]
    artist = await spotify_api.match_artist(artist_id)
    if artist:
        await methods.send_artist(query.message.chat.id, artist)
    else:
        return SendMessage(
            query.message.chat.id,
            'Artist is not found on Deezer, try manual search')


@dp.callback_query_handler(Text(startswith='spotify:lyrics'))
async def get_lyrics(query: types.CallbackQuery):
    await query_answer(query)
    track_id = query.data.split(':')[2]
    result = await genius_api.spotify_match(track_id)

    if not result:
        return SendMessage(
            query.message.chat.id,
            f'Didn\'t found lyrics for this song',
            reply_to_message_id=query.message.message_id)

    for text in split_string(await result.get_lyrics()):
        await bot.send_message(query.message.chat.id, text)


@dp.callback_query_handler(text='spotify:update_current')
async def update_current(query: types.CallbackQuery):
    await query_answer(query)
    token = await spotify_api.get_token(query.from_user.id)
    if not token:
        return SendMessage(
            query.from_user.id, 'Please authorize',
            reply_markup=auth_keyboard(query.from_user.id))
    req = await request_get(
        'https://api.spotify.com/v1/me/player/currently-playing',
        headers={'Authorization': f'Bearer {token}'})
    try:
        json = await req.json()
        track = AttrDict(json['item'])
    except Exception as e:
        print_traceback(e)
        return SendMessage(
            query.message.chat.id,
            f'Play something in Spotify and try again',
            reply_to_message_id=query.message.message_id)

    await bot.edit_message_text(
        text='Currently playing track:\n' +
        f'{track.artists[0].name} - {track.name}'
        f'<a href="{track.album.images[0].url}">&#8203;</a>',
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        reply_markup=current_track_keyboard(track), parse_mode='HTML')


@dp.callback_query_handler(text='spotify:previous_track')
async def previous_track(query: types.CallbackQuery):
    await query_answer(query)
    token = await spotify_api.get_token(query.from_user.id)
    if not token:
        return SendMessage(
            query.from_user.id, 'Please authorize',
            reply_markup=auth_keyboard(query.from_user.id))

    await request_post(
        'https://api.spotify.com/v1/me/player/previous',
        headers={'Authorization': f'Bearer {token}'})

    await asyncio.sleep(.7)
    req = await request_get(
        'https://api.spotify.com/v1/me/player/currently-playing',
        headers={'Authorization': f'Bearer {token}'})
    try:
        json = await req.json()
        track = AttrDict(json['item'])
    except Exception as e:
        print_traceback(e)
        return SendMessage(
            query.message.chat.id,
            f'Play something in Spotify and try again',
            reply_to_message_id=query.message.message_id)

    await bot.edit_message_text(
        text='Currently playing track:\n' +
        f'{track.artists[0].name} - {track.name}'
        f'<a href="{track.album.images[0].url}">&#8203;</a>',
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        reply_markup=current_track_keyboard(track), parse_mode='HTML')


@dp.callback_query_handler(text='spotify:next_track')
async def next_track(query: types.CallbackQuery):
    await query_answer(query)
    token = await spotify_api.get_token(query.from_user.id)
    if not token:
        return SendMessage(
            query.from_user.id, 'Please authorize',
            reply_markup=auth_keyboard(query.from_user.id))

    await request_post(
        'https://api.spotify.com/v1/me/player/next',
        headers={'Authorization': f'Bearer {token}'})

    await asyncio.sleep(.7)
    req = await request_get(
        'https://api.spotify.com/v1/me/player/currently-playing',
        headers={'Authorization': f'Bearer {token}'})
    try:
        json = await req.json()
        track = AttrDict(json['item'])
    except Exception as e:
        print_traceback(e)
        return SendMessage(
            query.message.chat.id,
            f'Play something in Spotify and try again',
            reply_to_message_id=query.message.message_id)

    await bot.edit_message_text(
        text='Currently playing track:\n' +
        f'{track.artists[0].name} - {track.name}'
        f'<a href="{track.album.images[0].url}">&#8203;</a>',
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        reply_markup=current_track_keyboard(track), parse_mode='HTML')

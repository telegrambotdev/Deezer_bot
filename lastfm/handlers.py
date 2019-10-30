from time import time

from aiogram import types
from aiogram.dispatcher.webhook import SendMessage

from bot import dp
from db_utils import unset_lastfm_token, get_lastfm_token
from .keyboards import auth_keyboard
from .lastfm_api import api_request


@dp.message_handler(commands='lastfm_logout')
async def logout(message: types.Message):
    await unset_lastfm_token(message.from_user.id)
    return SendMessage(
        message.from_user.id, 'you are succesfully logged out from Last.fm')


@dp.message_handler(commands='lastfm_scrobble')
async def scrobble(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        return SendMessage(message.chat.id, 'Reply to a song')
    sk = await get_lastfm_token(message.from_user.id)
    if not sk:
        return SendMessage(
            message.chat.id, 'Please authorize',
            reply_markup=auth_keyboard(message.from_user.id))

    track = message.reply_to_message.audio
    resp = await api_request(
        'POST', 'track.scrobble', artist=track.performer,
        track=track.title, timestamp=int(time()), sk=sk)

    scrobble = resp.scrobbles.scrobble

    return SendMessage(
        message.chat.id,
        f"{scrobble.artist['#text']} - {scrobble.track['#text']} scrobbled")


@dp.message_handler(commands='lastfm_love')
async def love(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        return SendMessage(message.chat.id, 'Reply to a song')
    sk = await get_lastfm_token(message.from_user.id)
    if not sk:
        print('nosk')
        return SendMessage(
            message.chat.id, 'Please authorize',
            reply_markup=auth_keyboard(message.from_user.id))

    track = message.reply_to_message.audio
    resp = await api_request(
        'POST', 'track.love', artist=track.performer,
        track=track.title, sk=sk)

    return SendMessage(
        message.chat.id,
        f'{track.performer} - {track.title} loved on your account')

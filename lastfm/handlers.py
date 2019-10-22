from time import time
from pprint import pformat

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
        'track.scrobble', artist=track.performer,
        track=track.title, timestamp=int(time()), sk=sk)

    return SendMessage(message.chat.id, pformat(resp.data))


@dp.message_handler(commands='lastfm_love')
async def love(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        return SendMessage(message.chat.id, 'Reply to a song')
    sk = await get_lastfm_token(message.from_user.id)
    if not sk:
        return SendMessage(
            message.chat.id, 'Please authorize',
            reply_markup=auth_keyboard(message.from_user.id))

    print(sk)

    track = message.reply_to_message.audio
    resp = await api_request(
        'track.love', artist=track.performer, track=track.title, sk=sk)
    print(resp)

    return SendMessage(message.chat.id, pformat(resp.data))

from time import time
from pprint import pformat

from aiogram import types
from aiogram.dispatcher.webhook import SendMessage

from bot import dp
from db_utils import unset_lastfm_token, get_lastfm_token
from .lastfm_api import api_request


@dp.message_handler(commands='lastfm_logout')
async def logout(message: types.Message):
    await unset_lastfm_token(message.from_user.id)


@dp.message_handler(commands='lastfm_scrobble')
async def scrobble(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        return SendMessage(message.chat.id, 'Reply to a song')

    track = message.reply_to_message.audio
    resp = await api_request(
        'track.scrobble', artist=track.performer,
        track=track.title, timestamp=int(time()),
        sk=await get_lastfm_token(message.from_user.id))

    return SendMessage(message.chat.id, pformat(resp.data))


@dp.message_handler(commands='lastfm_love')
async def love(message: types.Message):
    if not message.reply_to_message or not message.reply_to_message.audio:
        return SendMessage(message.chat.id, 'Reply to a song')

    track = message.reply_to_message.audio
    resp = await api_request(
        'track.love', artist=track.performer, track=track.title,
        sk=await get_lastfm_token(message.from_user.id))

    return SendMessage(message.chat.id, pformat(resp.data))

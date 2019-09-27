from aiogram import types
from aiogram.dispatcher.filters import Text

from bot import dp, bot
import utils
from . import soundcloud_api
from . import methods


@dp.message_handler(Text(contains='soundcloud.com/'))
@dp.channel_post_handler(Text(contains='soundcloud.com/'))
async def soundcloud_link_handler(message: types.Message):
    url = utils.clear_link(message)
    try:
        result = await soundcloud_api.resolve(url)
    except ValueError:
        await bot.send_message(
            message.chat.id, '🚫 this item is not available')
    if result.kind == 'track':
        await methods.send_track(message.chat.id, result)
    elif result.kind == 'user':
        await methods.send_artist(message.chat.id, result)
    elif result.kind == 'playlist':
        await methods.send_playlist(message.chat.id, result)

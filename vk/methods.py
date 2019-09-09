import shutil
from aiogram.utils.markdown import escape_md

from bot import bot
from time import time
import db_utils
from userbot import post_large_track
from var import var
from utils import already_downloading
from . import keyboards
import config


async def send_track(chat_id, track):
    if not already_downloading(track.full_id):
        var.downloading[track.full_id] = int(time())
    else:
        return
    file_id = await db_utils.get_vk_track(track.full_id)
    if file_id:
        return await bot.send_audio(chat_id, file_id)

    return await var.session.post(
        'http://localhost:8082/vk/send.track',
        json={'track': track.data, 'chat_id': chat_id})


async def send_playlist(chat_id, playlist, pic=True, send_all=False):
    if pic:
        if not send_all:
            markup = keyboards.playlist_keyboard(
                playlist,
                show_artists=not hasattr(playlist, 'access_key'),
                post=chat_id in config.admins)
        else:
            markup = None
        try:
            await bot.send_photo(
                chat_id,
                playlist.photo['photo_600'],
                caption=f'{escape_md(playlist.title)}',
                reply_markup=markup)
        except Exception:
            await bot.send_photo(
                chat_id,
                'AgADBAADjKkxG2SUZVFzIAqSalXHJZnn-RkABIP8pp76pJdTqbwFAAEC',
                caption=f'{escape_md(playlist.title)}',
                reply_markup=markup)
            raise

    if send_all:
        return await var.session.post(
            'http://localhost:8082/vk/send.playlist',
            json={'playlist': playlist.data, 'chat_id': chat_id})

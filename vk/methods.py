import shutil
from aiogram.utils.markdown import escape_md

from bot import bot
from time import time
import db_utils
from userbot import post_large_track
from var import var
from utils import already_downloading
from . import keyboards


async def send_track(chat_id, track):
    if not already_downloading(track.id):
        var.downloading[track.id] = int(time())
    else:
        return
    file_id = await db_utils.get_vk_track(track.full_id)
    if file_id:
        return await bot.send_audio(chat_id, file_id)
    path = await track.download()
    await bot.send_chat_action(chat_id, 'upload_audio')
    await post_large_track(path, track, provider='vk')
    file_id = await db_utils.get_vk_track(track.full_id)
    await bot.send_audio(chat_id, file_id)
    shutil.rmtree(path.rsplit('/', 1)[0])
    var.downloading.pop(track.id)


async def send_playlist(chat_id, playlist, pic=True, send_all=False):
    if pic:
        if not send_all:
            markup = keyboards.playlist_keyboard()
        else:
            markup = None
        await bot.send_photo(
            chat_id,
            playlist.thumb.photo_600,
            caption=f'{escape_md(playlist.title)}',
            reply_markup=markup)
    if send_all:
        for track in playlist:
            print(track.title)
            await send_track(chat_id, track)

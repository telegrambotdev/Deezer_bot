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
    path = await track.download()
    thumb = await track.get_thumb()
    await bot.send_chat_action(chat_id, 'upload_audio')
    await post_large_track(path, track, provider='vk', thumb=thumb)
    file_id = await db_utils.get_vk_track(track.full_id)
    await bot.send_audio(chat_id, file_id)
    shutil.rmtree(path.rsplit('/', 1)[0])
    var.downloading.pop(track.full_id, None)
    var.vk_tracks.pop(track.full_id, None)


async def send_playlist(chat_id, playlist):
    if send_all:
        for track in playlist.tracks:
            print(track.title)
            await send_track(chat_id, track)

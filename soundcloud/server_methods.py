import os
import shutil
import traceback

from aiogram.types import InputFile

from bot import bot
from userbot import post_large_track
from utils import calling_queue
import db_utils


@calling_queue(4)
async def send_track(chat_id, track):
    path = await track.download()
    thumb = await track.get_thumb()
    if os.path.getsize(path) >> 20 < 49:
        msg = await bot.send_audio(
            chat_id=chat_id, audio=InputFile(path), thumb=thumb,
            performer=track.artist, title=track.title)
        file_id = msg.audio.file_id
    else:
        file_id = await post_large_track()
    await db_utils.add_sc_track(track.id, file_id)
    shutil.rmtree(path.rsplit('/', 1)[0])
    await bot.send_audio(-1001246220493, file_id)


async def send_tracks(chat_id, tracks):
    for track in tracks:
        try:
            await send_track(chat_id, track)
        except Exception as exc:
            print('didnt send sc track', exc)
            print(''.join(traceback.format_tb(exc.__traceback__)))
            await bot.send_message(
                chat_id,
                '🚫This track is not available '
                f'{track.artist} - {track.title}')

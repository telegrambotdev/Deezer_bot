import os
import shutil
import traceback
import asyncio
from io import BytesIO

from aiogram.types import InputFile

from bot import bot
from userbot import post_large_track
from utils import calling_queue, delete_later
import db_utils


@calling_queue(4)
async def send_track(chat_id, track):
    try:
        stream = await track.download()
        thumb = await track.get_thumb()
        if thumb:
            thumb = InputFile(BytesIO(thumb), filename='thumb.jpg')
        filename = f"{track.artist} - {track.title}.mp3".replace('/', '_')
    except ValueError:
        await bot.send_message(
            chat_id,
            "🚫This track is not available "
            f"({track.artist} - {track.title})")
        raise

    msg = await bot.send_audio(
        chat_id=-1001246220493,
        audio=InputFile(stream, filename=filename),
        thumb=thumb, performer=track.artist, title=track.title)
    file_id = msg.audio.file_id
    await db_utils.add_sc_track(track.id, file_id)
    await bot.send_audio(chat_id, file_id)


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

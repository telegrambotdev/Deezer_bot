import asyncio
import json
import os
import shutil
from asyncio import sleep
from time import time
from io import BytesIO

from aiogram import exceptions, types
from aiogram.types import InputFile

import config
import db_utils
import deezer.keyboards as dz_keyboards
import inline_keyboards
from bot import bot
from logger import file_download_logger, format_name, sent_message_logger
from userbot import post_large_track
from utils import already_downloading, calling_queue, get_file
from var import var


async def finish_download(track, inline_message_id, user):
    file_id = await db_utils.get_track(track.id)
    if file_id:
        return await bot.edit_message_media(
            media=types.InputMediaAudio(
                media=file_id,
                title=track.title,
                performer=track.artist.name,
                duration=track.duration),
            inline_message_id=inline_message_id)
    try:
        track_file = await track.download()
        thumb = await track.get_thumb()
        if thumb:
            thumb = BytesIO(thumb)
        filename = f"{track.artist.name} - {track.title}.mp3".replace('/', '_')
    except ValueError:
        return await bot.edit_message_reply_markup(
            inline_message_id=inline_message_id,
            reply_markup=inline_keyboards.download_error_keyboard)
    msg = await bot.send_audio(
        chat_id=-1001246220493,
        audio=InputFile(track_file, filename=filename),
        thumb=InputFile(thumb, filename='thumb.jpg'),
        performer=track.artist.name,
        title=track.title, duration=track.duration)
    file_id = msg.audio.file_id
    await db_utils.add_track(track.id, file_id)
    file_id = await db_utils.get_track(track.id)

    try:
        await bot.edit_message_media(
            media=types.InputMediaAudio(
                media=file_id,
                title=track.title,
                performer=track.artist.name,
                duration=track.duration),
            inline_message_id=inline_message_id)
    except exceptions.BadRequest:
        try:
            await bot.send_audio(user.id, file_id)
        except:
            pass

    file_download_logger.info(
        f'[downloaded track {track.id} (inline)] {track}')
    sent_message_logger.info(
        f'[send track {track.id} to {format_name(user)} (inline)] {track}')

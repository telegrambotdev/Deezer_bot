import asyncio
import json
import os
import shutil
from asyncio import sleep
from time import time

from aiogram import exceptions, types

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
        path = await track.download()
    except ValueError:
        return await bot.edit_message_reply_markup(
            inline_message_id=inline_message_id,
            reply_markup=inline_keyboards.download_error_keyboard)
    await post_large_track(path, track)
    file_id = await db_utils.get_track(track.id)

    try:
        await bot.edit_message_media(
            media=types.InputMediaAudio(
                media=file_id,
                title=track.title,
                performer=track.artist.name,
                duration=track.duration),
            inline_message_id=inline_message_id)
        shutil.rmtree(path.rsplit('/', 1)[0])
    except exceptions.BadRequest:
        try:
            await bot.send_audio(user.id, file_id)
        except:
            pass

    file_download_logger.info(
        f'[downloaded track {track.id} (inline)] {track}')
    sent_message_logger.info(
        f'[send track {track.id} to {format_name(user)} (inline)] {track}')

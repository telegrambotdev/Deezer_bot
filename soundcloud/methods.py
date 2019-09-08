import shutil

from aiogram import exceptions

import config
import db_utils
from bot import bot
from userbot import post_large_track
from var import var

from . import keyboards


async def send_track(chat_id, track):
    file_id = await db_utils.get_sc_track(track.id)
    if file_id:
        return await bot.send_audio(chat_id, file_id)

    return await var.session.post(
        'http://localhost:8082/soundcloud/send.track',
        json={'track': track, 'chat_id': chat_id})

    path = await track.download()
    thumb = await track.get_thumb()
    await post_large_track(path, track, provider='soundcloud', thumb=thumb)
    file_id = await db_utils.get_sc_track(track.id)
    await bot.send_audio(chat_id, file_id)
    shutil.rmtree(path.rsplit('/', 1)[0])


async def send_artist(chat_id, artist):
    await bot.send_photo(
        chat_id=chat_id,
        photo=artist.avatar_url,
        caption=f'[{artist.username}]({artist.permalink_url})',
        parse_mode='markdown',
        reply_markup=keyboards.artist_keyboard(artist))


async def send_playlist(chat_id, playlist, pic=True, send_all=False):
    if pic:
        if not send_all:
            markup = keyboards.playlist_keyboard(
                playlist, chat_id in config.admins)
        else:
            markup = None
        try:
            await bot.send_photo(
                chat_id, playlist.artwork_url, reply_markup=markup,
                caption=f'{playlist.user.username} \u2013 {playlist.title}')
        except exceptions.BadRequest:
            await bot.send_photo(
                chat_id, playlist.tracks[0].artwork_url, reply_markup=markup,
                caption=f'{playlist.user.username} \u2013 {playlist.title}')
    if send_all:

        await var.session.post(
            'http://localhost:8082/soundcloud/send.tracks',
            json={'tracks': playlist.tracks, 'chat_id': chat_id})

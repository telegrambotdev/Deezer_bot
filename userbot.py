import sys
import asyncio

import pyrogram
from pyrogram.errors.exceptions import FloodWait

import config
import db_utils


async def start():
    app_name = sys.argv[0] if sys.argv else 'interactive'
    client = pyrogram.Client(
        f"{app_name}_Bot_{config.bot_token.split(':')[0]}",
        api_id=config.client_api_id,
        api_hash=config.client_api_hash, bot_token=config.bot_token)
    await client.start()
    return client


async def upload(path, attrs):
    timeout = int(attrs.get('duration', 3600)) / 60
    try:
        msg = await asyncio.wait_for(
            client.send_audio(-1001246220493, path, **attrs), timeout)
    except FloodWait as exc:
        await asyncio.sleep(exc.x + 1)
        return await upload(path, attrs)
    return msg.audio.file_id


async def post_large_track(
        path, track, quality='mp3', provider='deezer', thumb=None):
    if provider == 'deezer':
        attrs = {
            'duration': track.duration,
            'title': track.title,
            'performer': track.artist.name,
            'thumb': thumb
        }
        file_id = await upload(path, attrs)
        await db_utils.add_track(track.id, file_id, quality)

    elif provider == 'soundcloud':
        attrs = {
            'duration': track.duration,
            'title': track.title,
            'performer': track.artist,
            'thumb': thumb
        }
        file_id = await upload(path, attrs)
        await db_utils.add_sc_track(track.id, file_id)

    elif provider == 'vk':
        attrs = {
            'duration': track.duration,
            'title': track.title,
            'performer': track.artist,
            'thumb': thumb
        }
        file_id = await upload(path, attrs)
        await db_utils.add_vk_track(track.full_id, file_id)
    else:
        raise ValueError(f'wrong provider: {provider}')


client = asyncio.get_event_loop().run_until_complete(start())

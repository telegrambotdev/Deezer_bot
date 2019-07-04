import asyncio


import pyrogram

import config
import db_utils


loop = asyncio.get_event_loop()


async def start():
    client = pyrogram.Client(
        f"Bot_{config.bot_token.split(':')[0]}",
        api_id=config.client_api_id,
        api_hash=config.client_api_hash, bot_token=config.bot_token)
    await client.start()
    return client


async def post_large_track(path, track, quality='mp3', provider='deezer'):
    if provider == 'deezer':
        msg = await client.send_audio(
            chat_id=-1001246220493, audio=path, duration=track.duration,
            title=track.title, performer=track.artist.name)
        await db_utils.add_track(track.id, msg.audio.file_id, quality)
    elif provider == 'soundcloud':
        msg = await client.send_audio(
            chat_id=-1001246220493, audio=path, duration=track.duration,
            title=track.title, performer=track.artist)
        await db_utils.add_sc_track(track.id, msg.audio.file_id)
    elif provider == 'vk':
        msg = await client.send_audio(
            chat_id=-1001246220493, audio=path, duration=track.duration,
            title=track.title, performer=track.artist)
        await db_utils.add_vk_track(track.full_id, msg.audio.file_id)
    else:
        raise ValueError(f'wrong provider: {provider}')


client = loop.run_until_complete(start())

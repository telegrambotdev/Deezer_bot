import shutil

from bot import bot
import db_utils
from userbot import post_large_track
from var import var
from utils import already_downloading, calling_queue, launch_with_timeout


@calling_queue(4)
async def send_track(chat_id, track):
    try:
        path = await track.download()
        thumb = await track.get_thumb()
    except ValueError:
        await bot.send_message(
            chat_id,
            "🚫This track is not available "
            f"({track.artist} - {track.title})")
        raise

    await bot.send_chat_action(chat_id, 'upload_audio')
    await post_large_track(path, track, provider='vk', thumb=thumb)
    file_id = await db_utils.get_vk_track(track.full_id)
    await bot.send_audio(chat_id, file_id)
    shutil.rmtree(path.rsplit('/', 1)[0])
    var.downloading.pop(track.full_id, None)
    var.vk_tracks.pop(track.full_id, None)


async def send_playlist(chat_id, playlist):
    for track in playlist.tracks:
        print(track.title)
        await send_track(chat_id, track)

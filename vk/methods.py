from bot import bot
import db_utils
from userbot import post_large_track


async def send_track(chat_id, track):
    file_id = await db_utils.get_vk_track(track.full_id)
    if file_id:
        return await bot.send_audio(chat_id, file_id)
    path = await track.download()
    await post_large_track(path, track, provider='vk')

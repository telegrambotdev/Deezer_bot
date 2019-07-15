from bot import bot, dp
import filters
from . import methods
from . import vk_api
from . import keyboards


@dp.message_handler(filters.VKPlaylistFilter)
async def playlist_handler(message, owner_id, playlist_id, access_key):
    playlist = await vk_api.get_playlist(owner_id, playlist_id, access_key)
    await methods.send_playlist(message.chat.id, playlist)


@dp.message_handler(filters.VKProfileFilter)
async def profile_handler(message, profile_id, profile_nickname):
    profile_id = await vk_api.get_user_id(profile_id or profile_nickname)
    if not profile_id:
        return await bot.send_message(
            message.chat.id, 'Can\'t access audios of this account')

    tracks = await vk_api.get_audio(profile_id)
    await bot.send_message(
        message.chat.id, 'Tracks:',
        reply_markup=keyboards.profile_keyboard(tracks))

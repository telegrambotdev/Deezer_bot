from aiogram.dispatcher.filters import Text

from bot import dp
from . import vk_api, methods, keyboards
from utils import parse_callback


@dp.callback_query_handler(Text(startswith='vk_track'))
async def vk_track(callback):
    await callback.answer()
    _, obj_id, action = parse_callback(callback.data)
    track_id = callback.data.split(':')[1]
    track = await vk_api.get_track(track_id)
    await methods.send_track(callback.message.chat.id, track)


@dp.callback_query_handler(Text(startswith='vk_playlist'))
async def vk_playlist(callback):
    await callback.answer()
    _, obj_id, action = parse_callback(callback.data)
    if action == 'download':
        owner_id, playlist_id, access_key = obj_id.split('_')
        playlist = await vk_api.get_playlist(owner_id, playlist_id, access_key)
        await methods.send_playlist(
            callback.message.chat.id, playlist, pic=False, send_all=True)
    elif action == 'post':
        owner_id, playlist_id, access_key = obj_id.split('_')
        playlist = await vk_api.get_playlist(owner_id, playlist_id, access_key)
        await methods.send_playlist(
            -1001171972924, playlist, pic=True, send_all=True)


@dp.callback_query_handler(Text(startswith='vk_profile_audio_page'))
async def vk_profile_audio(callback):
    await callback.answer()
    _, profile_id, page = parse_callback(callback.data)
    tracks = await vk_api.get_audio(profile_id)
    return await callback.message.edit_reply_markup(
        keyboards.profile_keyboard(tracks, profile_id, int(page)))

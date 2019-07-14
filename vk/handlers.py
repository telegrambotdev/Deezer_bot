from . import methods
from . import vk_api


async def playlist_handler(message, owner_id, playlist_id, access_key):
    playlist = await vk_api.get_playlist(owner_id, playlist_id, access_key)
    await methods.send_playlist(message.chat.id, playlist)

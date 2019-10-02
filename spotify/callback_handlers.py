from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.webhook import SendMessage
from asyncache import cached
from cachetools import LRUCache

from bot import dp
from var import var
from deezer import deezer_api, methods
from utils import query_answer


@dp.callback_query_handler(Text(startswith='spotify:download_track'))
async def download_track(query):
    await query_answer(query)
    track_id = query.data.split(':')[2]
    track = await match_track(track_id)
    if track:
        await methods.send_track(query.message.chat.id, track)
    else:
        return SendMessage(
            query.message.chat.id,
            'Track is not found on Deezer, try manual search')


@cached(LRUCache(5000))
async def match_track(spotify_track_id):
    sp_track = await var.spot.get_track(spotify_track_id)
    search_query = f'{sp_track.artists[0].name} {sp_track.name}'
    tracks = await deezer_api.search(search_query)
    return tracks and tracks[0]

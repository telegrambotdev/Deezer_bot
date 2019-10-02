from aiogram.dispatcher.filters import Text

from bot import dp
from var import var
from deezer import deezer_api, methods


@dp.callback_query_handler(Text(startswith='spotify:download_track'))
async def download_track(query):
    track_id = query.data.split(':')[2]
    sp_track = await var.spot.get_track(track_id)
    search_query = f'{sp_track.artists[0].name} {sp_track.name}'
    track = await deezer_api.search(search_query)
    await methods.send_track(query.message.chat.id, track)

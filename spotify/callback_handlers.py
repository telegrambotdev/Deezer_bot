from aiogram.dispatcher.filters import Text

from bot import dp
from var import var
from deezer import deezer_api, methods
from utils import query_answer


@dp.callback_query_handler(Text(startswith='spotify:download_track'))
async def download_track(query):
    await query_answer(query)
    track_id = query.data.split(':')[2]
    sp_track = await var.spot.get_track(track_id)
    search_query = f'{sp_track.artists[0].name} {sp_track.name}'
    tracks = await deezer_api.search(search_query)
    await methods.send_track(query.message.chat.id, tracks[0])

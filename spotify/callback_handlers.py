from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.webhook import SendMessage
from asyncache import cached
from cachetools import LRUCache

from bot import dp
from var import var
from deezer import deezer_api, methods
from utils import query_answer


@dp.callback_query_handler(Text(startswith='spotify:download_track'))
async def download_track(query: types.CallbackQuery):
    await query_answer(query)
    track_id = query.data.split(':')[2]
    track = await match_track(track_id)
    if track:
        await methods.send_track(query.message.chat.id, track)
    else:
        return SendMessage(
            query.message.chat.id,
            'Track is not found on Deezer, try manual search')


@dp.callback_query_handler(Text(startswith='spotify:album'))
async def get_album(query: types.CallbackQuery):
    await query_answer(query)
    album_id = query.data.split(':')[2]
    album = match_album(album_id)
    if album:
        await methods.send_album(query.message.chat.id, album)
    else:
        return SendMessage(
            query.message.chat.id,
            'Album is not found on Deezer, try manual search')


@dp.callback_query_handler(Text(startswith='spotify:artist'))
async def get_artist(query: types.CallbackQuery):
    await query_answer(query)
    artist_id = query.data.split(':')[2]
    artist = match_artist(artist_id)
    if artist:
        await methods.send_artist(query.message.chat.id, artist)
    else:
        return SendMessage(
            query.message.chat.id,
            'Artist is not found on Deezer, try manual search')


@cached(LRUCache(5000))
async def match_track(spotify_track_id):
    sp_track = await var.spot.get_track(spotify_track_id)
    search_query = f'{sp_track.artists[0].name} {sp_track.name}'
    tracks = await deezer_api.search(search_query)
    return tracks and tracks[0]


@cached(LRUCache(5000))
async def match_album(spotify_album_id):
    sp_album = await var.spot.get_album(spotify_album_id)
    search_query = f'{sp_album.artists[0].name} {sp_album.name}'
    albums = await deezer_api.search(search_query, 'album')
    return albums and albums[0]


@cached(LRUCache(5000))
async def match_artist(spotify_artist_id):
    sp_artist = await var.spot.get_artist(spotify_artist_id)
    artists = await deezer_api.search(sp_artist.name, 'artist')
    return artists and artists[0]

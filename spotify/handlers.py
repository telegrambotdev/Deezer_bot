import re
from asyncio import sleep

from aiogram import types
from aiogram.utils.markdown import escape_md
from aiogram.dispatcher.webhook import SendMessage
from yarl import URL

from deezer import deezer_api
from deezer import methods as dz_methods
from .integration import get_token, REDIRECT_URL
from bot import bot, dp
from var import var
import filters
from db_utils import unset_spotify_token
from config import spotify_client
from utils import request_get, print_traceback
from AttrDict import AttrDict


@dp.message_handler(commands='spotify_logout')
async def spotify_logout(message: types.Message):
    await unset_spotify_token(message.from_user.id)
    return SendMessage(
        message.chat.id, 'You are successfully logged out')


@dp.message_handler(commands='spotify_auth')
async def spotify_auth(message: types.Message):
    params = {
        'client_id': spotify_client,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URL,
        'scope': 'user-read-currently-playing user-modify-playback-state',
        'state': message.from_user.id}
    url = URL('https://accounts.spotify.com/authorize').with_query(params)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Authorize', url=str(url)))
    return SendMessage(
        message.chat.id, 'Please authorize', reply_markup=markup)


@dp.message_handler(commands='spotify_now')
async def now_playing(message: types.Message):
    token = await get_token(message.from_user.id)
    if not token:
        return await spotify_auth(message)
    req = await request_get(
        'https://api.spotify.com/v1/me/player/currently-playing',
        headers={'Authorization': f'Bearer {token}'})
    try:
        json = await req.json()
        track = AttrDict(json['item'])
    except Exception as e:
        print_traceback(e)
        return SendMessage(
            message.chat.id,
            f'Play something in Spotify and try again')
    markup = types.InlineKeyboardMarkup(1)
    markup.add(types.InlineKeyboardButton(
        text='Open track', url=track.external_urls.spotify))
    markup.add(types.InlineKeyboardButton(
        text='Download track',
        callback_data=f'spotify:download_track:{track.id}'))
    markup.add(types.InlineKeyboardButton(
        text='Get album',
        callback_data=f'spotify:album:{track.album.id}'))
    markup.add(types.InlineKeyboardButton(
        text='Get artist',
        callback_data=f'spotify:artist:{track.artists[0].id}'))

    return SendMessage(
        message.chat.id,
        'Currently playing track:\n' +
        f'{track.artists[0].name} - {track.name}'
        f'<a href="{track.album.images[0].url}">&#8203;</a>',
        reply_markup=markup, parse_mode='HTML')


@dp.message_handler(filters.SpotifyFilter)
@dp.channel_post_handler(filters.SpotifyFilter)
async def spotify_handler(message, track_id):
    spotify_song = await var.spot.get_track(track_id)
    print(track_id)
    search_query = '%s %s' % (
        spotify_song.artists[0].name,
        re.match(r'[^\(\[\-]+', spotify_song.name).group(0))
    search_results = await deezer_api.search(q=search_query)
    if not search_results:
        return await bot.send_message(
            message.chat.id, 'Sorry, track is not found on Deezer')
    print(search_results[0])
    await dz_methods.send_track(message.chat.id, search_results[0])


@dp.message_handler(filters.SpotifyPlaylistFilter)
async def spotify_playlist_handler(message, playlist_id):
    spotify_playlist = await var.spot.get_playlist(playlist_id)
    for track in spotify_playlist:
        try:
            search_query = '{} {}'.format(
                track.artists[0].name,
                re.match(r'[^\(\[\-]+', track.name).group(0))
            search_results = await deezer_api.search(q=search_query)
            if search_results:
                await dz_methods.send_track(message.chat.id, search_results[0])
            else:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f'Sorry, track {track.artists[0].name} - {track.name} is not found on Deezer')
        except Exception as e:
            print(e)
        await sleep(.5)


@dp.message_handler(filters.SpotifyAlbumFilter)
async def spotify_album_handler(message, album_id):
    spotify_album = await var.spot.get_album(album_id)
    search_results = await deezer_api.search(
        f'{spotify_album.artists[0].name} {spotify_album.name}', 'album')
    if not search_results:
        return await bot.send_message(
            chat_id=message.chat.id,
            text=f'Sorry, album {spotify_album.name} by {spotify_album.artists[0].name} is not found on Deezer')
    await dz_methods.send_album(message.chat.id, search_results[0])


@dp.message_handler(filters.SpotifyArtistFilter)
async def spotify_artist_handler(message, artist_id):
    spotify_artist = await var.spot.get_artist(artist_id)
    search_results = await deezer_api.search(spotify_artist.name, 'artist')
    await dz_methods.send_artist(message.chat.id, search_results[0])

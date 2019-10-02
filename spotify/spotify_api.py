from base64 import urlsafe_b64encode
import re
from time import time

from asyncache import cached
from cachetools import TTLCache, LRUCache

from AttrDict import AttrDict
from bot import WEBHOOK_HOST
from deezer import deezer_api
from utils import encode_url, request_get, request_post, print_traceback
from db_utils import set_spotify_token, get_spotify_token, \
    get_spotify_refresh_token
from config import spotify_client, spotify_secret
from var import var

spotify_track = re.compile(r'open.spotify.com/track/[^? ]+')
spotify_album = re.compile(r'open.spotify.com/album/[^? ]+')
spotify_artist = re.compile(r'open.spotify.com/artist/[^? ]+')
spotify_playlist = re.compile(r'open.spotify.com/.+/playlist/[^? ]+')

AUTH = urlsafe_b64encode(
    f'{spotify_client}:{spotify_secret}'.encode()).decode()
AUTH_HEADER = {'Authorization': f"Basic {AUTH}"}
REDIRECT_URL = 'https://' + WEBHOOK_HOST + '/spotify_auth'


async def authorize(code=None, user_id=None):
    if code and user_id:
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URL,
            'state': user_id}
    else:
        data = {'grant_type': 'client_credentials'}

    try:
        req = await request_post(
            'https://accounts.spotify.com/api/token',
            data=data, headers={
                **AUTH_HEADER,
                'Content-Type': 'application/x-www-form-urlencoded'})
    except ValueError as exc:
        print_traceback(exc)
        return False
    resp = await req.json()

    if code and user_id:
        access_token = resp.get('access_token')
        refresh_token = resp.get('refresh_token')

        await set_spotify_token(
            user_id, access_token, refresh_token)
        return access_token

    else:
        var.spotify_token = resp.get('access_token')
        var.spotify_token_expires = int(resp.get('expires_in')) + time()
        return var.spotify_token


async def get_token(user_id):
    code = await get_spotify_token(user_id)
    if not code:
        await refresh_token(user_id)
    code = await get_spotify_token(user_id)
    return code


async def refresh_token(user_id):
    code = await get_spotify_refresh_token(user_id)
    if code:
        await authorize(code, user_id)


@cached(TTLCache(100, 600))
async def search(query, obj_type='track', limit=5):
    if not var.spotify_token or time() > var.spotify_token_expires:
        await authorize()
    data = {'type': obj_type, 'limit': limit, 'q': query}
    headers = {'Authorization': f'Bearer {var.spotify_token}'}
    r = await request_get(encode_url(
        'https://api.spotify.com/v1/search', data=data), headers=headers)
    json = await r.json()
    return [AttrDict(track) for track in json['tracks']['items']]


@cached(TTLCache(100, 600))
async def get_track(track_id):
    if not var.spotify_token or time() > var.spotify_token_expires:
        await authorize()
    r = await request_get(
        f'https://api.spotify.com/v1/tracks/{track_id}',
        headers={'Authorization': f'Bearer {var.spotify_token}'})
    json = await r.json()
    if not json.get('error'):
        return AttrDict(json)
    else:
        raise ValueError('Cannot get track')


@cached(TTLCache(100, 600))
async def get_playlist(playlist_id):
    if not var.spotify_token or time() > var.spotify_token_expires:
        await authorize()
    r = await request_get(
        f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
        headers={'Authorization': f'Bearer {var.spotify_token}'})
    print(r.url)
    json = await r.json()
    if not json.get('error'):
        return [AttrDict(track['track']) for track in json['items']]
    else:
        raise ValueError('Error getting playlist: ' + json.get('error'))


@cached(TTLCache(100, 600))
async def get_album(album_id):
    if not var.spotify_token or time() > var.spotify_token_expires:
        await authorize()
    r = await request_get(
        f'https://api.spotify.com/v1/albums/{album_id}',
        headers={'Authorization': f'Bearer {var.spotify_token}'})
    print(r.url)
    json = await r.json()
    if not json.get('error'):
        return AttrDict(json)
    else:
        raise ValueError('Error getting albums: ' + json.get('error'))


@cached(TTLCache(100, 600))
async def get_artist(artist_id):
    if not var.spotify_token or time() > var.spotify_token_expires:
        await authorize()
    r = await request_get(
        f'https://api.spotify.com/v1/artists/{artist_id}',
        headers={'Authorization': f'Bearer {var.spotify_token}'})
    print(r.url)
    json = await r.json()
    if not json.get('error'):
        return AttrDict(json)
    else:
        raise ValueError('Error getting artist: ' + json.get('error'))


@cached(LRUCache(5000))
async def match_track(spotify_track_id):
    sp_track = await get_track(spotify_track_id)
    search_query = f'{sp_track.artists[0].name} {sp_track.name}'
    search_query2 = f'{sp_track.artists[0].name} {sp_track.name}'\
        .lower().split('(f')[0]

    tracks = await deezer_api.search(search_query)
    if not tracks:
        tracks = await deezer_api.search(search_query2)
    return tracks and tracks[0]


@cached(LRUCache(5000))
async def match_album(spotify_album_id):
    sp_album = await get_album(spotify_album_id)
    search_query = f'{sp_album.artists[0].name} {sp_album.name}'
    albums = await deezer_api.search(search_query, 'album')
    return albums and albums[0]


@cached(LRUCache(5000))
async def match_artist(spotify_artist_id):
    sp_artist = await get_artist(spotify_artist_id)
    artists = await deezer_api.search(sp_artist.name, 'artist')
    return artists and artists[0]

import requests
from base64 import urlsafe_b64encode
import re
from time import time

from AttrDict import AttrDict
from bot import WEBHOOK_HOST
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


async def search(query, obj_type='track', limit=5):
    if not var.spotify_token or time() > var.spotify_token_expires:
        await authorize()
    data = {'type': obj_type, 'limit': limit, 'q': query}
    headers = {'Authorization': f'Bearer {var.spotify_token}'}
    r = await request_get(encode_url(
        'https://api.spotify.com/v1/search', data=data), headers=headers)
    json = await r.json()
    return [AttrDict(track) for track in json['tracks']['items']]


async def get_track(track_id):
    if not var.spotify_token or time() > var.spotify_token_expires:
        await authorize()
    r = await request_get(
        f'https://api.spotify.com/v1/tracks/{track_id}',
        headers={'Authorization': f'Bearer {var.spotify_token}'})
    print(r.url)
    json = await r.json()
    if not json.get('error'):
        return AttrDict(json)
    else:
        raise ValueError('Cannot get track')


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

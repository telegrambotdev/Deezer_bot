import os
import json
import asyncio
import random
import shutil
from io import BytesIO
from time import time
from hashlib import md5

from asyncache import cached
from cachetools import TTLCache

import config
from var import var
from utils import download_file, get_file, request_get, \
    vk_add_tags, print_traceback
from AttrDict import AttrDict


HEADERS = {"user-agent": "VKAndroidApp/5.11.1-2316"}
HOST_API = "https://api.vk.com/"
OAUTH = "https://oauth.vk.com/"

VK_API_VERSION = "5.89"


async def call_oauth(method, param={}, **kwargs):
    """Выполнение метода VK API"""
    try:
        response = await(
            await request_get(method, params=param, headers=HEADERS)).json()
    except Exception as e:
        raise e

    if "error" in response:
        if "need_captcha" == response["error"]:
            raise Exception("Error : CAPTHA!")

        elif "need_validation" == response["error"]:
            if "ban_info" in response:
                # print(response)
                raise Exception(
                    "Error: {error_description}".format(**response))

                return "Error: 2fa isn't supported"

        else:
            raise Exception("Error : {error_description}".format(**response))

    return response


async def call(method, param={}, **kwargs):
    """Выполнение метода VK API"""
    try:
        response = await (
            await request_get(method, params=param, headers=HEADERS)).json()
    except Exception as e:
        print(e)
        raise e

    if "error" in response:
        raise Exception(
            "VKError #{error_code}: {error_msg}".format(**response["error"])
        )

    if "response" in response:
        return response["response"]

    return response


async def autorization(login, password, client_id, client_secret,
                       code, captcha_sid="null", captcha_key="null",
                       force_reauth=False):
    if not force_reauth:
        try:
            with open("vk_auth.json", "r") as f:
                var.vk_auth = json.load(f)['access_token']
                return var.vk_auth
        except FileNotFoundError:
            pass

    param = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": login,
        "password": password,
        "v": VK_API_VERSION,
        "2fa_supported": "1",
        "code": code,
        "captcha_sid": captcha_sid,
        "captcha_key": captcha_key,
    }

    response = await call_oauth(OAUTH + "token", param)

    with open("vk_auth.json", "w") as f:
        json.dump(response, f)
    var.vk_auth = response['access_token']

    return response['access_token']


async def refresh_token(access_token: str):
    param = {
        "access_token": access_token,
        "receipt": config.vk_token_receipt,
        "v": VK_API_VERSION,
    }

    response = await call(HOST_API + "method/auth.refreshToken", param)
    token = response['token']
    var.vk_refresh_token = token

    return token


async def get_user_id(account):
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION,
        "user_ids": account,
        "fields": "can_see_audio"}

    response = await call(HOST_API + "method/users.get", param)
    user_id = response[0]['id']
    if not response[0]['can_see_audio']:
        return None

    return user_id


@cached(TTLCache(100, 1200))
async def get_audio(owner_id):
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION,
        "owner_id": owner_id
    }

    audios = await call(HOST_API + "method/audio.get", param)

    return [Track(track) for track in audios['items']]


@cached(TTLCache(100, 1200))
async def get_track(track_id):
    cached_track = var.vk_tracks.get(track_id)
    if cached_track:
        return cached_track

    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION,
        "audios": track_id
    }

    tracks = await call(HOST_API + "method/audio.getById", param)

    return Track(tracks[0])


@cached(TTLCache(100, 1200))
async def get_tracks(track_ids):
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION,
        "audios": ','.join(track_ids)
    }

    tracks = await call(HOST_API + "method/audio.getById", param)

    return [Track(track) for track in tracks]


async def get_catalog():
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION}

    return await call(HOST_API + "method/audio.getCatalog", param)


@cached(TTLCache(100, 1200))
async def search(query: str):
    param = {"access_token": var.vk_refresh_token,
             "v": VK_API_VERSION, "q": query}

    results = await call(HOST_API + "method/audio.search", param)
    if results:
        tracks = [Track(track) for track in results['items']]
        for track in tracks:
            var.vk_tracks[track.full_id] = track

        return tracks
    return []


async def get_playlist(
        owner_id: int, playlist_id: int, access_key: str = None):
    param = {
        "access_token": var.vk_refresh_token,
        "owner_id": owner_id,
        "id": playlist_id,
        "need_playlist": 1,
        "v": VK_API_VERSION,
    }

    if access_key:
        param['access_key'] = access_key

    response = await call(HOST_API + "method/execute.getPlaylist", param)
    playlist = Playlist(response)

    for track in playlist.tracks:
        var.vk_tracks[track.full_id] = track

    return playlist


async def get_music_page(owner_id):
    param = {
        "func_v": 3,
        "need_playlists": 1,
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION,
        "owner_id": owner_id
    }

    playlist = await call(HOST_API + "method/execute.getMusicPage", param)

    return playlist


class Track(AttrDict):
    def __init__(self, mapping: dict):
        super().__init__(mapping)
        self.valid_till = time() + 23 * 3600
        self.full_id = f"{self.owner_id}_{self.id}"

    def url_valid(self):
        return self.valid_till < time()

    def hash_track(self):
        args = [self.artist, self.title, str(self.duration)]
        if self.album:
            args.extend([str(self.album.id), self.album.title])

        s = ':'.join(args).encode('utf-8', 'ignore')
        return md5(s).hexdigest()

    async def download(self):
        print(
            f'[VK] Start downloading: {self.full_id} '
            f' | {self.artist} - {self.title}')
        stream = BytesIO(await get_file(self.url))
        cover = None
        if self.album and self.album.thumb and self.album.thumb.photo_600:
            cover = await get_file(self.album.thumb.photo_600)
        vk_add_tags(stream, self, cover)
        print(
            f'[VK] Finished downloading: {self.full_id} '
            f' | {self.artist} - {self.title}')
        return stream

    async def get_thumb(self):
        if self.album and self.album.thumb and self.album.thumb.photo_135:
            return await get_file(self.album.thumb.photo_135)


class Playlist:
    def __init__(self, mapping):
        self.tracks = [Track(x) for x in mapping['audios']]
        for key, val in mapping['playlist'].items():
            self.__setattr__(key, val)

        if not hasattr(self, 'photo'):
            self.photo = None

        if hasattr(self, 'access_key'):
            self.full_id = f'{self.owner_id}_{self.id}_{self.access_key}'
        else:
            self.full_id = f'{self.owner_id}_{self.id}_'

        self.data = mapping


async def login(force_reauth=False):
    auth = await autorization(
        config.vk_login,
        config.vk_password,
        *config.vk_android_clinet_key,
        config.vk_auth,
        force_reauth=force_reauth)
    await refresh_token(auth)

asyncio.get_event_loop().run_until_complete(login())
print('vk login')

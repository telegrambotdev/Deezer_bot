import os
import json

import config
from var import var
from utils import download_file, get_file, request_get, vk_add_tags
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
                       forse_reauth=False):
    if not forse_reauth:
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


async def user_get():
    param = {"access_token": var.vk_refresh_token, "v": VK_API_VERSION}

    return await call(HOST_API + "method/users.get", param)


async def get_audio(owner_id):
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION,
        "owner_id": owner_id
    }

    audios = await call(HOST_API + "method/audio.get", param)

    return [Track(track) for track in audios['items']]


async def get_track(owner_id: int, track_id: int):
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION,
        "owner_id": owner_id,
        "id": track_id
    }

    track = await call(HOST_API + "method/audio.get", param)

    return Track(track)


async def get_catalog():
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION}

    return await call(HOST_API + "method/audio.getCatalog", param)


async def search(query: str):
    param = {"access_token": var.vk_refresh_token,
             "v": VK_API_VERSION, "q": query}

    results = await call(HOST_API + "method/audio.search", param)

    return [Track(track) for track in results['items']]


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

    return Playlist(
        (await call(HOST_API + "method/execute.getPlaylist", param))['audios'],
        playlist_id)


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

    @property
    def full_id(self):
        return f"{self.owner_id}_{self.id}"

    async def download(self, path: str = None):
        if not path:
            os.makedirs(f"downloads/vk_{self.id}/", exist_ok=True)
            path = (
                f"downloads/vk_{self.id}/" +
                f"{self.artist} - {self.title}".replace("/", "_")[:70] +
                ".mp3")
        await download_file(self.url, path)
        cover = None
        if self.album and self.album.thumb and self.album.thumb.photo_600:
            cover = await get_file(self.album.thumb.photo_600)
        vk_add_tags(path, self, cover)
        return path


class Playlist:
    def __init__(self, tracks: list, playlist_id: int):
        self.tracks = [Track(track) for track in tracks]

        for track in self.tracks:
            if track.album and track.album['id'] == playlist_id:
                for key, val in track.album.items():
                    if not isinstance(val, dict):
                        setattr(self, key, val)
                    else:
                        setattr(self, key, AttrDict(val))
                break
        else:
            raise ValueError('Can\'t get a playlist')


async def login():
    auth = await autorization(
        '79654924081',
        'P8F4zJ3j7hNCI1CbDbFQOBkxgQGCvkn6',
        *config.vk_android_clinet_key,
        config.vk_auth)
    await refresh_token(auth)

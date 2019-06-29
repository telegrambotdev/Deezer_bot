import json

import config
from var import var
from utils import download_file, get_file, request_get, vk_add_tags
from AttrDict import AttrDict


HEADERS = {"user-agent": "VKAndroidApp/5.11.1-2316"}
HOST_API = "https://api.vk.com/"
OAUTH = "https://oauth.vk.com/"
BACKUP_API = "http://api.xn--41a.ws/api.php"

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


async def refreshToken(access_token):
    param = {
        "access_token": access_token,
        "receipt": config.vk_token_receipt,
        "v": VK_API_VERSION,
    }

    return await call(HOST_API + "method/auth.refreshToken", param)


async def user_get():
    param = {"access_token": var.vk_, "v": VK_API_VERSION}

    return await call(HOST_API + "method/users.get", param)


async def get_audio():
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION}

    return await call(HOST_API + "method/audio.get", param)


async def get_catalog():
    param = {
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION}

    return await call(HOST_API + "method/audio.getCatalog", param)


async def search(query):
    param = {"access_token": var.vk_refresh_token,
             "v": VK_API_VERSION, "q": query}

    return await call(HOST_API + "method/audio.search", param)


async def get_playlist(owner_id, playlist_id):
    param = {
        "access_token": var.vk_refresh_token,
        "owner_id": owner_id,
        "id": playlist_id,
        "need_playlist": 1,
        "v": VK_API_VERSION,
    }

    return await call(HOST_API + "method/execute.getPlaylist", param)


async def get_music_page():
    param = {
        "func_v": 3,
        "need_playlists": 1,
        "access_token": var.vk_refresh_token,
        "v": VK_API_VERSION,
    }

    return await call(HOST_API + "method/execute.getMusicPage", param)


class Track(AttrDict):
    def __init__(self, mapping):
        super().__init__(mapping)

    async def download(self, path=None):
        if not path:
            path = (
                f"downloads/vk_{self.id}/"
                + f"{self.performer} - {self.title}".replace("/", "_")[:70]
                + ".mp3"
            )
        await download_file(self.url, path)
        cover = None
        if self.album and self.album.thumb and self.album.thumb.photo_600:
            cover = await get_file(self.album.thumb.photo_600)
        vk_add_tags(path, self.artist, self.title, self.album, cover)
        return path


class Playlist(AttrDict):
    def __init__(self, mapping):
        super().__init__(mapping)
        self.tracks = []
        for track in self.list:
            self.tracks.append(Track(track))

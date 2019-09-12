import asyncio
import os
import random
from io import BytesIO
from contextlib import suppress

from asyncache import cached
from cachetools import TTLCache

import utils
from AttrDict import AttrDict
from config import deezer_private_cookies, deezer_private_headers
from logger import file_download_logger
from utils import request_get, request_post, get_album_cover_url
from var import var

from . import decrypt

unofficial_api_url = 'https://www.deezer.com/ajax/gw-light.php'
api_url = 'https://api.deezer.com'

qualities = {
    'MP3_128': '1',
    'MP3_320': '3',
    'FLAC': '9',
}


def get_api_cid():
    return int(1e9 * random.random())


async def getCSRFToken():
    r = await private_api_call('deezer.getUserData')
    var.CSRFToken = r['checkForm']
    return var.CSRFToken


async def private_api_call(method, **json_req):
    api_token = 'null' if method == 'deezer.getUserData' else (
        var.CSRFToken or await getCSRFToken())
    context = {
        'api_version': '1.0',
        'api_token': api_token,
        'input': 3,
        'cid': get_api_cid(),
        'method': method}
    r = await request_post(
        unofficial_api_url, params=context,
        json=json_req, headers=deezer_private_headers,
        cookies=deezer_private_cookies)
    return (await r.json())['results']


async def api_call(obj_name, obj_id, method='', errcount=0, **params):
    r = await request_get(
        f'{api_url}/{obj_name}/{obj_id}/{method}', params=params)
    obj = AttrDict(await r.json())
    if obj.error:
        if errcount > 2:
            raise ValueError(
                f'error getting object {obj}_{obj_id}'
                f'\n{r.url}')

        url = f'https://deezer.com/{obj_name}/{obj_id}/'
        r = await request_get(url)
        new_id = str(r.url).split('/')[-1]
        return await api_call(obj_name, new_id, method, errcount + 1, **params)

    if obj.get('data'):
        obj = obj['data']
        if not len(obj):
            return []
    if isinstance(obj, list):
        return obj
    return AttrDict(obj)


@cached(TTLCache(100, 600))
async def search(q='', obj='track'):
    encoded_url = utils.encode_url(
        f'{api_url}/search/{obj}/', {'q': q, 'limit': 50})
    results = await (await request_get(encoded_url)).json()
    try:
        if obj == 'artist':
            result = [Artist(result) for result in results['data']]
        elif obj == 'album':
            result = [Album(result) for result in results['data']]
        elif obj == 'track':
            result = [Track(result) for result in results['data']]
        else:
            result = [AttrDict(result) for result in results['data']]
        return result or []
    except KeyError:
        print(obj)


@utils.calling_queue(5)
async def download_track(track_id, quality='MP3_320'):
    track = await gettrack(track_id)
    album = await getalbum(track.album.id)
    private_info = await getprivateinfo(track.id)
    try:
        private_track = private_info['DATA']
    except KeyError:
        await getCSRFToken()
        try:
            private_track = private_info['DATA']
        except KeyError:
            raise ValueError('Cant download track')
    try:
        lyrics = private_info['LYRICS']['LYRICS_TEXT']
    except KeyError:
        lyrics = None
    if not private_track[f'FILESIZE_{quality}']:
        raise ValueError(
            f'quality {quality} is not availible for track {track_id}')
    quality_n = qualities[quality]
    if quality_n == '9':
        ext = 'flac'
    else:
        ext = 'mp3'

    print(
        f'[Deezer] Start downloading: {track.id} | {track.artist.name} - {track.title} ')
    track_url = decrypt.get_dl_url(private_track, quality_n)
    os.makedirs(f'downloads/{track.id}', exist_ok=True)
    filepath = f'downloads/{track.id}/{track.filename_safe}.{ext}'
    stream = await utils.get_file(track_url)
    await decrypt.decrypt_track(stream, private_track, filepath)
    cover = await track.get_max_size_cover(album)
    utils.add_tags(filepath, track, album, cover, lyrics)
    print(
        f'[Deezer] Finished downloading: {track.id} | {track.artist.name} - {track.title} ')
    file_download_logger.info(f'[downloaded track {track.id}] {track}')
    return filepath


@cached(TTLCache(100, 600))
async def getprivateinfo(track_id):
    return (await private_api_call(
        'deezer.pageTrack', SNG_ID=track_id))


async def getlyrics(track_id):
    return (await private_api_call(
        track_id))['LYRICS']['LYRICS_TEXT']


@cached(TTLCache(100, 600))
async def gettrack(track_id):
    track = Track(await api_call('track', track_id))
    return track


@cached(TTLCache(100, 600))
async def getalbum(album_id):
    obj = await api_call('album', album_id)
    return Album(obj)


@cached(TTLCache(100, 600))
async def getplaylist(playlist_id):
    playlist = await api_call('playlist', playlist_id)
    return AttrDict(playlist)


@cached(TTLCache(100, 600))
async def getplaylist_tracks(playlist_id):
    playlist = await api_call('playlist', playlist_id, 'tracks', limit=2000)
    return [Track(track) for track in playlist]


@cached(TTLCache(100, 600))
async def getartist(artist_id):
    obj = await api_call('artist', artist_id)
    return Artist(obj)


class Track(AttrDict):
    def __init__(self, json):
        super().__init__(json)

    @property
    def filename_safe(self):
        if self.track_position < 10:
            track_number = '0' + str(self.track_position)
        else:
            track_number = str(self.track_position)
        return f'{track_number} {self.artist.name} - {self.title}' \
            .replace('/', '_')[:200].strip()

    async def download(self, quality='MP3_320'):
        return await download_track(self.id, quality)

    async def get_max_size_cover(self, album):
        url = album.cover_xl or await get_album_cover_url(album.id)
        r = await request_get(url)
        res = await r.content.read()
        if len(res) < 100:
            r = await request_get(album.cover)
            r = await request_get(r.url.replace('120x120', '1000x1000'))
            res = await r.content.read()
        return res

    async def get_thumb(self):
        os.makedirs(f'downloads/{self.id}', exist_ok=True)
        filepath = f'downloads/{self.id}/thumb.jpg'
        track = await gettrack(self.id)
        return await utils.download_file(track.album.cover_small, filepath)

    def __repr__(self):
        with suppress(AttributeError):
            return (f'[{self.id}] {self.artist.name}'
                    f' - {self.title} - {self.album.title}')
        return self.title

    def __hash__(self):
        return 24531 * self.id


class Album(AttrDict):
    def __init__(self, json):
        super().__init__(json)

    async def get_tracks(self):
        r = await request_get(
            f'https://api.deezer.com/album/{self.id}/tracks',
            data={'limit': -1})
        json = await r.json()
        return [Track(track) for track in json['data']]

    def __hash__(self):
        return 39733 * self.id


class Artist(AttrDict):
    def __init__(self, json):
        super().__init__(json)

    async def all_tracks(self):
        tracks = []

        for album in await self.albums():
            tracks.extend(await album.get_tracks())
        return tracks

    async def albums(self):
        try:
            r = await api_call('artist', self.id, 'albums', limit=99)
            return [Album(album) for album in r]
        except Exception as e:
            print(self.name, e, type(e))

    async def top(self, limit=5):
        r = await api_call('artist', self.id, 'top', limit=limit)
        return [AttrDict(track) for track in r]

    async def related(self):
        r = await api_call('artist', self.id, 'related')
        return [Artist(artist) for artist in r]

    async def radio(self):
        r = await api_call('artist', self.id, 'radio')
        return [AttrDict(track) for track in r]

    def __hash__(self):
        return 57323 * self.id


async def main():
    s = await getalbum(input('album id: '))
    return s

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    s = loop.run_until_complete(main())
    print('result in object "s"')

import re
import asyncio
from bs4 import BeautifulSoup

from asyncache import cached
from aiograph import Telegraph
from cachetools import TTLCache, LRUCache

from AttrDict import AttrDict
from utils import request_get
from deezer import deezer_api
from spotify import spotify_api
from config import genius_token, telegraph_token
from db_utils import get_telegraph_url, add_telegraph_url


telegraph = Telegraph()
page_template = '''<img src="{img_url}">

<p><h3>{title}</h3></p>
<br>
<p><h4>{artist}</h4></p>
<br>
<p><h4>From {album}</h4></p>
<br>
<br>
<p>
{lyrics_body}
</p>'''


async def telegraph_track(chat_id, track):
    in_db_url = await get_telegraph_url(track.id)
    if in_db_url:
        in_db_url
    lyrics = await track.get_lyrics(False)
    page = await telegraph.create_page(
        f'{track.primary_artist.name} \u2013 {track.title}',
        page_template.format(
            img_url=track.album.cover_art_url if track.album else track.song_art_image_url,
            artist=track.primary_artist.name,
            album=track.album.name if track.album else track.title,
            title=track.title, lyrics_body=lyrics),
        access_token=telegraph_token)

    await add_telegraph_url(track.id, page.url)
    return page.url


@cached(LRUCache(1000))
async def deezer_match(track_id):
    track = deezer_api.gettrack(track_id)
    search_query = f'{track.artist.name} {track.name}'\
        .lower().split('(f')[0].split('feat.')[0].split('ft.')[0]
    results = await search(search_query)
    for result in results:
        if result.primary_artist.name == track.artist.name:
            return result


@cached(LRUCache(1000))
async def spotify_match(track_id):
    track = await spotify_api.get_track(track_id)
    search_query = f'{track.artists[0].name} {track.name}'\
        .lower().split('(f')[0].split('feat.')[0].split('ft.')[0]
    results = await search(search_query)
    for result in results:
        if result.primary_artist.name in [
                artist.name for artist in track.artists]:
            return result


@cached(TTLCache(500, 600))
async def search(query):
    data = {
        'access_token': genius_token,
        'q': query}
    r = await request_get('https://api.genius.com/search', params=data)
    search_obj = AttrDict(await r.json())
    return [Song(r.result) for r in search_obj.response.hits]


@cached(TTLCache(500, 600))
async def get_track(song_id):
    r = await request_get(
        f'https://api.genius.com/songs/{song_id}',
        params={'access_token': genius_token})
    result = Song(await r.json())
    return result


@cached(TTLCache(500, 600))
async def get_album(album_id):
    r = await request_get(
        f'https://api.genius.com/albums/{album_id}',
        params={'access_token': genius_token})
    obj = (await r.json())['response']['album']
    return Album(obj)


@cached(TTLCache(500, 600))
async def get_artist(artist_id):
    r = await request_get(
        f'https://api.genius.com/artists/{artist_id}',
        params={'access_token': genius_token})
    return Song(await r.json())


async def request(method, id, **params):
    r = request_get(
        f'https://api.genius.com/{method}/{id}',
        params={**params, 'access_token': genius_token})
    j = await r.json()
    response_code = j['meta']['status']
    if response_code != 200:
        raise ValueError(f'request error code: {response_code}')
    return AttrDict(j)


class Song(AttrDict):
    def __init__(self, json):
        self._spotify = None
        self._soundcloud = None
        self._youtube = None
        try:
            if isinstance(json, AttrDict):
                super().__init__(json)
            else:
                super().__init__(json['response']['song'])
        except KeyError:
            raise ValueError('Song id is not valid')

    async def get_lyrics(self, text_only=True):
        r = await request_get(self.url)
        soup = BeautifulSoup(await r.text(), 'html.parser')
        if text_only:
            return soup.find(class_='lyrics').text
        lyrics = str(soup.find(class_='lyrics'))
        converted_lyrics = re.sub(
            r'</?(a|div|p|!--sse--)[^>]*>', '', lyrics, flags=re.S)
        return converted_lyrics

    @property
    def spotify(self):
        if not self._spotify:
            for i in self.media:
                if i.provider == 'spotify':
                    self._spotify = i.url
        return self._spotify

    @property
    def youtube(self):
        if not self._youtube:
            for i in self.media:
                if i.provider == 'youtube':
                    self._youtube = i.url
        return self._youtube

    @property
    def soundcloud(self):
        if not self._soundcloud:
            for i in self.media:
                if i.provider == 'soundcloud':
                    self._soundcloud = i.url
        return self._soundcloud


class Album(AttrDict):
    def __init__(self, json):
        try:
            super().__init__(self, json)
        except KeyError as e:
            print(e)
            raise ValueError('Album id is not valid')

    @property
    def tracks(self):
        return [Song(x) for x in self.song_performances]


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())

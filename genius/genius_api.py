import asyncio
from bs4 import BeautifulSoup

from asyncache import cached
from cachetools import TTLCache

from AttrDict import AttrDict
from utils import request_get
from config import genius_token


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

    async def get_lyrics(self):
        r = await request_get(self.url)
        soup = BeautifulSoup(await r.text(), 'html.parser')
        lyrics = soup.find(
            'div', {'class': 'song_body-lyrics'}).text.split('More on Genius')[0]
        return lyrics.replace('\n\n\n', '\n')

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

import re

from aiogram.dispatcher.filters import BoundFilter
from aiogram import types


deezer_track = re.compile(r'.*deezer\.com/.{0,3}track/(\d+).*')
deezer_artist = re.compile(r'.*deezer\.com/.{0,3}artist/(\d+).*')
deezer_album = re.compile(r'.*deezer\.com/.{0,3}album/(\d+).*')
deezer_playlist = re.compile(r'.*deezer\.com/.{0,3}playlist/(\d+).*')
spotify_track = re.compile(r'.*open\.spotify\.com/track/([^? ]+)')
spotify_album = re.compile(r'.*open\.spotify\.com/album/([^? ]+)')
spotify_artist = re.compile(r'.*open\.spotify\.com/artist/([^? ]+)')
spotify_playlist = re.compile(r'.*open\.spotify\.com/.+/playlist/([^? ]+)')


async def SpotifyFilter(message: types.Message):
	match = re.match(spotify_track, message.text)
	if match:
		return {'track_id': match.group(1)}


async def SpotifyPlaylistFilter(message: types.Message):
	match = re.match(spotify_playlist, message.text)
	if match:
		return {'playlist_id': match.group(1)}


async def SpotifyAlbumFilter(message: types.Message):
	match = re.match(spotify_album, message.text)
	if match:
		return {'album_id': match.group(1)}


async def SpotifyArtistFilter(message: types.Message):
	match = re.match(spotify_artist, message.text)
	if match:
		return {'artist_id': match.group(1)}


async def DeezerFilter(message: types.Message):
	match = re.match(deezer_track, message.text)
	if match:
		return {'track_id': match.group(1)}


async def DeezerPlaylistFilter(message: types.Message):
	match = re.match(deezer_playlist, message.text)
	if match:
		return {'playlist_id': match.group(1)}


async def DeezerAlbumFilter(message: types.Message):
	match = re.match(deezer_album, message.text)
	if match:
		return {'album_id': match.group(1)}


async def DeezerArtistFilter(message: types.Message):
	match = re.match(deezer_artist, message.text)
	if match:
		return {'artist_id': match.group(1)}


async def ShazamFilter(message: types.Message):
	return 'shazam.com' in message.text

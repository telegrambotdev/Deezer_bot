from asyncio import sleep

from aiogram import types

from var.var import bot, dp
import db_utils
from . import deezer_api
from . import methods
import filters
import utils


async def redownload_handler(message: types.Message):
    if 'com/' in message.text:
        obj_type = message.text.split('/')[-2]
        obj_id = message.text.split('/')[-1]
        if obj_type == 'track':
            track = await deezer_api.gettrack(obj_id)
            await methods.send_track(message.chat.id, track, Redownload=True)
        else:
            album = await deezer_api.getalbum(obj_id)
            for track in await album.get_tracks():
                await methods.send_track(message.chat.id, track, Redownload=True)
    else:
        search = await deezer_api.search(q=message.text.strip('/re '))
        await methods.send_track(
            message.chat.id,
            await deezer_api.gettrack(search[0].id),
            Redownload=True)


async def diskography_handler(message: types.Message):
    if message.reply_to_message and message.reply_to_message.audio:
        artist_name = message.reply_to_message.audio.performer
    else:
        artist_name = message.text.strip('/d ').split('/')[-1]
    if artist_name.isdigit():
        artist = await deezer_api.getartist(artist_name)
    else:
        artist = (await deezer_api.search(artist_name, 'artist'))[0]

    tracks = await artist.all_tracks()
    total, skipped = len(tracks), 0
    for track in tracks:
        if await db_utils.get_track(track.id):
            skipped += 1

    text = f'{artist.name}\n\nskipped ({skipped}/{total})'

    await bot.send_message(message.chat.id, text)

    for track in tracks:
        try:
            await methods.cache(track)
            await sleep(0)
        except Exception as e:
            print(e)
            await bot.send_message(message.chat.id, e)
    await bot.send_message(message.chat.id, f'{artist.name} done')

    for artist in (await artist.related())[:5]:
        try:
            await sleep(2)
            tracks = await artist.all_tracks()
            total, skipped = len(tracks), 0
            for i, track in enumerate(tracks, start=1):
                if await db_utils.get_track(track.id):
                    skipped += 1
            if skipped == total:
                await sleep(3)
                continue
            text = f'{artist.name}\n\nskipped ({skipped}/{total})'
            await bot.send_message(message.chat.id, text)
            for track in tracks:
                await methods.cache(track)
            await bot.send_message(message.chat.id, f'{artist.name} done')

        except Exception as e:
            print(e)
            await bot.send_message(message.chat.id, f'{artist.name}\n\n{e}')


@dp.message_handler(commands=['a', 'artist'])
async def artist_search_handler(message):
    artist = (await deezer_api.search(
        message.text.strip(message.get_command()), 'artist'))[0]
    await methods.send_artist(message.chat.id, artist)


@dp.message_handler(filters.DeezerArtistFilter)
async def artist_handler(message, artist_id):
    artist = await deezer_api.getartist(artist_id)
    await methods.send_artist(message.chat.id, artist)


@dp.message_handler(filters.DeezerAlbumFilter)
async def album_handler(message, album_id):
    album = await deezer_api.getalbum(album_id)
    await methods.send_album(message.chat.id, album)


@dp.message_handler(filters.DeezerPlaylistFilter)
async def playlist_handler(message, playlist_id):
    playlist = await deezer_api.getplaylist(playlist_id)
    tracks = await deezer_api.getplaylist_tracks(playlist_id)
    await methods.send_playlist(message.chat.id, playlist, tracks)


@dp.message_handler(filters.DeezerFilter)
@dp.channel_post_handler(filters.DeezerFilter)
async def track_handler(message, track_id):
    track = await deezer_api.gettrack(track_id)
    if utils.already_downloading(track.id):
        return
    await methods.send_track(message.chat.id, track)
    db_utils.add_user(message.from_user)

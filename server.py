import os
import asyncio
import shutil

import aioredis
from aiogram import Bot, types
from aiohttp import web, ClientSession

from deezer import deezer_api, server_methods as deezer_methods
from soundcloud import soundcloud_api, server_methods as soundcloud_methods
from vk import vk_api, server_methods as vk_methods
import config
from userbot import post_large_track
from var import var

loop = asyncio.get_event_loop()
bot = Bot(config.bot_token, loop=loop)
app = web.Application()
routes = web.RouteTableDef()
session = None


async def on_startup(app):
    global session
    await deezer_api.getCSRFToken()
    session = ClientSession(raise_for_status=True)
    var.CSRFToken = None
    var. conn = await aioredis.create_connection(
        ('localhost', 6379), encoding='utf-8', db=4, loop=loop)
    var.loop = loop


async def on_shutdown(app):
    await session.close()
    await asyncio.sleep(0)


@routes.post('/deezer/send.track')
async def deezer_send(request: web.Request):
    data = await request.json()
    track = data.get('track')
    chat_id = data.get('chat_id')
    if track and chat_id:
        track = deezer_api.Track(track)
        asyncio.create_task(deezer_methods.send_track(chat_id, track))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


@routes.post('/deezer/send.tracks')
async def deezer_send_many(request: web.Request):
    data = await request.json()
    tracks = data.get('tracks')
    chat_id = data.get('chat_id')
    if tracks and chat_id:
        tracks = [deezer_api.Track(track) for track in tracks]
        asyncio.create_task(
            deezer_methods.send_playlist(chat_id, tracks))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


@routes.post('/soundcloud/send.track')
async def soundcloud_send(request: web.Request):
    data = await request.json()
    track = data.get('track')
    chat_id = data.get('chat_id')
    if track and chat_id:
        track = soundcloud_api.SoundCloudTrack(track)
        asyncio.create_task(
            soundcloud_methods.send_track(chat_id, track))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


@routes.post('/soundcloud/send.tracks')
async def soundcloud_send_many(request: web.Request):
    data = await request.json()
    tracks = data.get('tracks')
    chat_id = data.get('chat_id')
    if tracks and chat_id:
        tracks = [soundcloud_api.SoundCloudTrack(track) for track in tracks]
        asyncio.create_task(
            soundcloud_methods.send_tracks(chat_id, tracks))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


@routes.post('/vk/send.track')
async def vk_send(request: web.Request):
    data = await request.json()
    track = data.get('track')
    chat_id = data.get('chat_id')
    if track and chat_id:
        track = vk_api.Track(track)
        asyncio.create_task(
            vk_methods.send_track(chat_id, track))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


@routes.post('/vk/send.playlist')
async def vk_send_many(request: web.Request):
    data = await request.json()
    playlist = data.get('playlist')
    chat_id = data.get('chat_id')
    if playlist and chat_id:
        playlist = vk_api.Playlist(playlist)
        asyncio.create_task(
            vk_methods.send_playlist(chat_id, playlist))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.add_routes(routes)
web.run_app(app, host='localhost', port=8082)

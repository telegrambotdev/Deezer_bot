import os
import asyncio
import shutil

import aioredis
from aiogram import Bot, types
from aiohttp import web, ClientSession

from deezer import deezer_api, server_methods as deezer_methods
from vk import vk_api
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
async def deezer_send(request):
    track_id = request.query.get('track_id')
    chat_id = request.query.get('chat_id')
    if track_id and chat_id:
        track = await deezer_api.gettrack(track_id)
        asyncio.create_task(await deezer_methods.send_track(track, chat_id))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


@routes.post('/deezer/send.album')
async def deezer_album_send(request):
    album_id = request.query.get('album_id')
    chat_id = request.query.get('chat_id')
    if album_id and chat_id:
        album = await deezer_api.getalbum(album_id)
        asyncio.create_task(deezer_methods.send_album(album, chat_id))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


@routes.post('/deezer/send.playlist')
async def deezer_playlist_send(request):
    playlist_id = request.query.get('playlist_id')
    chat_id = request.query.get('chat_id')
    if playlist_id and chat_id:
        tracks = await deezer_api.getplaylist_tracks(playlist_id)
        asyncio.create_task(deezer_methods.send_playlist(tracks, chat_id))
        return web.Response(text='OK')
    else:
        return web.Response(text='no data', status=404)


app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
web.run_app(app, port=8082)

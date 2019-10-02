from aiogram import types

from bot import bot
from AttrDict import AttrDict
import bot_config
import utils
import methods
import inline_keyboards
from var import var

async def start_command_handler(message):
    await bot.send_message(
        chat_id=message.chat.id,
        text=bot_config.welcome_message,
        reply_markup=inline_keyboards.start_keyboard())


async def track_handler(message):
    track = await var.GeniusAPI.get_track(message.text.split('/')[-1])
    await methods.send_track(track, message.chat.id)


async def audio_message_handler(message):
    title = message.audio.title
    artist = message.audio.performer
    search_results = await var.GeniusAPI.search(f'{artist} {title}')
    track = await var.GeniusAPI.get_track(search_results[0].id)
    await methods.send_track(track, message.chat.id)


async def spotify_handler(message):
    spotify_track = await var.SpotifyAPI.get_track(message.text)
    search_results = await var.GeniusAPI.search(
        f'{spotify_track.artist.name} {spotify_track.name}')
    track = await var.GeniusAPI.get_track(search_results[0].id)
    await methods.send_track(track, message.chat.id)    


async def deezer_handler(message):
    track_id = message.text.split('/')[-1]
    r = await var.session.get(f'https://api.deezer.com/track/{track_id}')
    deezer_track = AttrDict(await r.json())
    search_results = await var.GeniusAPI.search(
        f'{deezer_track.artist.name} {deezer_track.title}')
    track = await var.GeniusAPI.get_track(search_results[0].id)
    await methods.send_track(track, message.chat.id)


async def ytdl_handler(message):
    await methods.ytdl_download_by_link(message.text, message.chat.id)


async def search_handler(message):
    search_results = await var.GeniusAPI.search(message.text)
    await bot.send_message(
        chat_id=message.chat.id,
        text=message.text + ':',
        reply_markup=inline_keyboards.search_results_keyboard(search_results))

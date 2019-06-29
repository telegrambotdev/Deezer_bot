import asyncio
import glob
import random
import string
from asyncio import sleep
from collections import namedtuple
from concurrent.futures._base import TimeoutError
from datetime import date
from functools import wraps
from time import time

import aiofiles
import aiohttp
import mutagen
from aiogram import exceptions, types
from eyed3 import id3
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from yarl import URL

from var import var


def new_callback(*args, sep=":"):
    return sep.join(str(arg) for arg in args)


def parse_callback(callback, sep=":"):
    return callback.split(sep)


def random_string(length=10):
    return "".join(random.sample(string.ascii_letters, length))


def clear_link(message):
    for entity in message.entities:
        if entity.type == "url":
            return (
                entity.url
                or message.text[entity.offset: entity.offset + entity.length]
            )


def split_string(text, divider="\n"):
    result = []
    words = text.split(divider)
    string = ""
    for i, word in enumerate(words):
        if len(string + word) > 4096:
            result.append(string)
            string = ""
        string += word + divider
        if i == len(words) - 1:
            result.append(string)
            string = ""
    return result


def already_downloading(track_id):
    status = var.downloading.get(track_id)  # pylint: disable=no-member
    if status is None or int(time()) - status > 60:
        return False
    return True


def islink(text):
    return "https://" in text or "http://" in text


Stats = namedtuple("Stats", ("downloaded_tracks",
                             "sent_tracks", "received_messages"))


def get_today_stats():
    datestr = date.today().isoformat()
    downloaded_tracks = 0
    sent_tracks = 0
    received_messages = 0
    for filename in glob.iglob(f"logs/{datestr}*file_downloads.log"):
        downloaded_tracks += sum(1 for line in open(filename))
    for filename in glob.iglob(f"logs/{datestr}*sent_messages.log"):
        sent_tracks += sum(1 for line in open(filename))
    for filename in glob.iglob(f"logs/{datestr}*messages.log"):
        received_messages += sum(1 for line in open(filename))
    return Stats(downloaded_tracks, sent_tracks, received_messages)


def encode_url(url, *args, **kwargs):
    data = {}
    for arg in args:
        if isinstance(arg, dict):
            data.update(arg)
    data.update(kwargs)
    url = URL(url).with_query(data)
    return str(url)


def calling_queue(size):
    def wrapper(coro):
        sem = asyncio.Semaphore(size)

        @wraps(coro)
        async def decorator(*args, **kwargs):
            async with sem:
                result = await coro(*args, **kwargs)
            return result

        return decorator

    return wrapper


async def download_file(url, path):
    r = await request_get(url)
    async with aiofiles.open(path, "wb") as f:
        async for chunk in r.content.iter_chunked(2048):
            await f.write(chunk)


async def get_file(url):
    r = await request_get(url)
    return await r.content.read()


async def get_album_cover_url(album_id):
    r = await request_get(f"https://api.deezer.com/album/{album_id}/image")
    return r.url.replace("120x120", "1000x1000")


def add_tags(path, track, album, image, lyrics):
    try:
        genre = album["genres"]["data"][0]["name"]
    except (KeyError, IndexError):
        genre = ""

    tag = id3.Tag()
    tag.parse(path)
    tag.artist = track["artist"]["name"]
    tag.album = track["album"]["title"]
    tag.album_artist = album["artist"]["name"]
    try:
        tag.original_release_date = track["album"]["release_date"]
        tag.recording_date = int(track["album"]["release_date"].split("-")[0])
    except Exception:
        pass
    tag.title = track["title"]
    tag.track_num = track["track_position"]
    tag.disc_num = track["disk_number"]
    tag.non_std_genre = genre
    tag.bpm = track["bpm"]
    if lyrics:
        tag.lyrics.set(lyrics)
    tag.images.set(type_=3, img_data=image, mime_type="image/png")
    tag.save()


def sc_add_tags(path, track, image, lyrics=None):
    try:
        album_title = track["publisher_metadata"]["album_title"]
    except KeyError:
        album_title = ""

    tag = id3.Tag()
    tag.parse(path)
    tag.title = track.title
    tag.artist = track.artist
    tag.album = album_title
    tag.album_artist = track.artist if album_title else ""
    tag.original_release_date = (
        track.created_at.split("T")[0].split(" ")[0].replace("/", "-")
    )
    tag.non_std_genre = track.get("genre", "")
    if lyrics:
        tag.lyrics.set(lyrics)
    if image:
        tag.images.set(type_=3, img_data=image, mime_type="image/png")
    tag.save()


def vk_add_tags(path, artist, title, album, image=None):
    tag = id3.Tag()
    tag.parse(path)
    tag.title = title
    tag.artist = artist
    if album:
        tag.album = album.title
        tag.album_artist = album.artist
    if image:
        tag.images.set(type_=3, img_data=image, mime_type="image/png")
    tag.save()


errcount = {"count": 0}


async def request_get(url, params=None, json=None, *args, **kwargs):
    retries_count = 0
    while True:
        try:
            result = await var.session.get(
                url, params=params, json=json, *args, **kwargs)
        except TimeoutError:
            if errcount["count"] > 3:
                exit(1)
            await var.session.close()
            var.session = aiohttp.ClientSession(raise_for_status=True)
            errcount["count"] += 1
        except Exception as err:
            retries_count += 1
            if retries_count > 3:
                print(url)
                raise ValueError("Number of retries exceeded") from err
        else:
            return result


async def request_post(url, *args, **kwargs):
    retries_count = 0
    while True:
        try:
            result = await var.session.post(url, *args, **kwargs)
        except TimeoutError:
            if errcount["count"] > 3:
                exit(1)
            await var.session.close()
            var.session = aiohttp.ClientSession()
            errcount["count"] += 1
        except Exception as err:
            retries_count += 1
            if retries_count > 3:
                raise ValueError("Number of retries exceeded") from err
        else:
            return result


@calling_queue(3)
async def upload_track(bot, path, title, performer, duration=None, tries=0):
    if tries > 3:
        raise RuntimeError("can't upload track")
    try:
        msg = await bot.send_audio(
            chat_id=-1001246220493,
            audio=types.InputFile(path),
            title=title,
            performer=performer,
            duration=duration,
        )
    except exceptions.RetryAfter as e:
        print(f"flood control exceeded, sleeping for {e.timeout + 10} seconds")
        await sleep(e.timeout + 10)
        return await upload_track(bot, path, title, performer, duration, tries + 1)
    except exceptions.TelegramAPIError:
        await sleep(5)
        return await upload_track(bot, path, title, performer, duration, tries + 1)
    return msg


async def launch_with_timeout(coro, timeout, on_error="raise"):
    task = asyncio.create_task(coro)
    try:
        result = await asyncio.wait_for(task, timeout)
        return result
    except TimeoutError as exc:
        if on_error == "raise":
            raise
        elif on_error == "print":
            print(exc)

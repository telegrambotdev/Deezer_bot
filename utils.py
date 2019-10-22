import asyncio
import glob
import random
import string
import shutil
import traceback
from asyncio import sleep, TimeoutError
from collections import namedtuple
from datetime import date
from functools import wraps
from time import time
from hashlib import sha256
from contextlib import suppress

import aiofiles
import aiohttp
from mutagen.flac import FLAC, Picture
from aiogram import exceptions, types
from eyed3.id3 import Tag
from yarl import URL

from var import var
import config


def sign_request(*args):
    sign_str = ':'.join(str(arg) for arg in args) + config.request_sign
    return sha256(sign_str.encode('ascii')).hexdigest()


def print_traceback(exc):
    print(''.join(traceback.format_tb(exc.__traceback__)))


async def query_answer(query, *args, **kwargs):
    try:
        await query.answer(*args, **kwargs)
    except exceptions.InvalidQueryID as exc:
        print(exc)


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
                entity.url or
                message.text[entity.offset: entity.offset + entity.length]
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


def donated_user(user_id):
    return user_id in config.admins or user_id in config.donated_users


def islink(text):
    return "https://" in text or "http://" in text


Stats = namedtuple("Stats", ("downloaded_tracks",
                             "sent_tracks", "received_messages"))


def get_today_stats():
    datestr = date.today().isoformat()
    downloaded_tracks = 0
    sent_tracks = 0
    received_messages = 0
    for filename in glob.iglob(f"logs/{datestr}/*file_downloads.log"):
        downloaded_tracks += sum(1 for line in open(filename))
    for filename in glob.iglob(f"logs/{datestr}/*sent_messages.log"):
        sent_tracks += sum(1 for line in open(filename))
    for filename in glob.iglob(f"logs/{datestr}/*messages.log"):
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
                try:
                    result = await asyncio.wait_for(coro(*args, **kwargs), 100)
                except TimeoutError as exc:
                    print_traceback(exc)
                else:
                    return result

        return decorator

    return wrapper


async def download_file(url, path):
    r = await request_get(url)
    async with aiofiles.open(path, "wb") as f:
        async for chunk in r.content.iter_chunked(2048):
            await f.write(chunk)
    return path


async def get_file(url):
    r = await request_get(url)
    return await r.content.read()


async def get_album_cover_url(album_id, res='1000x1000'):
    r = await request_get(f"https://api.deezer.com/album/{album_id}/image")
    return str(r.url).replace("120x120", res)


def add_tags(path, track, album, image, lyrics):
    try:
        genre = album["genres"]["data"][0]["name"]
    except (KeyError, IndexError):
        genre = ""

    tags = {
        'artist': track["artist"]["name"],
        'album': track["album"]["title"],
        'album_artist': album["artist"]["name"],
        'original_release_date': track["album"]["release_date"],
        'recording_date': int(track["album"]["release_date"].split("-")[0]),
        'title': track["title"],
        'track_num': track["track_position"],
        'disc_num': track["disk_number"],
        'non_std_genre': genre,
        'bpm': track["bpm"]
    }
    if path.endswith('mp3'):
        add_mp3_tags(path, tags, image, lyrics, image_mimetype='image/jpg')
    elif path.endswith('flac'):
        add_flac_tags(path, tags, image, lyrics, image_mimetype='image/jpg')


def sc_add_tags(path, track, image, lyrics=None):
    try:
        album_title = track["publisher_metadata"]["album_title"]
    except KeyError:
        album_title = ""

    tags = {
        'title': track.title,
        'artist': track.artist,
        'album': album_title,
        'album_artist': track.artist if album_title else "",
        'album_title': album_title,
        'original_release_date': (
            track.created_at.split("T")[0].split(" ")[0].replace("/", "-")),
        'non_std_genre': track.get("genre", ""),
    }
    add_mp3_tags(path, tags, image, lyrics)


def vk_add_tags(path, track, image=None):
    tags = {
        'title': track.title,
        'artist': track.artist,
    }
    if track.album:
        tags.update({'album': track.album.title})
    add_mp3_tags(path, tags, image, image_mimetype='image/jpg')


def add_mp3_tags(path, tags, image, lyrics=None, image_mimetype='image/png'):
    tag = Tag()
    tag.parse(path)
    for key, val in tags.items():
        try:
            setattr(tag, key, val)
        except Exception as e:
            print(e)
    if lyrics:
        tag.lyrics.set(lyrics)
    if image:
        tag.images.set(type_=3, img_data=image, mime_type=image_mimetype)
    tag.save(encoding='utf-8')


def add_flac_tags(path, tags, image, lyrics=None, image_mimetype='image/jpg'):
    tag = FLAC(path)
    pic = Picture()
    pic.data = image
    pic.type = 3
    pic.mime = image_mimetype
    tag.add_picture(pic)
    for key, val in tags.items():
        try:
            tag[key] = str(val)
        except Exception as e:
            print(e)
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
                print(
                    f'url=\n{url}\nparams={params}\n'
                    f'args={args}\nkwargs={kwargs}')
                print_traceback(err)
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
                print(
                    f'url=\n{url}\nargs={args}\nkwargs={kwargs}')
                raise ValueError("Number of retries exceeded") from err
        else:
            return result


@calling_queue(3)
async def upload_track(bot, path, thumb_path, title,
                       performer, duration=None, tries=0):
    if tries > 3:
        shutil.rmtree(path.rsplit('/', 1)[0])
        raise RuntimeError("can't upload track")
    try:
        msg = await bot.send_audio(
            chat_id=-1001246220493,
            audio=types.InputFile(path),
            thumb=types.InputFile(thumb_path),
            title=title,
            performer=performer,
            duration=duration,
        )
    except exceptions.RetryAfter as e:
        print(f"flood control exceeded, sleeping for {e.timeout + 10} seconds")
        await sleep(e.timeout + 10)
        return await upload_track(
            bot, path, title, performer, duration, tries + 1)
    except exceptions.TelegramAPIError:
        await sleep(5)
        return await upload_track(
            bot, path, title, performer, duration, tries + 1)
    return msg


# async def launch_with_timeout(size):
#     def wrapper(coro, timeout, on_error="raise"):
#         @wraps(coro)
#         async def decorator(*args, **kwargs):
#             task = asyncio.create_task(coro)
#             try:
#                 result = await asyncio.wait_for(task, timeout)
#                 return result
#             except TimeoutError as exc:
#                 if on_error == "raise":
#                     raise
#                 elif on_error == "print":
#                     print_traceback(exc)

#         return decorator

#     return wrapper


async def answer_empty_inline_query(query: types.InlineQuery, text: str):
    if not text:
        return await query.answer(
            results=[],
            switch_pm_text='Search',
            switch_pm_parameter='0')
    elif query.offset == 'done':
        return await query.answer(results=[])
    else:
        return False
    return True


async def delete_later(path: str, delay: int = 100):
    await asyncio.sleep(delay)
    with suppress(FileNotFoundError):
        shutil.rmtree(path.rsplit('/', 1)[0])

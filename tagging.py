from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture
from mutagen.easyid3 import EasyID3
from mutagen.id3 import (
    TIT2, TALB, TCON, TPE2,
    TPE1, TRCK, TXXX, TYER,
    TDAT, TBPM, APIC, TSRC,
    USLT)

from utils import print_traceback


def add_tags(fileobj, track_format, track, album, cover, lyrics=None):
    if track.track_position and album.tracks:
        track_n = f'{track.track_position}/{len(album.tracks.data)}'
    elif track.track_position:
        track_n = str(track.track_position)
    else:
        track_n = '1'
    genre = album.genres and album.genres.get('data')\
        and album.genres['data'][0]['name']

    tags = {
        'title': track.title,
        'artist': track.artist.name,
        'album': track.album.title,
        'album_artist': album.artist.name,
        'track_n': track_n,
        'genre': genre or '',
        'year': track.release_date.split('-')[0],
        'bpm': str(track.bpm) or '',
        'isrc': track.isrc or '',
        'explicit': str(int(track.explicit_lyrics)) or ''
    }

    if track_format == 'mp3':
        add_mp3_tags(fileobj, tags, cover, lyrics, image_mimetype='image/jpg')
    elif track_format == 'flac':
        add_flac_tags(fileobj, tags, cover, lyrics, image_mimetype='image/jpg')


def sc_add_tags(fileobj, track, cover, lyrics=None):
    try:
        album_title = track["publisher_metadata"]["album_title"]
    except KeyError:
        album_title = ""

    release_date = track.created_at.split("T")[0].split(" ")[0].replace("/", "-")
    tags = {
        'title': track.title,
        'artist': track.artist,
        'album': album_title,
        'albumartist': track.artist if album_title else "",
        'date': release_date,
        'year': release_date.split('-')[0],
        'genre': track.get("genre", ""),
    }
    add_mp3_tags(fileobj, tags, cover, lyrics)


def vk_add_tags(fileobj, track, image=None):
    tags = {
        'title': track.title,
        'artist': track.artist,
    }
    if track.album:
        tags.update({'album': track.album.title})
    add_mp3_tags(fileobj, tags, image, image_mimetype='image/jpg')


def add_mp3_tags(fileobj, tags, cover=None,
                 lyrics=None, image_mimetype='image/png'):
    handle = MP3(fileobj=fileobj)
    if 'artist' in tags:
        handle['TPE1'] = TPE1(text=tags['artist'])
    if 'title' in tags:
        handle['TIT2'] = TIT2(text=tags['title'])
    if 'album' in tags:
        handle['TALB'] = TALB(text=tags['album'])
    if 'albumartist' in tags:
        handle['TPE2'] = TPE2(text=tags['albumartist'])
    if 'genre' in tags:
        handle['TCON'] = TCON(genres=[tags['genre']])
    if 'tracknumber' in tags:
        handle['TRCK'] = TRCK(text=tags['tracknumber'])
    if 'year' in tags:
        handle['TYER'] = TYER(text=tags['year'])
    if 'date' in tags:
        handle['TDAT'] = TDAT(text=tags['date'])
    if 'bpm' in tags:
        handle['TBPM'] = TBPM(text=tags['bpm'])
    if 'isrc' in tags:
        handle['TSRC'] = TSRC(text=tags['isrc'])
    if 'explicit' in tags:
        handle['TXXX'] = TXXX(text=tags['explicit'])
    if lyrics:
        handle['USLT'] = USLT(text=lyrics)
    if cover:
        handle['APIC'] = APIC(data=cover, mime=image_mimetype)
    handle.save(fileobj)


def add_flac_tags(fileobj, tags, image, lyrics=None, image_mimetype='image/jpg'):
    handle = FLAC(fileobj)
    pic = Picture()
    pic.data = image
    pic.type = 3
    pic.mime = image_mimetype
    handle.add_picture(pic)
    for key, val in tags.items():
        try:
            handle[key] = str(val)
        except Exception as e:
            print_traceback(e)
    handle.save(fileobj)

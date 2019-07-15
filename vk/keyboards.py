from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils import new_callback


def search_results_keyboard(results, page, per_page=5):
    kb = InlineKeyboardMarkup(2)
    total_pages = ceil(len(results) / per_page)
    start = (page - 1) * per_page
    stop = start + per_page
    last_page = page == total_pages
    for i, result in enumerate(results[start: stop], start=start):
        kb.insert(InlineKeyboardButton(
            f'{i+1}. {result.artist} - {result.title}',
            callback_data=new_callback(
                'vk_track', result.full_id, 'send')))
        kb.row()
    if page != 1:
        kb.insert(InlineKeyboardButton(
            '◀️', callback_data=new_callback('vk_page', page - 1)))
    if not last_page:
        kb.insert(InlineKeyboardButton(
            '️️▶️', callback_data=new_callback('vk_page', page + 1)))
    kb.row(
        InlineKeyboardButton(
            text='Deezer ☑️', callback_data=new_callback('page', 1)),
        InlineKeyboardButton(
            text='SoundCloud ☑️️️', callback_data=new_callback('sc_page', 1)),
        InlineKeyboardButton(
            text='VK ✅', callback_data=new_callback('vk_page', 1)))
    return kb


def playlist_keyboard(playlist, show_artists=False, post=False):
    kb = InlineKeyboardMarkup(1)
    for i, track in enumerate(playlist.tracks[:97], start=1):
        if show_artists:
            kb.insert(InlineKeyboardButton(
                f'{i}.{track.artist} - {track.title}',
                callback_data=new_callback(
                    'vk_track', track.full_id, 'send')))
        else:
            kb.insert(InlineKeyboardButton(
                f'{i}. {track.title}',
                callback_data=new_callback(
                    'vk_track', track.full_id, 'send')))
    kb.insert(InlineKeyboardButton(
        'Get all tracks', callback_data=new_callback(
            'vk_playlist', playlist.full_id, 'download')))
    if post:
        kb.insert(InlineKeyboardButton(
            'Post',
            callback_data=new_callback(
                'vk_playlist', playlist.full_id, 'post')))
    kb.insert(InlineKeyboardButton(text='Close', callback_data='close'))
    return kb


def profile_keyboard(tracks, profile_id, page, per_page=7):
    kb = InlineKeyboardMarkup(2)
    total_pages = ceil(len(tracks) / per_page)
    start = (page - 1) * per_page
    stop = start + per_page
    last_page = page == total_pages

    for i, track in enumerate(tracks[start: stop], start=start):
        kb.row(InlineKeyboardButton(
            f'{i+1}. {track.artist} - {track.title}',
            callback_data=new_callback(
                'vk_track', track.full_id, 'send')))
    kb.row()
    if page != 1:
        kb.insert(InlineKeyboardButton(
            '◀️', callback_data=new_callback(
                'vk_profile_audio_page', profile_id, page - 1)))
    if not last_page:
        kb.insert(InlineKeyboardButton(
            '️️▶️', callback_data=new_callback(
                'vk_profile_audio_page', profile_id, page + 1)))
    return kb

from aiogram import types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.dispatcher.filters import Text

import db_utils
from deezer import deezer_api
import inline_keyboards
import methods
import utils
from bot import bot, dp


@dp.inline_handler(Text(startswith='.ar'))
async def artist_search(query):
    q = query.query.lstrip('.ar ')
    if utils.answer_empty_inline_query(query, q):
        return
    offset = int(query.offset) if query.offset.isdecimal() else 0

    search_results = await deezer_api.search('artist', q)
    inline_results = [InlineQueryResultArticle(
        id=result.link,
        title=result.name,
        thumb_url=result.picture_small,
        thumb_width=56,
        thumb_height=56,
        input_message_content=InputTextMessageContent(result.link)
    ) for result in search_results[offset: offset + 5]]

    if offset + 6 < len(search_results):
        next_offset = str(offset + 5)
    else:
        next_offset = 'done'
    await bot.answer_inline_query(
        inline_query_id=query.id,
        results=inline_results,
        next_offset=next_offset)


@dp.inline_handler(Text(startswith='.a'))
async def albums_search(query: types.InlineQuery):
    q = query.query.lstrip('.a ')
    if utils.answer_empty_inline_query(query, q):
        return
    offset = int(query.offset) if query.offset.isdecimal() else 0

    search_results = await deezer_api.search('album', q)
    inline_results = [InlineQueryResultArticle(
        id=result.link,
        title=result.album.title,
        description=result.artist.name,
        thumb_url=result.album.cover_small,
        thumb_width=56,
        thumb_height=56,
        input_message_content=InputTextMessageContent(result.link)
    ) for result in search_results[offset: offset + 5]]

    if offset + 6 < len(search_results):
        next_offset = str(offset + 5)
    else:
        next_offset = 'done'
    await bot.answer_inline_query(
        inline_query_id=query.id,
        results=inline_results,
        next_offset=next_offset,
        cache_time=30)


@dp.inline_handler()
async def tracks_search(query: types.InlineQuery):
    q = query.query
    if utils.answer_empty_inline_query(query, q):
        return
    offset = int(query.offset) if query.offset.isdecimal() else 0

    search_results = await deezer_api.search(q=q)
    inline_results = []

    for result in search_results[offset:offset + 5]:
        file_id = await db_utils.get_track(result.id)
        if file_id:
            inline_results.append(types.InlineQueryResultCachedAudio(
                id='done:' + utils.random_string(), audio_file_id=file_id))
        elif result.preview:
            inline_results.append(types.InlineQueryResultAudio(
                id=f'finish_download:{result.id}:{utils.random_string(4)}',
                audio_url=result.preview,
                title=result.title,
                performer=result.artist.name,
                audio_duration=30,
                reply_markup=inline_keyboards.finish_download_keyboard))

    if offset + 6 < len(search_results):
        next_offset = str(offset + 5)
    else:
        next_offset = 'done'
    await bot.answer_inline_query(
        inline_query_id=query.id,
        results=inline_results,
        next_offset=next_offset,
        cache_time=30)


@dp.chosen_inline_handler(lambda q: 'finish_download:' in q.result_id)
async def finish_download_handler(chosen_inline: types.ChosenInlineResult):
    if utils.islink(chosen_inline.result_id):
        return
    if chosen_inline.result_id.split(':')[0] == 'done':
        return
    try:
        track_id = int(chosen_inline.result_id.split(':')[1])
    except ValueError:
        track_id = int(chosen_inline.result_id.split(':')[1].split('/')[-1])
    track = await deezer_api.gettrack(track_id)
    await methods.finish_download(
        track, chosen_inline.inline_message_id, chosen_inline.from_user)

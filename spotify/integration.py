from base64 import urlsafe_b64encode

from aiohttp import web
from aiogram import types
from aiogram.dispatcher.webhook import SendMessage
from yarl import URL

from AttrDict import AttrDict
from utils import request_post, request_get
from config import spotify_client, spotify_secret
from bot import dp, bot, app, WEBHOOK_HOST
from db_utils import get_spotify_token, set_spotify_token, \
    get_spotify_refresh_token

routes = web.RouteTableDef()
AUTH = urlsafe_b64encode(
    f'{spotify_client}:{spotify_secret}'.encode()).decode()
AUTH_HEADER = {'Authorization': f"Basic {AUTH}"}
REDIRECT_URL = 'https://' + WEBHOOK_HOST + '/spotify_auth'


@dp.message_handler(commands='spotify_auth')
async def spotify_auth(message: types.Message):
    params = {
        'client_id': spotify_client,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URL,
        'scope': 'user-read-currently-playing user-modify-playback-state',
        'state': message.from_user.id}
    url = URL('https://accounts.spotify.com/authorize').with_query(params)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text='Authorize', url=str(url)))
    return SendMessage(
        message.chat.id, 'Please authorize', reply_markup=markup)


@dp.message_handler(commands='spotify_now')
async def now_playing(message: types.Message):
    token = await get_token(message.from_user.id)
    req = await request_get(
        'https://api.spotify.com/v1/me/player/currently-playing',
        headers={'Authorization': f'Bearer {token}'})
    track = AttrDict(await req.json())
    markup = types.InlineKeyboardMarkup(1)
    markup.add(types.InlineKeyboardButton(
        text='Open track', url=track.external_urls.spotify))
    return SendMessage(
        message.chat.id,
        f'Currently playing track:\n{track.artists[0].name} - {track.name}',
        reply_markup=markup)


@routes.get('/spotify_auth')
async def auth_redirect(request: web.Request):
    auth_code = request.query.get('code')
    user_id = request.query.get('state')
    if not auth_code or not user_id:
        return False

    await authorize(auth_code, user_id)

    await bot.send_message(
        int(user_id),
        'You successfuly authorized to use spotify,'
        'send /spotify_now to get info about currently playing track')
    return web.HTTPFound('tg://resolve/?domain=DeezerMusicBot')


async def authorize(code, user_id):
    data = {
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URL,
        'state': user_id}

    req = await request_post(
        'https://accounts.spotify.com/api/token',
        data=data, headers={
            **AUTH_HEADER,
            'Content-Type': 'application/x-www-form-urlencoded'})
    resp = await req.json()

    access_token = resp.get('access_token')
    refresh_token = resp.get('refresh_token')

    await set_spotify_token(
        user_id, access_token, refresh_token)


async def get_token(user_id):
    code = await get_spotify_token(user_id)
    if not code:
        await refresh_token(user_id)
    code = await get_spotify_token(user_id)
    return code


async def refresh_token(user_id):
    code = await get_spotify_refresh_token(user_id)
    await authorize(code, user_id)


app.add_routes(routes)

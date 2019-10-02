from base64 import urlsafe_b64encode

from aiohttp import web

from utils import request_post, print_traceback
from config import spotify_client, spotify_secret
from bot import bot, app, WEBHOOK_HOST
from db_utils import get_spotify_token, set_spotify_token, \
    get_spotify_refresh_token

routes = web.RouteTableDef()
AUTH = urlsafe_b64encode(
    f'{spotify_client}:{spotify_secret}'.encode()).decode()
AUTH_HEADER = {'Authorization': f"Basic {AUTH}"}
REDIRECT_URL = 'https://' + WEBHOOK_HOST + '/spotify_auth'


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

    try:
        req = await request_post(
            'https://accounts.spotify.com/api/token',
            data=data, headers={
                **AUTH_HEADER,
                'Content-Type': 'application/x-www-form-urlencoded'})
    except ValueError as exc:
        print_traceback(exc)
        return False
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
    if code:
        await authorize(code, user_id)


app.add_routes(routes)

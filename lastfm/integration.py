from aiohttp import web

from bot import bot, app
from .lastfm_api import api_request
from utils import sign_request
from db_utils import set_lastfm_token

routes = web.RouteTableDef()


@routes.get('/lastfm')
async def auth_redirect(request: web.Request):
    data = request.query.get('data')
    if data:
        data = data.split('AAA', 1)
        if len(data) == 2:
            user_id, sign = data
    token = request.query.get('token')
    if not token or not user_id or not sign or \
            sign != sign_request(user_id):
        return web.HTTPForbidden()

    session = await api_request('auth.getSession', token=token)
    await set_lastfm_token(user_id, session.session.key)

    await bot.send_message(
        int(user_id),
        'You successfuly authorized to use Last.fm '
        f'as {session.session.name}, '
        'reply /lastfm_scrobble to a song to scrobble it\n'
        'reply /lastfm_love to a song to love it on your account\n'
        'send /lastfm_logout to logout from current account')
    return web.HTTPFound('tg://resolve/?domain=DeezerMusicBot')


app.add_routes(routes)

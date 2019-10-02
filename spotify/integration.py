from aiohttp import web

from bot import bot, app
from .spotify_api import authorize

routes = web.RouteTableDef()


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


app.add_routes(routes)

from hashlib import md5

from AttrDict import AttrDict
from utils import request_get, request_post
from config import lastfm_api, lastfm_secret


api_url = 'https://ws.audioscrobbler.com/2.0/'


def sign(method, **params):
    params.pop('sk')
    data = ''.join(f"{key}{val}" for key, val in params.items())
    return md5(
        f"api_key{lastfm_api}method{method}"
        f"{data}{lastfm_secret}"
        .encode('utf-8')).hexdigest()


async def api_request(request_method, method, need_sign=True, **args):
    params = {
        'method': method,
        'api_key': lastfm_api,
        'format': 'json',
        **args}
    if need_sign:
        params['api_sig'] = sign(method, **args)
    if request_method == 'POST':
        req = await request_post(api_url, params=params)
    elif request_method == 'GET':
        req = await request_get(api_url, params=params)
    resp = await req.json()
    return AttrDict(resp)

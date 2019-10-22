from hashlib import md5

from var import var
from AttrDict import AttrDict
from utils import request_get
from config import lastfm_api, lastfm_secret


api_url = 'https://ws.audioscrobbler.com/2.0/'


def sign(method, **params):
    data = ''.join(f"{key}{val}" for key, val in params.items())
    return md5(
        f"api_key{lastfm_api}method{method}"
        f"{data}{lastfm_secret}"
        .encode('utf-8')).hexdigest()


async def api_request(method, need_sign=True, **args):
    params = {
        'method': method,
        'api_key': lastfm_api,
        'format': 'json',
        **args}
    if need_sign:
        params['api_sig'] = sign(method, **args)
    req = await request_get(api_url, params=params)
    resp = await req.json()
    return AttrDict(resp)

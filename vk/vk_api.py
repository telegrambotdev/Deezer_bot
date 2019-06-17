import re
import asyncio

# from var import var
from bs4 import BeautifulSoup
from aiohttp import ClientSession

# import config

session = ClientSession()


url = 'https://m.vk.com/audio'
search_result = re.compile(r'audio(-?\d+)_(\d+).+')
RE_LOGIN_HASH = re.compile(r'name="lg_h" value="([a-z0-9]+)"')


async def search():
    pass


def scrap_search(soup):
    results = []
    for item in soup.find_all(class_='audios_block audios_list _si_container'):
        result = {}
        result['title'] = item.find(class_='ai_title').text
        result['artist'] = item.find(class_='ai_artist').text
        match = re.match(search_result, item['id'])
        result['owner_id'] = match.group(1)
        result['id'] = match.group(2)
        results.append(result)
    return results


async def vk_login(login, password, captcha_sid=None, captcha_key=None):
    """ Авторизация ВКонтакте с получением cookies remixsid
    :param captcha_sid: id капчи
    :type captcha_key: int or str
    :param captcha_key: ответ капчи
    :type captcha_key: str
    """

    response = await session.get('https://vk.com/')
    response_text = await response.text()

    values = {
        'act': 'login',
        'role': 'al_frame',
        '_origin': 'https://vk.com',
        'utf8': '1',
        'email': login,
        'pass': password,
        'lg_h': re.match(RE_LOGIN_HASH, response_text).group(0)
    }

    if captcha_sid and captcha_key:

        values.update({
            'captcha_sid': captcha_sid,
            'captcha_key': captcha_key
        })

    response = await session.post('https://login.vk.com/', data=values)

    if 'onLoginFailed(4' in response_text:
        raise ValueError('Bad password')


async def main():
    await vk_login('79654924081', 'P8F4zJ3j7hNCI1CbDbFQOBkxgQGCvkn6')

asyncio.get_event_loop().run_until_complete(main())
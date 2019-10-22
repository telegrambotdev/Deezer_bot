from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def auth_keyboard(user_id):
    markup = InlineKeyboardMarkup()
    url = ('http://www.last.fm/api/auth/?api_key=xxx&cb='
           'https://static.138.197.203.116.clients.your-server.de/'
           f'lastfm/?user_id={user_id}')
    markup.add(InlineKeyboardButton(text='Authorize', url=url))
    return markup

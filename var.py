class Var:
    __slots__ = [
        'conn', 'db', 'spot', 'downloading',
        'session', 'CSRFToken', 'loop',
        'vk_refresh_token', 'vk_auth', 'vk_tracks']


var = Var()

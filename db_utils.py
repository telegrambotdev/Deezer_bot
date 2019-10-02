from var import var


async def set_spotify_token(user_id, token, refresh_token=None):
    await var.conn.execute(
        'set', f'user:{user_id}:spotify_token', token, EX=3599)
    if refresh_token:
        await var.conn.execute(
            'set', f'user:{user_id}:spotify_refresh_token', refresh_token)


async def get_spotify_token(user_id):
    return await var.conn.execute(
        'get', f'user:{user_id}:spotify_token')


async def get_spotify_refresh_token(user_id):
    return await var.conn.execute(
        'get', f'user:{user_id}:spotify_refresh_token')


async def get_track(track_id, quality='mp3'):
    return await var.conn.execute(
        'get', f'track:deezer:{track_id}:{quality}')


async def add_track(track_id, file_id, quality='mp3'):
    await var.conn.execute(
        'set', f'track:deezer:{track_id}:{quality}', file_id)
    await var.conn.execute('incr', 'tracks:deezer:total')
    print(f'dz:{track_id} - {file_id}')


async def get_sc_track(track_id):
    return await var.conn.execute('get', f'track:soundcloud:{track_id}')


async def add_sc_track(track_id, file_id):
    await var.conn.execute('set', f'track:soundcloud:{track_id}', file_id)
    await var.conn.execute('incr', 'tracks:soundcloud:total')
    print(f'sc:{track_id} - {file_id}')


async def get_vk_track(track_id):
    return await var.conn.execute('get', f'track:vk:{track_id}')


async def add_vk_track(track_id, file_id):
    await var.conn.execute('set', f'track:vk:{track_id}', file_id)
    await var.conn.execute('incr', 'tracks:vk:total')
    print(f'vk:{track_id} - {file_id}')


async def get_quality_setting(user_id):
    return await var.conn.execute(
        'get', f'user:{user_id}:quality_setting') or 'mp3'


async def set_quality_setting(user_id, setting):
    await var.conn.execute('set', f'user:{user_id}:quality_setting', setting)


def add_user(user, isadmin=False):
    user_indb = var.db.select('USERS', 'USER_ID', user.id)
    print(user_indb)
    if not len(user_indb):
        new_user = (
            user.id,
            user.first_name,
            user.last_name if user.last_name else 'NULL',
            user.username if user.username else 'NULL',
            0 if not isadmin else 1,
            user.language_code if user.language_code else 'NULL')
        var.db.insert('USERS', new_user)
        var.db.commit()


def get_users_count():
    var.db.execute('SELECT * FROM USERS')
    allusers = var.db.fetchall()
    return len(allusers)


if __name__ == '__main__':
    var.db.execute(
        """CREATE TABLE STATS""")

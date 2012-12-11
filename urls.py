#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

import time, json, hmac, base64, logging, hashlib

from datetime import datetime, tzinfo, timedelta

from transwarp.web import ctx, get, post, route, seeother, forbidden, jsonresult, Template
from transwarp import db

from config import APP_ID, APP_SECRET

from weibo import APIError, APIClient

import record

_TD_ZERO = timedelta(0)
_TD_8 = timedelta(hours=8)

class UTC8(tzinfo):
    def utcoffset(self, dt):
        return _TD_8

    def tzname(self, dt):
        return "UTC+8:00"

    def dst(self, dt):
        return _TD_ZERO

_UTC8 = UTC8()

def _parse_datetime(dt):
    t = datetime.strptime(dt, '%a %b %d %H:%M:%S +0800 %Y').replace(tzinfo=_UTC8)
    tp = t.timetuple()
    return time.mktime(tp), tp.tm_year * 10000 + tp.tm_mon * 100 + tp.tm_mday

def _from_weibo_user(user):
    return dict( \
        name = user.name, \
        gender = user.get('gender', ''), \
        city = user.get('city', ''), \
        province = user.get('province', ''), \
        image_url = user.get('image_url', ''), \
        profile_image_url = user.get('profile_image_url', ''), \
        avatar_large = user.get('avatar_large', ''), \
        statuses_count = user.get('statuses_count', 0), \
        friends_count = user.get('friends_count', 0), \
        followers_count = user.get('followers_count', 0), \
        verified = user.get('verified', False), \
        verified_type = user.get('verified_type', 0), \
    )

@route('/')
def index():
    i = ctx.request.input()
    client = _create_client()
    data = client.parse_signed_request(i.signed_request)
    if data is None:
        raise StandardError('Error!')
    user_id = data.get('uid', '')
    auth_token = data.get('oauth_token', '')
    if not user_id or not auth_token:
        return Template('/static/auth.html', client_id=APP_ID)

    expires = data.expires
    client.set_access_token(auth_token, expires)

    # check database if user exist:
    user = None
    users = db.select('select * from users where id=?', user_id)
    if users:
        # user exist, update if token changed:
        user = users[0]
        if auth_token != user.auth_token:
            uu = _from_weibo_user(client.users.show.get(uid=user_id))
            uu['auth_token'] = auth_token
            uu['expired_time'] = expires
            user.update(uu)
            db.update_kw('users', 'id=?', user_id, **uu)
    else:
        u = client.users.show.get(uid=user_id)
        user = _from_weibo_user(u)
        user['id'] = user_id
        user['level'] = 0
        user['weight'] = 55 if user['gender']==u'f' else 75
        user['since_id'] = ''
        user['auth_token'] = auth_token
        user['expired_time'] = expires
        db.insert('users', **user)
    img = user['avatar_large'] or user['profile_image_url'] or user['image_url']
    return Template('/static/index.html', user=user, user_img=img, signed_request=i.signed_request)

@post('/update_timeline')
@jsonresult
def update_timeline():
    i = ctx.request.input()
    client = _create_client()
    data = client.parse_signed_request(i.signed_request)
    if data is None:
        raise StandardError('Error!')
    user_id = data.get('uid', '')
    auth_token = data.get('oauth_token', '')
    if not user_id or not auth_token:
        return dict(error='bad_signature')
    expires = data.expires
    client.set_access_token(auth_token, expires)

    u = db.select('select since_id from users where id=?', user_id)[0]
    kw = dict(uid=user_id, count=100, trim_user=1)
    since_id = u.since_id
    if since_id:
        kw['since_id'] = since_id

    timeline = client.statuses.user_timeline.get(**kw)
    statuses = timeline.statuses
    count = 0
    if statuses:
        since_id = str(statuses[0].id)
        for st in statuses:
            info = record.parse(st.text)
            if info:
                t, ymd = _parse_datetime(st.created_at)
                r = dict(id=st.id, user_id=user_id, text=st.text, created_at=t, rdistance=info[0], rtime=info[1], rdate=ymd)
                if not db.select('select id from records where id=?', st.id):
                    db.insert('records', **r)
                    count = count + 1
        db.update_kw('users', 'id=?', user_id, since_id = since_id)
    return dict(count=count, since_id=since_id)

@post('/statistics')
@jsonresult
def statistics():
    i = ctx.request.input()
    client = _create_client()
    data = client.parse_signed_request(i.signed_request)
    if data is None:
        return dict(error='bad_signature')
    user_id = data.uid
    last_6m = (datetime.now() - timedelta(days=180)).timetuple()
    dt = last_6m.tm_year * 10000 + last_6m.tm_mon * 100 + last_6m.tm_mday
    return dict( \
        days = 180, \
        start = dt, \
        data = db.select('select text, rdistance, rtime, rdate from records where rdate>? and user_id=?', dt, user_id) \
    )

@post('/update')
@jsonresult
def update():
    i = ctx.request.input()
    client = _create_client()
    data = client.parse_signed_request(i.signed_request)
    if data is None:
        raise StandardError('Error!')
    user_id = data.get('uid', '')
    auth_token = data.get('oauth_token', '')
    if not user_id or not auth_token:
        return dict(error='bad_signature')
    expires = data.expires
    client.set_access_token(auth_token, expires)
    r = client.statuses.update.post(status=ctx.request['text'])
    if 'error' in r:
        return r
    return dict(result='success')

def _create_client(oauth_token=None, expires=None):
    client = APIClient(APP_ID, APP_SECRET, 'http://weiborun.sinaapp.com/callback')
    if oauth_token and expires:
        client.set_access_token(oauth_token, expires)
    return client

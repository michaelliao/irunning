#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

'''
A WSGI app for dev.

create table users (
    id varchar(50) not null,
    name varchar(50) not null,
    gender varchar(10) not null,
    city varchar(20) not null,
    province varchar(20) not null,
    image_url varchar(500) not null,
    profile_image_url varchar(500) not null,
    avatar_large varchar(500) not null,
    statuses_count bigint not null,
    friends_count bigint not null,
    followers_count bigint not null,
    verified bool not null,
    verified_type int not null,

    level int not null,
    weight int not null,
    since_id varchar(50) not null,
    auth_token varchar(2000) not null,
    expired_time real not null,
    primary key(id)
);

create table records (
    id varchar(50) not null,
    user_id varchar(50) not null,
    text varchar(200) not null,
    created_at real not null,

    rdistance real not null,
    rtime real not null,
    rdate int not null,
    primary key(id),
    index idx_user_id_rdate(user_id,rdate)
);

'''

from wsgiref.simple_server import make_server

import os, logging
logging.basicConfig(level=logging.INFO)

from transwarp import web, db

def create_app():
    db.init(db_type = 'mysql', db_schema = 'irunning', db_host = 'localhost', db_port = 3306, db_user = 'www-data', db_password = 'www-data')
    return web.WSGIApplication(('urls',), document_root=os.path.dirname(os.path.abspath(__file__)), template_engine='jinja2', DEBUG=True)

if __name__=='__main__':
    logging.info('application will start...')
    server = make_server('127.0.0.1', 80, create_app())
    server.serve_forever()

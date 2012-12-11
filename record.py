#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao'

import re, collections

Part = collections.namedtuple('Part', 'text start end length')

_PATTERN_DIGITS = ur'[0-9][0-9\.\,]*'
_PATTERN_NON_DIGITS = ur'[^0-9]'

_PATTERN_TIME_M = ur'(%s)\s*\分\钟?' % _PATTERN_DIGITS
_PATTERN_TIME_H = ur'(%s)\s*\小\时\s*%s{0,2}\s*(%s)\分\钟?' % (_PATTERN_DIGITS, _PATTERN_NON_DIGITS, _PATTERN_DIGITS)
_PATTERN_DISTANCE = ur'(%s)\s*k?m' % _PATTERN_DIGITS

_RE_TIME_M = re.compile(_PATTERN_TIME_M)
_RE_TIME_H = re.compile(_PATTERN_TIME_H)
_RE_DISTANCE = re.compile(_PATTERN_DISTANCE)

def main():
    ss = [
        u'昨天的跑步成绩是45分钟6.2km',
        u'今天25分钟跑了两千米，时速达8km/h',
        u'今天晚上跑步5公里，耗时35分钟。进入冬天，以后每周要坚持至少跑两次5公里。',
        u'终于恢复5公里跑步了！今天成绩是36分钟。',
        u'１小时零5分！9公里！',
        u'3分钟，1.2.1km',
        u'55.4分8KM!',
    ]
    for s in ss:
        print s
        print parse(s)

def parse(text):
    tl, dl = _parse_text(_pre_format(text))
    if tl and dl:
        info = _guess_info(tl, dl)
        if info:
            return info
    return None

def _guess_info(time_list, distance_list):
    for t in time_list:
        if t > 0.1:
            for d in distance_list:
                sp = d / t
                if sp > 0.05 and sp < 1.0:
                    return d, t, sp * 60
    return None

def _find_first(*ms):
    L = [999 for m in ms]
    n = 0
    for m in ms:
        if m:
            L[n] = m.start()
        n = n + 1
    l = min(L)
    if l==999:
        return (-1)
    return L.index(l)

def _parse_digit(text):
    s = text.replace(',', '')
    n1 = s.find('.')
    n2 = s.rfind('.')
    if n1==(-1):
        return float(s)
    if n1==n2:
        return float(s)
    return (-1.0)

def _parse_time(text):
    m = _RE_TIME_H.match(text)
    if m:
        return _parse_digit(m.group(1)) * 60 + _parse_digit(m.group(2))
    m = _RE_TIME_M.match(text)
    if m:
        return _parse_digit(m.group(1))
    raise ValueError(text)

def _parse_distance(text):
    m = _RE_DISTANCE.match(text)
    if m:
        return _parse_digit(m.group(1))
    raise ValueError(text)

def _parse_text(s):
    TL = []
    DL = []
    pos = 0
    while True:
        m0 = _RE_TIME_H.search(s, pos)
        m1 = _RE_TIME_M.search(s, pos)
        m2 = _RE_DISTANCE.search(s, pos)
        f = _find_first(m0, m1, m2)
        if f==(-1):
            break
        if f==0:
            pos = m0.end()
            TL.append(Part(s[m0.start():m0.end()], m0.start(), m0.end(), (m0.end()-m0.start()+1)))
        if f==1:
            pos = m1.end()
            TL.append(Part(s[m1.start():m1.end()], m1.start(), m1.end(), (m1.end()-m1.start()+1)))
        if f==2:
            pos = m2.end()
            DL.append(Part(s[m2.start():m2.end()], m2.start(), m2.end(), (m2.end()-m2.start()+1)))
    tls = [f for f in [_parse_time(p.text) for p in TL] if f > 0.0]
    dls = [f for f in [_parse_distance(p.text) for p in DL] if f > 0.0]
    if tls and dls:
        return tls, dls
    return None, None

_REPLACES = (
    (u'。', u'.'),
    (u'，', u','),
    (u'０', u'0'),
    (u'１', u'1'),
    (u'２', u'2'),
    (u'３', u'3'),
    (u'４', u'4'),
    (u'５', u'5'),
    (u'６', u'6'),
    (u'７', u'7'),
    (u'８', u'8'),
    (u'９', u'9'),
    (u'两', u'2'),
    (u'公里', u'km'),
    (u'千米', u'km'),
    (u'米', u'm'),
    (u'Ｋ', u'k'),
    (u'Ｍ', u'm'),
    (u'㏎', u'km'),
    (u'㎞', u'km'),
)

def _pre_format(text):
    s = text.lower()
    for k, v in _REPLACES:
        s = s.replace(k, v)
    return s

if __name__=='__main__':
    main()

#!/usr/bin/env python

import argparse
import sys
import subprocess
import base64
import os
import re
import urllib.parse
import unicodedata

import requests
import lxml.html

DUMP_URL = (
    "https://dumps.wikimedia.org/enwiktionary/"
    "latest/enwiktionary-latest-pages-articles.xml.bz2"
)

INITIALS = [
    'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'z',
    'h', 'c', 'h', 's', 'h', 'r', 'z', 'c', 's', 'b', 'ch', 'zh', 'sh'
]
FINALS = [
    'a', 'o', 'e', 'ai', 'ei', 'ao', 'ou', 'an', 'ang', 'en', 'eng', 'er',
    'u', 'ua', 'uo', 'uai', 'ui', 'uan', 'uang', 'un', 'ueng', 'ong', 'i',
    'ia', 'ie', 'iao', 'iu', 'ian', 'iang', 'in', 'ing', 'ü', 'üe', 'üan',
    'ün', 'iong'
]
OTHERS = [
    'a', 'o', 'e', 'ai', 'ei', 'ao', 'ou', 'an', 'ang', 'en', 'eng',
    'er', 'wu', 'wa', 'wo', 'wai', 'wei', 'wan', 'wang', 'wen', 'weng', 'yi',
    'ya', 'ye', 'yao', 'you', 'yan', 'yang', 'yin', 'ying', 'yu', 'yue',
    'yuan', 'yun', 'yong'
]


INITIALS.sort(key=len, reverse=True)
FINALS.sort(key=len, reverse=True)
OTHERS.sort(key=len, reverse=True)

r = '(?:%s)(?:%s)|(?:%s)' % ('|'.join(INITIALS), '|'.join(FINALS), '|'.join(OTHERS))
r2 = '^((?:%s)(?:%s)|(?:%s))+$' % ('|'.join(INITIALS), '|'.join(FINALS), '|'.join(OTHERS))
UNICODE_ACCENT_TO_TONE_NUMBER = {
        ' WITH MACRON': '1',
        ' WITH ACUTE': '2',
        ' WITH CARON': '3',
        ' WITH GRAVE': '4',
}

def pinyin_unicode_to_ascii(pinyin_unicode):
    no_tones = ''
    tones = []
    for c in pinyin_unicode:
        n = unicodedata.name(c)
        for accent in UNICODE_ACCENT_TO_TONE_NUMBER:
            if accent in n:
                n = n.replace(accent, '')
                tones.append(UNICODE_ACCENT_TO_TONE_NUMBER[accent])
        no_tones += unicodedata.lookup(n)
    pinyin = re.findall(r, no_tones)
    return pinyin, no_tones, tones


def get_cached(url, cache_dir):
    try:
        if cache_dir:
            b64 = base64.b64encode(url.encode()).decode().replace('/', '_')
            fname = os.path.join(cache_dir, b64)
            with open(fname) as f:
                return f.read()
    except IOError:
        pass

    with open(fname, 'w') as f:
        t = requests.get(url).text
        f.write(t)
        return t

def download_from_wikimedia(fname, out_path, cache_dir):
    url = 'https://commons.wikimedia.org/wiki/File:' + fname
    h = lxml.html.fromstring(get_cached(url, cache_dir))
    try:
        target_url = h.xpath('//audio/source/@src')[0]
    except IndexError:
        sys.stderr.write("Couldn't find audio at url=%r\n" % url)
        return
    fn = urllib.parse.unquote(target_url.split('/')[-1])
    if not os.path.exists(os.path.join('output', fn)):
        subprocess.call(['wget', '-q', target_url, '-O', out_path])

def main(out_dir, cache_dir):
    cmd = (
        "curl %s | bzcat | egrep -i --only-matching 'zh-[^.=]*\.ogg'"
    ) % DUMP_URL
    fnames_f = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE
    ).stdout
    for fname in fnames_f:
        fname = fname.decode()
        pinyin_unicode = fname.split('/')[-1].split('-')[1].split('.')[0]
        pinyin, no_tones, tones = pinyin_unicode_to_ascii(pinyin_unicode)
        as_ascii_joined = '_'.join([''.join(x) for x in zip(pinyin, tones)])
        out_path = os.path.join(out_dir, '%s.ogg' % as_ascii_joined)
        if pinyin and re.match(r2, no_tones) and len(tones) == len(pinyin):
            download_from_wikimedia(fname, out_path, cache_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache-dir')
    parser.add_argument('--out-dir')
    args = parser.parse_args()
    main(**args.__dict__)

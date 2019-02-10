#!/usr/bin/env python

"""Downloads Chinese speech samples with Pinyin from en.wiktionary.org."""

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

# NOTE: those three lists need to be kept sorted by length, otherwise regexes
# won't work properly. See: https://stackoverflow.com/a/54610421/1091116
INITIALS = [
    'ch', 'sh', 'zh', 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k',
    'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'x', 'z'
]

FINALS = [
    'iang', 'iong', 'uang', 'ueng', 'ang', 'eng', 'ian', 'iao', 'ing',
    'ong', 'uai', 'uan', 'üan', 'ai', 'an', 'ao', 'ei', 'en', 'er',
    'ia', 'ie', 'in', 'iu', 'ou', 'ua', 'ui', 'un', 'uo', 'üe', 'ün',
    'a', 'e', 'i', 'o', 'u', 'ü'
]

# Those syllabels stand on their own and aren't a combination of finals and
# initials. Also sorted by length.
OTHERS = [
    'wang', 'weng', 'yang', 'ying', 'yong', 'yuan', 'ang', 'eng',
    'wai', 'wan', 'wei', 'wen', 'yan', 'yao', 'yin', 'you', 'yue',
    'yun', 'ai', 'an', 'ao', 'ei', 'en', 'er', 'ou', 'wa', 'wo', 'wu',
    'ya', 'ye', 'yi', 'yu', 'a', 'e', 'o'
]

PINYIN_SINGLE_REGEX = '(?:%s)(?:%s)|(?:%s)' % (
    '|'.join(INITIALS), '|'.join(FINALS), '|'.join(OTHERS)
)

# According to unicodedata.name, 'ǚ' is:
# 'LATIN SMALL LETTER U WITH DIAERESIS AND CARON'. If we then remove the
# 'AND CARON' from its name and do unicodedata.lookup(new_name), we'll strip
# out the tone mark, making it ü. Those are mappings between the parts of names
# and tone numbers - if we find one of those, this syllabel has that tone.
UNICODE_ACCENT_TO_TONE_NUMBER = {
        'MACRON': '1',
        'ACUTE': '2',
        'CARON': '3',
        'GRAVE': '4',
}


def pinyin_unicode_to_digits(pinyin_unicode):
    """Convert Pinyin that has tone encoded in diacritic marks to one that has
    tones encoded in ASCII. For example:
    >>> pinyin_unicode_to_digits('nǚrén')
    (['nü', 'ren'], 'nüren', ['3', '2'])
    """
    no_tones = ''
    tones = []
    for c in pinyin_unicode:
        n = unicodedata.name(c)
        for accent in UNICODE_ACCENT_TO_TONE_NUMBER:
            if accent in n:
                n = n.replace(' WITH %s' % accent, '')
                n = n.replace(' AND %s' % accent, '')
                tones.append(UNICODE_ACCENT_TO_TONE_NUMBER[accent])
        no_tones += unicodedata.lookup(n)
    pinyin_parts = re.findall(PINYIN_SINGLE_REGEX, no_tones)
    return pinyin_parts, no_tones, tones


def get_cached(url, cache_dir):
    """Download a file, optionally trying to read it from cache_dir instead if
    that variable is not empty."""
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
    """Visit Wikimedia Commons page for a given file, find a hotlink to the
    resource and download it to the out_path if it's not there already."""
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


def download_if_valid_pinyin(out_dir, cache_dir, fname):
    """For a given filename, see if we can parse its Pinyin and if that's the
    case, try to save it to out_dir in a form easier to parse."""
    pinyin_unicode = fname.split('/')[-1].split('-')[1].split('.')[0]
    pinyin_items, no_tones, tones = pinyin_unicode_to_digits(pinyin_unicode)
    as_ascii_joined = '_'.join([''.join(x) for x in zip(pinyin_items, tones)])
    out_path = os.path.join(out_dir, '%s.ogg' % as_ascii_joined)
    if re.match('^(%s)+$' % PINYIN_SINGLE_REGEX, no_tones):
        if pinyin_items and len(tones) == len(pinyin_items):
            download_from_wikimedia(fname, out_path, cache_dir)


def main(out_dir, cache_dir):
    """Download the latest English Wiktionary snapshot, grepping for references
    to zh-(pinyin).ogg files, then try to parse and download them."""
    cmd = (
        # "bzcat wiktionary/enwiktionary-20190201-pages-meta-current.xml.bz2 |"
        "curl %(url)s | bzcat | "
        "egrep -i --only-matching 'zh-[^.=]*\\.ogg'"
    ) % {'url': DUMP_URL}
    fnames_f = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE
    ).stdout
    for fname in fnames_f:
        download_if_valid_pinyin(out_dir, cache_dir, fname.decode().strip())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir')
    parser.add_argument('--out-dir')
    args = parser.parse_args()
    main(**args.__dict__)

#!/usr/bin/env python

import sqlite3
import json
import re
import subprocess
import sys
import os
import random

from flask import session, Flask, request, send_from_directory
from flask_session.__init__ import Session

app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

devnull = open(os.devnull)

conn = sqlite3.connect('anki/collection.anki2')
flds = []
for row in conn.execute('select flds from notes order by random()'):
    flds.append(row[0])

with open('anki/media') as f:
    j = json.loads(f.read())
    j_reversed = {value: key for key, value in j.items()}


@app.route('/sample/<path:path>')
def send_sample(path):
    return send_from_directory('anki', path)

@app.route('/')
def main():
    ret = ''
    if request.args.get('tone_input') and 'tones' in session:
        if session['tones'] == request.args['tone_input']:
            ret = 'Dobrze'
        else:
            ret = session['tones']
    fld = random.choice(flds)
    path = j_reversed[fld[fld.rfind('['):].split(':')[1].split(']')[0]]
    fld_tones = re.findall('"[^"]+"', fld)
    tones = ''.join([x[-2] for x in fld_tones if x != '"colored"'])
    session['tones'] = tones
    return ret + '''
        <br />
        <audio autoplay="autoplay" controls>
        <source src="/sample/%s" type="audio/mpeg">
        </audio>
        <form><input name="tone_input" /></form>
    ''' % path

if __name__ == '__main__':
    app.run(host='0.0.0.0')

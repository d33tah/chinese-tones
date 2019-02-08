#!/usr/bin/env python

import sqlite3
import json
import re
import subprocess
import sys
import os
import random

from flask import session, Flask, request, send_from_directory, render_template
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

    # Compare answer with the one from the previous question
    answer = 'Welcome to Chinese Tones!'
    if request.args.get('tone_input') and 'tones' in session:
        if session['tones'] == request.args['tone_input']:
            answer = 'OK'
        else:
            answer = 'Nope, ' + session['tones']

    fld = random.choice(flds)

    media_file = fld[fld.rfind('['):].split(':')[1].split(']')[0]
    character = media_file.split('.')[0]

    path = j_reversed[media_file]
    fld_tones = re.findall('"[^"]+"', fld)
    tones = ''.join([x[-2] for x in fld_tones if x != '"colored"'])

    session['tones'] = tones

    return render_template('main.html',
        path='/sample/' + path,
        answer=answer,
        placeholder=('?' * len(tones)),
        character=character,
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0')

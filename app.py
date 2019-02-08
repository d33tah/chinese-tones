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

    score = session.get('score', 0)
    num_questions = session.get('num_questions', 0)
    
    # build answer string
    d = {}
    for key, value in sorted(request.args.items()):
        if not key.startswith('answer-'):
            continue
        _, n, tone = key.split('-')
        d[n] = tone
    upto_biggest_answered = range(int(max(d.keys() or [-1]))+1)
    u_answer = ''.join([d.get(str(i), '?') for i in upto_biggest_answered])

    # Compare answer with the one from the previous question
    answer = 'Welcome to Chinese Tones!'
    if u_answer and 'tones' in session:
        add_score = 0
        if session['tones'] == u_answer:
            answer = 'OK'
            score += 1
        else:
            answer = 'Nope, ' + session['tones']
        num_questions += 1

    session['score'] = score
    session['num_questions'] = num_questions

    fld = random.choice(flds)

    media_file = fld[fld.rfind('['):].split(':')[1].split(']')[0]
    character = media_file.split('.')[0]

    path = j_reversed[media_file]
    fld_tones = re.findall('"[^"]+"', fld)
    tones = ''.join([x[-2] for x in fld_tones if x != '"colored"'])

    session['tones'] = tones

    perc = '%0.2f%%' % (100.0 * score/num_questions) if num_questions else '0%'
    return render_template('main.html',
        path='/sample/' + path,
        answer=answer,
        placeholder=('?' * len(tones)),
        character=character,
        score=score,
        num_questions=num_questions,
        perc=perc,
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0')

#!/usr/bin/env python3

import os
import random

from flask import session, Flask, request, send_from_directory, render_template
from flask_session.__init__ import Session

app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

devnull = open(os.devnull)
sounds = os.listdir('sounds')
TONE_NAMES = {1: 'flat', 2: 'rising', 3: 'dipping', 4: 'falling', 5: 'neutral'}


@app.route('/sample/<path:path>')
def send_sample(path):
    return send_from_directory('sounds', path)


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
        u_answer = u_answer[:len(session['tones'])]
        if session['tones'] == u_answer:
            answer = 'OK'
            score += 1
        else:
            answer = 'Nope, ' + session['tones'] + '. Rehearse <a href="'
            answer += session['previous_sample'] + '">here</a>.'
        num_questions += 1

    session['score'] = score
    session['num_questions'] = num_questions

    path = '/sample/%s' % random.choice(sounds)
    pinyin_with_tones = path.split('/')[-1][:-len('.ogg')].split('_')
    tones = ''.join(x[-1] for x in pinyin_with_tones)
    pinyin_without_tones = [x[:-1] for x in pinyin_with_tones]

    session['tones'] = tones
    session['previous_sample'] = path

    perc = '%0.2f%%' % (100.0 * score/num_questions) if num_questions else '0%'
    return render_template(
        'main.html',
        path=path,
        answer=answer,
        placeholder=('?' * len(tones)),
        pinyin_without_tones=pinyin_without_tones,
        score=score,
        num_questions=num_questions,
        perc=perc,
        tones=TONE_NAMES,
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0')

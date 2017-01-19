import logging
import random
import os

import boto3

from flask import Flask, json, render_template
from flask_ask import Ask, request, session, question, statement, context, audio, current_stream

app = Flask(__name__)
ask = Ask(app, "/")
logger = logging.getLogger()
logging.getLogger('flask_ask').setLevel(logging.INFO)

BUCKET_NAME = 'alexa-simpsons'
simpsons_filenames = []
client = boto3.client(
    's3',
    aws_access_key_id=os.environ['S3_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET']
)
for key in client.list_objects(Bucket=BUCKET_NAME)['Contents']:
    simpsons_filenames.append(key['Key'])

def get_url(filename):
    return client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': BUCKET_NAME,
            'Key': filename
        }
    )

@ask.launch
def launch():
    random_episode_key = random.choice(simpsons_filenames)
    episode_title = random_episode_key[13:-4]
    stream_url = get_url(random_episode_key)
    card_title = 'Simpsons Audio'
    text = "Playing: {}".format(episode_title)
    return audio(text).simple_card(card_title, text).play(stream_url)

@ask.intent('AMAZON.NextIntent')
def next_episode():
    random_episode_key = random.choice(simpsons_filenames)
    episode_title = random_episode_key[13:-4]
    stream_url = get_url(random_episode_key)
    card_title = 'Simpsons Audio'
    text = "Playing: {}".format(episode_title)
    return audio(text).simple_card(card_title, text).play(stream_url)

@ask.intent('AMAZON.PauseIntent')
def pause():
    return audio('Paused the stream.').stop()

@ask.intent('AMAZON.ResumeIntent')
def resume():
    return audio('Resuming.').resume()

@ask.intent('AMAZON.StopIntent')
def stop():
    return audio('stopping').clear_queue(stop=True)



# optional callbacks
@ask.on_playback_started()
def started(offset, token):
    _infodump('STARTED Audio Stream at {} ms'.format(offset))
    _infodump('Stream holds the token {}'.format(token))
    _infodump('STARTED Audio stream from {}'.format(current_stream.url))


@ask.on_playback_stopped()
def stopped(offset, token):
    _infodump('STOPPED Audio Stream at {} ms'.format(offset))
    _infodump('Stream holds the token {}'.format(token))
    _infodump('Stream stopped playing from {}'.format(current_stream.url))


@ask.on_playback_nearly_finished()
def nearly_finished():
    _infodump('Stream nearly finished from {}'.format(current_stream.url))

@ask.on_playback_finished()
def stream_finished(token):
    _infodump('Playback has finished for stream with token {}'.format(token))

@ask.session_ended
def session_ended():
    return "", 200

def _infodump(obj, indent=2):
    msg = json.dumps(obj, indent=indent)
    logger.info(msg)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

import logging
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
    card_title = 'Audio Example'
    text = 'Welcome to an audio example. You can ask to begin demo, or try asking me to play the sax.'
    prompt = 'You can ask to begin demo, or try asking me to play the sax.'
    return question(text).reprompt(prompt).simple_card(card_title, text)


@ask.intent('DemoIntent')
def demo():
    speech = "Simpsons Season 4 Episode 15 - I love lisa"
    stream_url = get_url('the simpsons s04 - e15 I Love Lisa.mp3')
    return audio(speech).play(stream_url)


# 'ask audio_skil Play the sax
@ask.intent('SaxIntent')
def george_michael():
    speech = 'yeah you got it!'
    stream_url = 'https://ia800203.us.archive.org/27/items/CarelessWhisper_435/CarelessWhisper.ogg'
    return audio(speech).play(stream_url)


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
    app.run(debug=False)

import logging
import random
import os

import boto3
import dataset

from flask import Flask, json, render_template
from flask_ask import Ask, request, session, question, statement, context, audio, current_stream, convert_errors

app = Flask(__name__)
ask = Ask(app, "/")
logger = logging.getLogger()
logging.getLogger('flask_ask').setLevel(logging.INFO)

db = dataset.connect('sqlite:///alexa-simpsons.db')
episodes = db['episodes']

client = boto3.client(
    's3',
    aws_access_key_id=os.environ['S3_KEY'],
    aws_secret_access_key=os.environ['S3_SECRET']
)
BUCKET_NAME = 'alexa-simpsons'


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
    all_episodes = list(episodes.all())
    random_episode = random.choice(all_episodes)
    stream_url = get_url(random_episode['key'])
    card_title = 'Simpsons Audio'
    text = "Playing: Season {}, Episode {}, {}".format(random_episode['season'], random_episode['episode'], random_episode['title'])
    return audio(text).simple_card(card_title, text).play(stream_url)

@ask.intent('AMAZON.NextIntent')
def next_episode():
    all_episodes = list(episodes.all())
    random_episode = random.choice(all_episodes)
    stream_url = get_url(random_episode['key'])
    card_title = 'Simpsons Audio'
    text = "Playing: Season {}, Episode {}, {}".format(random_episode['season'], random_episode['episode'], random_episode['title'])
    return audio(text).simple_card(card_title, text).play(stream_url)

@ask.intent('SeasonIntent', convert={'season': int})
def season(season):
    if 'season' in convert_errors:
        return question("Can you please repeat the season? We only accept up to season 10.")
    season_episodes = episodes.find(season=season)
    if len(season_episodes) < 1:
        return question("Can you please try another season? We do not have that season.")
    random_episode = random.choice(season_episodes)
    stream_url = get_url(random_episode['key'])
    card_title = 'Simpsons Audio'
    text = "Playing: Season {}, Episode {}, {}".format(random_episode['season'], random_episode['episode'], random_episode['title'])
    return audio(text).simple_card(card_title, text).play(stream_url)

@ask.intent('SeasonEpisodeIntent', convert={'season': int, 'episode': int})
def season_episode(season, episode):
    if 'season' in convert_errors:
        return question("Can you please repeat the season? We only accept up to season 10.")
    if 'episode' in convert_errors:
        return question("Can you please repeat the episode?")
    season_episode = episodes.find_one(season=season, episode=episode)
    if not season_episode:
        return question("Can you please try another season and episode? We do not have that episode.")
    stream_url = get_url(season_episode['key'])
    card_title = 'Simpsons Audio'
    text = "Playing: Season {}, Episode {}, {}".format(season_episode['season'], season_episode['episode'], season_episode['title'])
    return audio(text).simple_card(card_title, text).play(stream_url)

@ask.intent('FastForwardIntent', convert={'seconds': int})
def fast_forward(seconds):
    print('current_stream fast_forward request')
    print(request)
    print('current_stream fast_forward session')
    print(session)
    if not current_stream:
        return statement("You are not currently playing anything.")
    if 'seconds' in convert_errors:
        return question("Can you please repeat the seconds?")
    current_time = current_stream.offsetInMilliseconds
    new_time = current_time + (seconds * 1000)
    return audio("").play(current_stream.url, offset=new_time)

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

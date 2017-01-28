Alexa Simpsons
---

A simple alexa skill for listening to simpsons episodes from seasons 1-10

The way this works is that 

1. Connect to a sqlitedb with information of all the episodes from seasons 1 - 10
2. Connect to s3 bucket with the audio files for all the episodes
3. When prompted through alexa, either return random episode audio url or specific episode audio url

Expected prompts (assuming your skill word is homer)
---
- alexa, ask homer to play season 3 episode 5
- alexa, ask homer to start
- alexa, ask homer to play season 7

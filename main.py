import os
import json
from flask import Flask, request, render_template
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

from google.oauth2 import service_account

private_key = """

{
  "type": "service_account",
  "project_id": "black-terminus-231919",
  "private_key_id": "9421a3be78c37c2049d918190297caa8bdd1fee4",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC1VsZbswNQ93dW\nz7NOnrkmaIyX3pVzaofPNdlgy1DXToLawnse3vU4yk5P6+8sKSz6zTbydjlBErjO\nwgfsF5Qe8x39vPSZhndH9DeNTq4ML1T62GQCyQJLOEUKhKBHqPEXg7320k396uBb\nbKUmwwgsYZdQBO0vJZ6/rb112Yki2klAv7M/lTTmjgMkD5pw+ZkKrS5Vn4WmNSTB\nV2WsgjIsfQyT99mqzKkTN6eeU5aYzxsLHVZLNa6AGNYqiZJFzOrdoTEos9Gxiy0C\nV+eCvJI0eoCroX2srlYZVKVLHLHalLJ/EfiW/ZQhi8honGe9gg2xG+JF6VZaGgX8\nw1ZYJDpzAgMBAAECggEAEG+vO/mI9+pDkVqdvycI03qPdREnjQC0vZXSawESsJPn\nrWoKRyfgpIdFu4hq3cmqT4iROJR5p7R0NsgEeCRCTd8tspAmwCbyzH1OGbXuIExG\nphPoq2NKchnwEWjTBEZuT897mjxr9Z4NPDbSmKWofylQpzVDGvkMdLA2kiYnqsEP\nH2FdriYUsNFeNdQJcBRGs0QyfRYyMCeclXkVHEtkgmpK6ymUPREa+9/cTpos3OYO\nsSiemieJ500iuEQzd/XnXkvW7g/hUEpR1/ld8YbQZasv/oHsdCBgto7hm4IEqLuH\nV1VEsp3kX0rIpFc/kjdZHYUR1wA7JsMl//b0ZaSMCQKBgQD7NIUsmuFLOmo8KMBW\nPaeIb7+pHo5Osd2srLc9RHSj+vcSYXdLVkNvgN6rGd9r+znEDeYqBizdCVLvKJL0\nU/6vjCc3yAKRvdzWx+BycPgHaI2xmupmTrCck8Dx6LM9+Zus3catTmMbcXv0SzIy\n6rovmKdEXq8WRsxH3EV5xlCQywKBgQC4zNzs0TP1jpoPuFHnxnFMOFeKfUcaIvWH\ngWTTJxPoABX9wTHPBqrhine4f5svQnWaQNs3J3FTFy74d0hNpiBnBheCtW9yaRO+\ngH1ACWGup0+bitNHLF2bV7m4EK5qA2YRMWsRtjNxVPTYipGJHxulqMU0vNp/cRrB\nZ5EaWfKP+QKBgQCfF/on78czv8E8bIqzk8Sg0jVORH3YNSmxjIlYkhxVJkKIL5Y/\n7lgzLCjZsD8hwjApjKvyfYq4Solt0gKQHwoz382OtGt8JgTROjFaCVXsSzlB/Fzr\ngna0E5elHb03SPhhGOwVIon9/XeFloIqYSKdtk5pLJYyw4/pCwYtQ34O1QKBgQCW\nZ43rZD0wvvYekzp+NCFkEnsVKO8kk41X0vUXcbee2+sKEyIRx/BuDj9wNtM7vJBw\nkhaYpg5yvOyqppJ/OBUpJGkgJcDl0iWSp4rJApmxB1UgV/Wq+K3az6RE7ba2a7u3\nhIwK50qpE6cPUoAupNXglyKh0I7YqFpJTJxpYQmtKQKBgG0//GI0/7OiV7HW8YuI\nS5XcVN2tmW2UiOewzsoTppqr33FS2P4p3vpyYSoxyAjJcHyXqxoVBz8cYUozeuJl\n0ra3xvAHnmu2b8t2klM7Sg98ACWF5EJge+I1hIvqFDVyTglUprW7oOYHgbzUWlWe\n6SEnKlkBSq+LVXa6vxgCrKuX\n-----END PRIVATE KEY-----\n",
  "client_email": "hapi-888@black-terminus-231919.iam.gserviceaccount.com",
  "client_id": "101811183768993227381",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/hapi-888%40black-terminus-231919.iam.gserviceaccount.com"
}
"""


# Allows to listen to specified tweets as they are posted
import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream, API, Cursor
import twitter_credentials 


# For specific user interaction
class TwitterClient():
    def __init__(self, twitter_user):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)    
        self.twitter_user = twitter_user
    
    # Gets specified number of tweets from user
    def get_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            if(tweet.lang == "en"):
                tweets.append(tweet)
        return tweets 

# Class for general Twitter authentication
class TwitterAuthenticator():
    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, 
                            twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, 
                                twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth


info = json.loads(private_key, strict=False)
credentials = service_account.Credentials.from_service_account_info(info)

from google.cloud.language import types

app = Flask(__name__)

# Class for streaming and processing live tweets
# ** Not currently in use 
class TwitterStreamer():
    # Constructor
    def __init__(self):
        self.twitter_authenticator = TwitterAuthenticator()   
 
    # Handles Twitter authentication and connection to Twitter Streaming API
    def stream_tweets(self, hash_tag):   
        auth = self.twitter_authenticator.authenticate_twitter_app()
        api = tweepy.API(auth,wait_on_rate_limit=True)
        tweets = []
        for tweet in tweepy.Cursor(api.search,q=hash_tag,count=1,lang="en").items():
            tweets.append(tweet.text)
        return tweets
    
    
# Basic listener class that just prints received tweets to stdout 
# Not currently in use
class TwitterListener(StreamListener):
    # Overriden method which takes in data streamed in from StreamListener
    def on_status(self, status):
        try: 
            print(status.text)
        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True       

    # Overriden method which happens if error occurs
    def on_error(self, status):
        # If we are throttling Twitter API
        if status == 420:
            return False
        print(status)


@app.route('/')
def my_form():
        return render_template('index.html')

@app.route('/', methods=['POST'])
def my_form_post():
        #Instantiates a client
        client = language.LanguageServiceClient(credentials=credentials)

        # The text to analyze
        text = request.form['text']
        overall_sentiment = 0

        if text[0] == "@":
            # Creates twitter client from user name
            user = TwitterClient(text)

            # Retrieves past 200 tweets
            tweets = user.get_tweets(50)

            for tweet in tweets:
                # Future optimisation includes filtering all text for erroenous data
                print(tweet.text)
                document = types.Document(content=tweet.text, type=enums.Document.Type.PLAIN_TEXT)
                overall_sentiment +=  (client.analyze_sentiment(document=document).document_sentiment).score

            sentiment_score = overall_sentiment/50
        
            return str(sentiment_score) 
        elif text[0] == "#":
            auth = tweepy.OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
            auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
            api = tweepy.API(auth,wait_on_rate_limit=True)
            for tweet in tweepy.Cursor(api.search,q=text,count=1,lang="en", since="2019-02-16").items(1):
                # Future optimisation includes filtering all text for erroenous data
                print("what")
                print(tweet.text)
                document = types.Document(content=tweet.text, type=enums.Document.Type.PLAIN_TEXT)
                overall_sentiment +=  (client.analyze_sentiment(document=document).document_sentiment).score

            sentiment_score = overall_sentiment/1
        
            return str(sentiment_score) 

        else:
            print("Invalid input")

def main():
    app.run(host='127.0.0.1', port=8080, debug=True)

main()

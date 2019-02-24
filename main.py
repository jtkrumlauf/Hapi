import os
import json
from flask import Flask, request, render_template
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from google.oauth2 import service_account

# Allows to listen to specified tweets as they are posted
import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream, API, Cursor
import twitter_credentials 

app = Flask(__name__)

private_key = """
{
}

"""
info = json.loads(private_key, strict=False)
credentials = service_account.Credentials.from_service_account_info(info)


AVG_SENTIMENT = 0.0
MOST_POSITIVE_TWEET = ""
MOST_NEGATIVE_TWEET = ""
NUM_POS_TWEETS = 0
NUM_NEG_TWEETS = 0
NUM_TWEETS_OMITTED = 0
MOST_POSITIVITY= -1
MOST_NEGATIVITY = 1
NUM_NEUTRAL = 0


# Removes unecessary data from tweet
def filter_tweet(tweet):
    tweet_list = tweet.split(" ")
    print("Original tweet_list: " + str(tweet_list))
    removals = []
    removal_count = 0
    for token in tweet_list:
        if len(token) == 0:
            removal_count += 1
            continue
        if token == "RT" or token[0] == "@": 
            removals.append(removal_count)
        elif len(token) >= 5: 
            if token[0:4] == "http":
                removals.append(removal_count)
        removal_count += 1
    print("Removals: " + str(removals))
    for ind in reversed(removals):
        del tweet_list[ind]
    print("Filtered tweet list: " + str(tweet_list))
    return ' '.join(tweet_list)

# For specific user interaction
class TwitterClient():
    def __init__(self, twitter_user):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)    
        self.twitter_user = twitter_user
    
    # Gets specified number of tweets from user
    def get_tweets(self, num_tweets):
        global NUM_TWEETS_OMITTED
        tweets = []
        count = 0
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            if(tweet.lang == "en" and len(tweet.text) != 0):
                print("Original tweet: " + tweet.text)
                filtered = filter_tweet(tweet.text)
                print("Filtered tweet: " + filtered)
                tweets.append(filtered)
                count += 1
            else:
                print("Omitted Tweet: " + tweet.text)
                NUM_TWEETS_OMITTED += 1
        return tweets, count 

# Class for general Twitter authentication
class TwitterAuthenticator():
    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, 
                            twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, 
                                twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth


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

"""
    Absolutely abhorrent method that is only here because we don't understand
    how flask works. Sorry
"""
def setGlobals():
        global AVG_SENTIMENT
        global MOST_POSITIVE_TWEET
        global MOST_NEGATIVE_TWEET
        global NUM_POS_TWEETS
        global NUM_NEG_TWEETS
        global NUM_TWEETS_OMITTED
        global MOST_POSITIVITY
        global MOST_NEGATIVITY
        global NUM_NEUTRAL
        AVG_SENTIMENT = 0.0
        MOST_POSITIVE_TWEET = ""
        MOST_NEGATIVE_TWEET = ""
        NUM_POS_TWEETS = 0
        NUM_NEG_TWEETS = 0
        NUM_TWEETS_OMITTED = 0
        MOST_POSITIVITY= -1
        MOST_NEGATIVITY = 1
        NUM_NEUTRAL = 0

"""
    Given the last several tweets from a user or hashtag, determine the
    sentiment for each one to compute the overall sentiment of their tweets
"""
def get_overall_sentiment(tweets, client):
    global NUM_POS_TWEETS
    global NUM_NEG_TWEETS
    global NUM_NEUTRAL
    global MOST_POSITIVITY
    global MOST_POSITIVE_TWEET
    global MOST_NEGATIVITY
    global MOST_NEGATIVE_TWEET

    overall_sentiment = 0
    for tweet in tweets:
        # Future optimisation includes filtering all text for erroenous data
        document = types.Document(content=tweet, type=enums.Document.Type.PLAIN_TEXT)
        inc_sentiment = (client.analyze_sentiment(document=document).document_sentiment).score
        if inc_sentiment > 0:
            NUM_POS_TWEETS += 1
        elif inc_sentiment < 0:
            NUM_NEG_TWEETS += 1
        elif inc_sentiment == 0:
            NUM_NEUTRAL += 1
        if(inc_sentiment > MOST_POSITIVITY):
            MOST_POSITIVITY = inc_sentiment
            MOST_POSITIVE_TWEET = tweet
        if(inc_sentiment < MOST_NEGATIVITY):
            MOST_NEGATIVITY = inc_sentiment
            MOST_NEGATIVE_TWEET = tweet
        overall_sentiment += inc_sentiment
    return overall_sentiment

"""
    Given a hashtag and number of tweets, returns at most that many tweets
    and however many tweets were considered
"""
def get_hashtag_tweets(num, hashtag):
    auth = tweepy.OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
    auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth,wait_on_rate_limit=True)
    tweets = []
    count = 0
    for tweet in tweepy.Cursor(api.search,q=hashtag,count=50,lang="en", since="2019-02-16").items(50):
        if( tweet.lang == "en" and len(tweet.text) != 0):
            print("Original tweet: " + tweet.text)
            filtered = filter_tweet(tweet.text)
            print("Filtered tweet: " + filtered)
            tweets.append(filtered)
            count += 1
    return tweets, count

"""
    Given the sentiment score for a set of tweets, formats the return string
    with all necessary global statistics 
"""
def get_return_string(overall_sentiment, count):
    global AVG_SENTIMENT
    global MOST_POSITIVE_TWEET
    global MOST_NEGATIVE_TWEET
    global NUM_POS_TWEETS
    global NUM_NEG_TWEETS
    global NUM_TWEETS_OMITTED
    global MOST_POSITIVITY
    global MOST_NEGATIVITY
    global NUM_NEUTRAL

    sentiment_score = overall_sentiment/count
    sentiment_percentage = 100 * sentiment_score
    sentiment_print = ""
    if sentiment_percentage < 0.0:
        sentiment_print = str(sentiment_percentage*(-1)) + "% Negative" 
    else:
        sentiment_print = str(sentiment_percentage) + "% Positive"
    return_string = ("Average Sentiment: " + sentiment_print + "<br/>" + "Tweets Omitted: " + str(NUM_TWEETS_OMITTED) 
                        + "<br/>" + "Most Positive Tweet: " + MOST_POSITIVE_TWEET + "<br/>" "Most Negative Tweet: " + MOST_NEGATIVE_TWEET 
                        + "<br/>" + "Number of Positive Tweets: " + str(NUM_POS_TWEETS) + "<br/>" + "Number of Negative Tweets: " + str(NUM_NEG_TWEETS)
                        + "<br/>" + "Number of Neutral Tweets: " + str(NUM_NEUTRAL))
    return return_string 

@app.route('/')
def my_form():
        return render_template('index.html', avg_sentiment = AVG_SENTIMENT, most_positive_tweet = MOST_POSITIVE_TWEET,
                                            most_negative_tweet = MOST_NEGATIVE_TWEET, num_pos_tweets = NUM_POS_TWEETS,
                                            num_neg_tweets = NUM_NEG_TWEETS, num_tweets_omitted = NUM_TWEETS_OMITTED)

"""
    Essentially the main method. Prompts the end user for a username or hashtag
    then runs sentiment analysis on the last at most 50 tweets from that 
    username or hashtag. Stores all important statistics for return.
"""
@app.route('/', methods=['POST'])
def my_form_post():
        setGlobals()

        # Instantiates a client
        client = language.LanguageServiceClient(credentials=credentials)

        # The text to analyze
        text = request.form['text']
        overall_sentiment = 0

        # In the case of asked for user
        if text[0] == "@":
            # Creates twitter client from user name
            user = TwitterClient(text)

            # Retrieves past 50 tweets
            tweets,count = user.get_tweets(50)
   
            # Gets overall sentiment from gathered tweets
            overall_sentiment = get_overall_sentiment(tweets, client)

            return get_return_string(overall_sentiment, count)
        # In the case of asked for hashtag
        elif text[0] == "#":
            # Retrieves past 50 tweets
            tweets, count = get_hashtag_tweets(50, text)
            
            # Gets overall sentiment from gathered tweets
            overall_sentiment = get_overall_sentiment(tweets, client)

            return get_return_string(overall_sentiment, count)
        else:
            print("Invalid input")

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)

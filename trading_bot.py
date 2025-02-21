import os
import time
import logging
import numpy as np
import pandas as pd
from binance.client import Client
import tweepy
import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pytrends.request import TrendReq
import instaloader
from threading import Lock, Thread

# ============================ CONFIGURATION ============================= #

# API Keys (Use environment variables for security)
BIRDEYE_API_KEY = '38c28e72148d42eba0ee74c0dd252fdd'  # Birdeye API Key
BINANCE_API_KEY = 'whOs56mPFA7qzPrldPvsgKSWo46X0XySxLmlftF6BvkNA45fJLxK1neq9x4uwlGh'  # Binance API Key
BINANCE_API_SECRET = 'Px1SX2FcjxGVdwnz6VrFt9amwSMPQyv0TAMXBYlyjaULTaarVWBJWSypv5f5WcLN'  # Binance Secret Key
TWITTER_API_KEY = 'Nr7tZuSV1duWdyKa6hy08Xt7B'  # Twitter API Key
TWITTER_API_SECRET = 'TElyaXspch7YiHPcR3S8OdJQGoVHmdhTTZRXb2bnrF3vdjWsyP'  # Twitter API Secret
TWITTER_ACCESS_TOKEN = '1885784749937180672-J8RTrApDMBuygRZHsaQI2Q7GiHZdaD'  # Twitter Access Token
TWITTER_ACCESS_TOKEN_SECRET = '53zt8NVFfyhamthm1JEakoQj8l9cXlwGOHxMc7zS3kHyR'  # Twitter Access Token Secret
TWITTER_BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAFHJygEAAAAA7ac65jgQg580L0erV4gZzblXM1g%3DEVQx8qkhVXqqLnR9CYYF7Js9dwnJVZfcvpvZd3F6gampuV90nA'  # Twitter Bearer Token
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')  # Reddit Client ID
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')  # Reddit Client Secret
REDDIT_USER_AGENT = 'crypto_trading_bot'  # Reddit User Agent

# Initialize APIs
binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter_api = tweepy.API(auth)
reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET, user_agent=REDDIT_USER_AGENT)
analyzer = SentimentIntensityAnalyzer()
pytrends = TrendReq(hl='en-US', tz=360)
insta_loader = instaloader.Instaloader()

# ============================= PARAMETERS ============================= #

# Trading Parameters
VOLUME_THRESHOLD = 10000
PRICE_CHANGE_THRESHOLD = 5.0
SENTIMENT_THRESHOLD = 0.2
STOP_LOSS_PERCENTAGE = 0.10  # 10% stop-loss

# Risk Management
MAX_TOTAL_INVESTMENT_PERCENTAGE = 0.80  # Max 80% of available USDT
MAX_SINGLE_TRADE_PERCENTAGE = 0.30  # Max 30% of available USDT per trade

# Celebrity Monitoring
CELEBRITY_HANDLES = ['elonmusk', 'MrBeast', 'SnoopDogg']
INSTAGRAM_ACCOUNTS = ['elonmusk', 'snoopdogg']

# Trade History & Tracking
trade_history = pd.DataFrame(columns=["symbol", "volume", "price_change", "sentiment", "confidence", "profit"])
traded_tokens = {}
trade_lock = Lock()

# Dry Run Mode
DRY_RUN = True  # Set to False for live trading

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ============================= FUNCTIONS ============================= #

# Safety Cap Functions
def get_usdt_balance():
    try:
        balance_info = binance_client.get_asset_balance(asset='USDT')
        return float(balance_info['free']) if balance_info else 0
    except Exception as e:
        logging.error(f"Error fetching USDT balance: {e}")
        return 0

def get_total_invested_usdt():
    total_invested = 0
    for symbol, data in traded_tokens.items():
        buy_price = data['buy_price']
        quantity = data.get('quantity', 0)
        total_invested += buy_price * quantity
    return total_invested

# Market & Sentiment Analysis
def get_new_tokens():
    try:
        url = f"https://public-api.birdeye.so/token/new"
        headers = {'X-API-KEY': BIRDEYE_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching new tokens: {e}")
        return {}

def analyze_sentiment(text):
    sentiment = analyzer.polarity_scores(text)
    return sentiment['compound']

def check_social_media_mentions(symbol):
    mentions = []
    try:
        for tweet in tweepy.Cursor(twitter_api.search_tweets, q=symbol, lang="en").items(10):
            mentions.append(analyze_sentiment(tweet.text))
        for submission in reddit.subreddit('CryptoCurrency').search(symbol, limit=5):
            mentions.append(analyze_sentiment(submission.title + " " + submission.selftext))
    except Exception as e:
        logging.error(f"Error checking social media mentions for {symbol}: {e}")
    return sum(mentions) / len(mentions) if mentions else 0

def check_celebrity_endorsement(symbol):
    for handle in CELEBRITY_HANDLES:
        try:
            tweets = twitter_api.user_timeline(screen_name=handle, count=5, tweet_mode='extended')
            for tweet in tweets:
                if symbol.lower() in tweet.full_text.lower():
                    sentiment = analyze_sentiment(tweet.full_text)
                    if sentiment > 0.2:
                        return True
        except Exception as e:
            logging.error(f"Error checking tweets for {handle}: {e}")
    return False

def check_google_trends(symbol):
    try:
        pytrends.build_payload([symbol], cat=0, timeframe='now 1-d', geo='', gprop='')
        data = pytrends.interest_over_time()
        if not data.empty:
            trend_score = data[symbol].iloc[-1]
            return trend_score > 50
    except Exception as e:
        logging.error(f"Error checking Google Trends for {symbol}: {e}")
    return False

# Confidence Scoring
def calculate_confidence(symbol, volume, price_change, sentiment):
    confidence = 0

    if volume >= VOLUME_THRESHOLD:
        confidence += 0.25 * min(volume / (VOLUME_THRESHOLD * 5), 1)

    if price_change >= PRICE_CHANGE_THRESHOLD:
        confidence += 0.25 * min(price_change / (PRICE_CHANGE_THRESHOLD * 5), 1)

    confidence += 0.2 * max(sentiment, 0)

    if check_celebrity_endorsement(symbol):
        confidence += 0.15

    if check_google_trends(symbol):
        confidence += 0.15

    return min(max(confidence, 0), 1)  # Ensure confidence is between 0 and 1

# Fund Allocation
def calculate_investment_amount(confidence):
    usdt_balance = get_usdt_balance()
    total_invested = get_total_invested_usdt()
    max_total_investable = usdt_balance * MAX_TOTAL_INVESTMENT_PERCENTAGE
    available_funds = max_total_investable - total_invested

    if available_funds <= 0:
        return 0

    investment_percentage = min(confidence, MAX_SINGLE_TRADE_PERCENTAGE)
    amount_to_invest = available_funds * investment_percentage
    return min(amount_to_invest, usdt_balance)

# Trading Execution
def execute_buy(symbol, confidence):
    with trade_lock:
        if symbol in traded_tokens:
            return

        amount_to_invest = calculate_investment_amount(confidence)
        if amount_to_invest <= 0:
            return

        try:
            price = float(binance_client.get_symbol_ticker(symbol=f"{symbol}USDT")['price'])
            quantity = round(amount_to_invest / price, 5)

            if quantity > 0:
                if DRY_RUN:
                    logging.info(f"Dry run: Would buy {symbol} with quantity {quantity} at price {price}")
                    return

                order = binance_client.order_market_buy(symbol=f"{symbol}USDT", quantity=quantity)
                traded_tokens[symbol] = {
                    "buy_price": float(order['fills'][0]['price']),
                    "peak_price": float(order['fills'][0]['price']),
                    "status": "holding",
                    "confidence": confidence,
                    "quantity": quantity
                }
                logging.info(f"Successfully bought {symbol} at {price} with confidence {confidence}")
        except Exception as e:
            logging.error(f"Failed to buy {symbol}: {e}")

def execute_sell(symbol, reason):
    with trade_lock:
        try:
            data = traded_tokens[symbol]
            quantity = data['quantity']

            if quantity > 0:
                if DRY_RUN:
                    logging.info(f"Dry run: Would sell {symbol} with quantity {quantity}")
                    return

                order = binance_client.order_market_sell(symbol=f"{symbol}USDT", quantity=quantity)
                sell_price = float(order['fills'][0]['price'])
                buy_price = data['buy_price']
                profit = (sell_price - buy_price) / buy_price * 100

                trade_history.loc[len(trade_history)] = [
                    symbol, data['quantity'], data['confidence'], profit
                ]
                del traded_tokens[symbol]
                logging.info(f"Successfully sold {symbol} at {sell_price} with profit {profit:.2f}% ({reason})")
        except Exception as e:
            logging.error(f"Failed to sell {symbol}: {e}")

def check_stop_loss(symbol):
    data = traded_tokens.get(symbol)
    if data:
        current_price = float(binance_client.get_symbol_ticker(symbol=f"{symbol}USDT")['price'])
        buy_price = data['buy_price']
        loss_percentage = (buy_price - current_price) / buy_price * 100
        if loss_percentage >= STOP_LOSS_PERCENTAGE:
            execute_sell(symbol, reason="Stop-loss triggered")

# Buy Decision Function
def should_buy(token_data):
    volume = token_data.get('volume', 0)
    price_change = token_data.get('price_change_24h', 0)
    symbol = token_data.get('symbol')
    sentiment = check_social_media_mentions(symbol)

    confidence = calculate_confidence(symbol, volume, price_change, sentiment)
    return confidence if confidence >= 0.5 else 0

# ============================= MAIN LOOP ============================= #

def main():
    logging.info("Starting trading bot...")
    while True:
        try:
            new_tokens = get_new_tokens()
            if new_tokens:
                for token in new_tokens.get('tokens', []):
                    symbol = token.get('symbol')
                    if symbol not in traded_tokens:
                        confidence = should_buy(token)
                        if confidence:
                            execute_buy(symbol, confidence)

            # Check stop-loss for all traded tokens
            for symbol in list(traded_tokens.keys()):
                check_stop_loss(symbol)

            time.sleep(60)  # Runs every minute
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            time.sleep(60)

if __name__ == '__main__':
    trading_thread = Thread(target=main)
    trading_thread.start()

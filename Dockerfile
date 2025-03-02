# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Set environment variables
ENV BIRDEYE_API_KEY=${BIRDEYE_API_KEY}
ENV BINANCE_API_KEY=${BINANCE_API_KEY}
ENV BINANCE_API_SECRET=${BINANCE_API_SECRET}
ENV TWITTER_API_KEY=${TWITTER_API_KEY}
ENV TWITTER_API_SECRET=${TWITTER_API_SECRET}
ENV TWITTER_ACCESS_TOKEN=${TWITTER_ACCESS_TOKEN}
ENV TWITTER_ACCESS_TOKEN_SECRET=${TWITTER_ACCESS_TOKEN_SECRET}
ENV TWITTER_BEARER_TOKEN=${TWITTER_BEARER_TOKEN}
ENV REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
ENV REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}

# Run the bot
CMD ["python", "trading_bot.py"]

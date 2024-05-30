from locust import HttpUser, task, between
import re
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class YouTubeCommentAnalyzer(HttpUser):
    wait_time = between(1, 3)

    @task
    def analyze_video_comments(self):
        # URL of the YouTube video to analyze comments
        video_url = "https://www.youtube.com/watch?v=r0oUWeNntM0"
        
        # Fetching video ID from the URL
        video_id = video_url[-11:]

        # Fetching video details to get uploader's channel ID
        video_response = self.client.get(
            f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key=AIzaSyAT4h5pQRMXWp8X1bV8WN7h3w7gY_CG6lE"
        ).json()
        uploader_channel_id = video_response['items'][0]['snippet']['channelId']

        # Fetching comments
        comments = []
        next_page_token = None
        while len(comments) < 600:
            response = self.client.get(
                f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults=100&pageToken={next_page_token}&key=AIzaSyAT4h5pQRMXWp8X1bV8WN7h3w7gY_CG6lE"
            ).json()
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                if comment['authorChannelId']['value'] != uploader_channel_id:
                    comments.append(comment['textDisplay'])
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        # Filtering relevant comments
        relevant_comments = []
        for comment_text in comments:
            comment_text = comment_text.lower().strip()
            emojis = emoji.emoji_count(comment_text)
            text_characters = len(re.sub(r'\s', '', comment_text))
            if (any(char.isalnum() for char in comment_text)) and not re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', comment_text):
                if emojis == 0 or (text_characters / (text_characters + emojis)) > 0.65:
                    relevant_comments.append(comment_text)

        # Storing relevant comments in a file
        with open("ytcomments.txt", 'w', encoding='utf-8') as f:
            for comment in relevant_comments:
                f.write(str(comment) + "\n")

        # Analyzing sentiment of comments
        analyzer = SentimentIntensityAnalyzer()
        positive_comments = []
        negative_comments = []
        neutral_comments = []
        with open("ytcomments.txt", 'r', encoding='utf-8') as f:
            comments = f.readlines()
        for comment in comments:
            sentiment_score = analyzer.polarity_scores(comment)['compound']
            if sentiment_score > 0.05:
                positive_comments.append(comment)
            elif sentiment_score < -0.05:
                negative_comments.append(comment)
            else:
                neutral_comments.append(comment)

        # Printing analysis results
        avg_polarity = sum([analyzer.polarity_scores(comment)['compound'] for comment in comments]) / len(comments)
        print("Average Polarity:", avg_polarity)
        if avg_polarity > 0.05:
            print("The Video has got a Positive response")
        elif avg_polarity < -0.05:
            print("The Video has got a Negative response")
        else:
            print("The Video has got a Neutral response")
        print("The comment with most positive sentiment:", max(positive_comments, key=lambda x: analyzer.polarity_scores(x)['compound']))
        print("The comment with most negative sentiment:", min(negative_comments, key=lambda x: analyzer.polarity_scores(x)['compound']))

    def on_start(self):
        pass

    def on_stop(self):
        pass

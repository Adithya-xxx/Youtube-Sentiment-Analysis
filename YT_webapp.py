from flask import Flask, render_template, request
from googleapiclient.discovery import build
import re
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt

app = Flask(__name__)

# Function to fetch comments from YouTube
def fetching_comments(request,comments):
    API_KEY = 'AIzaSyAT4h5pQRMXWp8X1bV8WN7h3w7gY_CG6lE' # Put in your API Key
    youtube = build('youtube', 'v3', developerKey=API_KEY)

    video_id = request.form['video_id'][-11:]
    uploader_channel_id = ''
    
    video_response = youtube.videos().list(part='snippet',id=video_id).execute()
    video_snippet = video_response['items'][0]['snippet']
    uploader_channel_id = video_snippet['channelId']

    nextPageToken = None
    while len(comments) < 600:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,
            pageToken=nextPageToken
        )
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            if comment['authorChannelId']['value'] != uploader_channel_id:
                comments.append(comment['textDisplay'])
        nextPageToken = response.get('nextPageToken')
        if not nextPageToken:
            break

    return comments

# Function to filter comments
def filtering_comments(comments, relevant_comments):
    hyperlink_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    threshold_ratio = 0.70
    for comment_text in comments:
        comment_text = comment_text.lower().strip()
        emojis = emoji.emoji_count(comment_text)
        text_characters = len(re.sub(r'\s', '', comment_text))
        if (any(char.isalnum() for char in comment_text)) and not hyperlink_pattern.search(comment_text):
            if emojis == 0 or (text_characters / (text_characters + emojis)) > threshold_ratio:
                relevant_comments.append(comment_text)

# Function to perform sentiment analysis
def sentiment_scores(comment, polarity):
    sentiment_object = SentimentIntensityAnalyzer()
    sentiment_dict = sentiment_object.polarity_scores(comment)
    polarity.append(sentiment_dict['compound'])
    return polarity

# Function to calculate polarity
def calculate_polarity(very_positive, very_negative, positive_comments, negative_comments, neutral_comments, polarity):
    with open("ytcomments.txt", 'r', encoding='utf-8') as f:
        comments = f.readlines()
    
    for items in comments:
        polarity = sentiment_scores(items, polarity)
        if polarity[-1] > 0.85:
            very_positive.append(items)
        elif polarity[-1] > 0:
            positive_comments.append(items)
        elif polarity[-1] < -0.70:
            very_negative.append(items)
        elif polarity[-1] < -0.03:
            negative_comments.append(items)
        else:
            neutral_comments.append(items)

    avg_polarity = sum(polarity)/len(polarity)
    if avg_polarity > 0.04:
        result = "The Video has got a Positive response"
    elif avg_polarity < -0.03:
        result = "The Video has got a Negative response"
    else:
        result = "The Video has got a Neutral response"
    
    most_positive_comment = comments[polarity.index(max(polarity))]
    most_negative_comment = comments[polarity.index(min(polarity))]
    
    return avg_polarity, result, most_positive_comment, most_negative_comment

# Function to generate bar graph
def bar_graph(very_positive, very_negative, positive_comments, negative_comments, neutral_comments):
    very_positive_count = len(very_positive)
    positive_count = len(positive_comments)
    negative_count = len(negative_comments)
    very_negative_count = len(very_negative)
    neutral_count = len(neutral_comments)
    
    labels = ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative']
    comment_counts = [very_positive_count, positive_count, neutral_count, negative_count, very_negative_count]
    
    plt.bar(labels, comment_counts, color=['blue', 'green', 'grey', 'orange', 'red'])
    plt.xlabel('Sentiment')
    plt.ylabel('Comment Count')
    plt.title('Sentiment Analysis of Comments')
    
    # Save the plot to a file
    plt.savefig('static/bar_chart.png')
    plt.close()

# Function to generate pie chart
def pie_chart(very_positive, very_negative, positive_comments, negative_comments, neutral_comments):
    very_positive_count = len(very_positive)
    positive_count = len(positive_comments)
    negative_count = len(negative_comments)
    very_negative_count = len(very_negative)
    neutral_count = len(neutral_comments)

    labels = ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative']
    comment_counts = [very_positive_count, positive_count, neutral_count, negative_count, very_negative_count]
    
    plt.pie(comment_counts, labels=labels, autopct='%1.1f%%')
    plt.title('Sentiment Analysis of Comments')
    
    # Save the plot to a file
    plt.savefig('static/pie_chart.png')
    plt.close()

# Route for home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle form submission
@app.route('/analyze', methods=['POST'])
def analyze():
    comments = []
    relevant_comments = []
    fetching_comments(request,comments)
    filtering_comments(comments, relevant_comments)

    with open("ytcomments.txt", 'w', encoding='utf-8') as f:
        for comment in relevant_comments:
            f.write(str(comment) + "\n\n")

    polarity = []
    very_positive = []
    positive_comments = []
    negative_comments = []
    neutral_comments = []
    very_negative =[]
    avg_polarity, result, most_positive_comment, most_negative_comment = calculate_polarity(
        very_positive, very_negative, positive_comments, negative_comments, neutral_comments, polarity
    )

    bar_graph(very_positive, very_negative, positive_comments, negative_comments, neutral_comments)
    pie_chart(very_positive, very_negative, positive_comments, negative_comments, neutral_comments)

    return render_template('results.html', avg_polarity=avg_polarity, result=result, 
                           most_positive_comment=most_positive_comment, most_negative_comment=most_negative_comment)

if __name__ == '__main__':
    app.run(debug=True)

# For Fetching Comments 
from googleapiclient.discovery import build 
# For filtering comments 
import re 
# For filtering comments with just emojis 
import emoji
# Analyze the sentiments of the comment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# For visualization 
import matplotlib.pyplot as plt


def FetchingComments(comments):
    API_KEY = 'AIzaSyAT4h5pQRMXWp8X1bV8WN7h3w7gY_CG6lE'# Put in your API Key

    youtube = build('youtube', 'v3', developerKey=API_KEY) # initializing Youtube API

    # Taking input from the user and slicing for video id
    video_id = input('Enter Youtube Video URL: ')[-11:]
    print("\nVIDEO DETAILS")
    print("video id: " + video_id)

    # Getting the channelId of the video uploader
    video_response = youtube.videos().list(part='snippet',id=video_id).execute()

    # Splitting the response for channelID
    video_snippet = video_response['items'][0]['snippet']
    uploader_channel_id = video_snippet['channelId']
    print("channel id: \n" + uploader_channel_id)

    # Fetch comments
    print("Fetching Comments...")
    nextPageToken = None
    while len(comments) < 600:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100, # You can fetch up to 100 comments per request
            pageToken=nextPageToken
        )
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            # Check if the comment is not from the video uploader
            if comment['authorChannelId']['value'] != uploader_channel_id:
                comments.append(comment['textDisplay'])
        nextPageToken = response.get('nextPageToken')

        if not nextPageToken:
            break

    return comments



def FilteringComments(comments,relevant_comments):
    hyperlink_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    threshold_ratio = 0.70
    # Inside your loop that processes comments
    for comment_text in comments:
        comment_text = comment_text.lower().strip()
        emojis = emoji.emoji_count(comment_text)
        # Count text characters (excluding spaces)
        text_characters = len(re.sub(r'\s', '', comment_text))
        if (any(char.isalnum() for char in comment_text)) and not hyperlink_pattern.search(comment_text):
            if emojis == 0 or (text_characters / (text_characters + emojis)) > threshold_ratio:
                relevant_comments.append(comment_text)
    # Print the relevant comments
    relevant_comments[:5]



def sentiment_scores(comment, polarity):
    # Creating a SentimentIntensityAnalyzer object.
    sentiment_object = SentimentIntensityAnalyzer()
 
    sentiment_dict = sentiment_object.polarity_scores(comment)
    polarity.append(sentiment_dict['compound'])
 
    return polarity

def Calculate_Polarity(very_positive,very_negative,positive_comments,negative_comments,neutral_comments,polarity):
    f = open("ytcomments.txt", 'r', encoding='`utf-8')
    comments = f.readlines()
    f.close()
    print("Analysing Comments...")
    for index, items in enumerate(comments):
        polarity = sentiment_scores(items, polarity)
        if polarity[-1] > 0.85:
            very_positive.append(items)
        elif polarity[-1] > 0.04:
            positive_comments.append(items)
        elif polarity[-1] < -0.70:
            very_negative.append(items)
        elif polarity[-1] < -0.03:
            negative_comments.append(items)
        else:
            neutral_comments.append(items)

    avg_polarity = sum(polarity)/len(polarity)
    print("Average Polarity:", avg_polarity)
    if avg_polarity > 0.04:
        print("The Video has got a Positive response")
    elif avg_polarity < -0.03:
        print("The Video has got a Negative response")
    else:
        print("The Video has got a Neutral response")
    
    print("The comment with most positive sentiment:", comments[polarity.index(max(polarity))], "with score", max(polarity), "and length", len(comments[polarity.index(max(polarity))]))
    print("The comment with most negative sentiment:", comments[polarity.index(min(polarity))], "with score", min(polarity), "and length", len(comments[polarity.index(min(polarity))]))




def BarGraph(very_positive,very_negative,positive_comments,negative_comments,neutral_comments):
    very_positive_count = len(very_positive)
    positive_count = len(positive_comments)
    negative_count = len(negative_comments)
    very_negative_count = len(very_negative)
    neutral_count = len(neutral_comments)
    
    # labels and data for Bar chart
    labels = ['Very Positive','Positive', 'Neutral', 'Negative','Very Negative']
    comment_counts = [very_positive_count,positive_count, neutral_count, negative_count,very_negative_count]
    
    # Creating bar chart
    plt.bar(labels, comment_counts, color=['blue','green', 'grey', 'orange','red'])
    
    # Adding labels and title to the plot
    plt.xlabel('Sentiment')
    plt.ylabel('Comment Count')
    plt.title('Sentiment Analysis of Comments')
    
    # Displaying the chart
    plt.show()

def PieChart(very_positive,very_negative,positive_comments,negative_comments,neutral_comments):
    very_positive_count = len(very_positive)
    positive_count = len(positive_comments)
    negative_count = len(negative_comments)
    neutral_count = len(neutral_comments)
    very_negative_count = len(very_negative)

    labels = ['Very Positive','Positive','Neutral','Negative','Very Negative']
    comment_counts = [very_positive_count,positive_count, neutral_count,negative_count,very_negative_count]
    
    plt.figure(figsize=(10, 6)) # setting size
    
    # plotting pie chart
    plt.pie(comment_counts, labels=labels)
    
    # Displaying Pie Chart
    plt.show()



comments = []
FetchingComments(comments)
relevant_comments = []
FilteringComments(comments,relevant_comments)

f = open("ytcomments.txt", 'w', encoding='utf-8')
for idx, comment in enumerate(relevant_comments):
    f.write(str(comment)+"\n\n")
f.close()
print("Comments stored successfully!")

polarity = []
very_positive = []
positive_comments = []
negative_comments = []
neutral_comments = []
very_negative =[]
Calculate_Polarity(very_positive,very_negative,positive_comments,negative_comments,neutral_comments,polarity)

check1 = input("\nDO YOU WANT TO GENERATE BAR GRAPH ? (Y/N)")
if(check1=="Y"):
    BarGraph(very_positive,very_negative,positive_comments,negative_comments,neutral_comments)

check2 = input("\nDO YOU WANT TO GENERATE PIE CHART ? (Y/N)")
if(check2=="Y"):
    PieChart(very_positive,very_negative,positive_comments,negative_comments,neutral_comments)




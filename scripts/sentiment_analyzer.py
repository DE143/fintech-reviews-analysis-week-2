import pandas as pd
import numpy as np
from transformers import pipeline
from textblob import TextBlob
import spacy

class SentimentAnalyzer:
    def __init__(self):
        # Initialize sentiment analysis pipeline
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            truncation=True
        )
        self.nlp = spacy.load("en_core_web_sm")
    
    def analyze_sentiment_distilbert(self, text):
        """Analyze sentiment using DistilBERT"""
        try:
            result = self.sentiment_pipeline(text[:512])[0]  # Truncate for model limits
            return result['label'], result['score']
        except:
            return 'NEUTRAL', 0.5
    
    def analyze_sentiment_textblob(self, text):
        """Analyze sentiment using TextBlob as backup"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            return 'POSITIVE', polarity
        elif polarity < -0.1:
            return 'NEGATIVE', abs(polarity)
        else:
            return 'NEUTRAL', 0.5
    
    def analyze_reviews(self, df):
        """Analyze sentiment for all reviews"""
        print("Starting sentiment analysis...")
        
        sentiments = []
        scores = []
        
        for text in df['cleaned_text']:
            # Use DistilBERT as primary
            sentiment, score = self.analyze_sentiment_distilbert(text)
            sentiments.append(sentiment)
            scores.append(score)
        
        df['sentiment_label'] = sentiments
        df['sentiment_score'] = scores
        
        # Summary statistics
        sentiment_counts = df['sentiment_label'].value_counts()
        print("Sentiment Distribution:")
        print(sentiment_counts)
        
        return df

if __name__ == "__main__":
    # Load cleaned data
    df = pd.read_csv('data/cleaned_reviews.csv')
    
    # Initialize analyzer
    analyzer = SentimentAnalyzer()
    
    # Analyze sentiment
    analyzed_df = analyzer.analyze_reviews(df)
    
    # Save results
    analyzed_df.to_csv('data/analyzed_reviews.csv', index=False)
    print("Sentiment analysis completed and saved!")
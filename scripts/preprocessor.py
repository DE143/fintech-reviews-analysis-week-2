import pandas as pd
import numpy as np
from datetime import datetime
import re

def preprocess_reviews(df):
    """
    Clean and preprocess the scraped reviews
    """
    print("Starting preprocessing...")
    
    # Remove duplicates
    initial_count = len(df)
    df = df.drop_duplicates(subset=['review_id'], keep='first')
    print(f"Removed {initial_count - len(df)} duplicates")
    
    # Handle missing data
    missing_before = df.isnull().sum()
    df = df.dropna(subset=['review_text', 'rating'])
    print(f"Removed rows with missing text/rating: {missing_before['review_text']}")
    
    # Clean text
    df['cleaned_text'] = df['review_text'].apply(clean_text)
    
    # Ensure date format
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    # Ensure rating is integer
    df['rating'] = df['rating'].astype(int)
    
    print(f"Final cleaned reviews: {len(df)}")
    return df

def clean_text(text):
    """
    Clean review text
    """
    if pd.isna(text):
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?]', '', text)
    
    # Convert to lowercase
    text = text.lower().strip()
    
    return text

if __name__ == "__main__":
    # Load raw data
    df = pd.read_csv('data/raw_reviews.csv')
    
    # Preprocess
    cleaned_df = preprocess_reviews(df)
    
    # Save cleaned data
    cleaned_df.to_csv('data/cleaned_reviews.csv', index=False)
    print("Cleaned data saved to data/cleaned_reviews.csv")
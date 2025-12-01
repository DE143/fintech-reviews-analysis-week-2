import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import spacy
from collections import Counter
import re

class ThematicAnalyzer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.themes = {
            'UI/UX': ['interface', 'design', 'layout', 'screen', 'button', 'menu', 'navigation'],
            'Performance': ['slow', 'fast', 'speed', 'loading', 'lag', 'crash', 'freeze'],
            'Functionality': ['transfer', 'payment', 'login', 'password', 'account', 'balance'],
            'Security': ['secure', 'safe', 'password', 'pin', 'authentication', 'fingerprint'],
            'Support': ['support', 'help', 'service', 'response', 'contact', 'complaint']
        }
    
    def extract_keywords(self, text):
        """Extract meaningful keywords from text"""
        doc = self.nlp(text)
        keywords = []
        
        for token in doc:
            # Keep nouns, adjectives, verbs that are not stop words
            if (not token.is_stop and not token.is_punct and 
                token.pos_ in ['NOUN', 'ADJ', 'VERB'] and len(token.lemma_) > 2):
                keywords.append(token.lemma_.lower())
        
        return keywords
    
    def assign_theme(self, text):
        """Assign theme based on keyword matching"""
        text_lower = text.lower()
        theme_scores = {}
        
        for theme, keywords in self.themes.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            theme_scores[theme] = score
        
        if max(theme_scores.values()) > 0:
            return max(theme_scores, key=theme_scores.get)
        else:
            return 'Other'
    
    def analyze_themes(self, df):
        """Perform thematic analysis on reviews"""
        print("Starting thematic analysis...")
        
        # Extract keywords for all reviews
        df['keywords'] = df['cleaned_text'].apply(self.extract_keywords)
        
        # Assign themes
        df['theme'] = df['cleaned_text'].apply(self.assign_theme)
        
        # Bank-specific analysis
        for bank in df['bank'].unique():
            bank_df = df[df['bank'] == bank]
            print(f"\n--- {bank} Theme Distribution ---")
            print(bank_df['theme'].value_counts())
            
            # Top keywords for this bank
            all_keywords = [kw for sublist in bank_df['keywords'] for kw in sublist]
            top_keywords = Counter(all_keywords).most_common(10)
            print(f"Top keywords: {top_keywords}")
        
        return df

if __name__ == "__main__":
    # Load analyzed data
    df = pd.read_csv('data/analyzed_reviews.csv')
    
    # Initialize thematic analyzer
    thematic_analyzer = ThematicAnalyzer()
    
    # Analyze themes
    final_df = thematic_analyzer.analyze_themes(df)
    
    # Save final results
    final_df.to_csv('data/final_analyzed_reviews.csv', index=False)
    print("Thematic analysis completed!")
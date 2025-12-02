"""
Main orchestrator script for the Fintech Reviews Analysis Project
"""
import sys
import os
import pandas as pd

# Add scripts directory to path
sys.path.append('scripts')

from scraper import scrape_play_store_reviews
from preprocessor import preprocess_reviews
from sentiment_analyzer import SentimentAnalyzer
from thematic_analyzer import ThematicAnalyzer
from database_handler import DatabaseHandler
from visualizer import ReviewVisualizer

def ensure_directories():
    """Ensure all required directories exist"""
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    print("✓ Directories verified: data/, reports/")

def save_dataframe(df, filename, description):
    """Save DataFrame with confirmation message"""
    df.to_csv(f'data/{filename}', index=False)
    print(f"✓ {description} saved to data/{filename}")

def main():
    print("=== Fintech Reviews Analysis Pipeline ===")
    
    # Ensure directories exist
    ensure_directories()
    
    try:
        # Step 1: Data Collection
        print("\n1. Scraping reviews from Google Play Store...")
        reviews_df = scrape_play_store_reviews()
        save_dataframe(reviews_df, 'raw_reviews.csv', 'Raw reviews')
        
        # Step 2: Data Preprocessing
        print("\n2. Preprocessing data...")
        cleaned_df = preprocess_reviews(reviews_df)
        save_dataframe(cleaned_df, 'cleaned_reviews.csv', 'Cleaned reviews')
        
        # Step 3: Sentiment Analysis
        print("\n3. Performing sentiment analysis...")
        sentiment_analyzer = SentimentAnalyzer()
        analyzed_df = sentiment_analyzer.analyze_reviews(cleaned_df)
        save_dataframe(analyzed_df, 'analyzed_reviews.csv', 'Sentiment analysis results')
        
        # Step 4: Thematic Analysis
        print("\n4. Performing thematic analysis...")
        thematic_analyzer = ThematicAnalyzer()
        final_df = thematic_analyzer.analyze_themes(analyzed_df)
        save_dataframe(final_df, 'final_analyzed_reviews.csv', 'Final analyzed data')
        
        # Step 5: Database Storage
        print("\n5. Storing data in PostgreSQL...")
        db_handler = DatabaseHandler()
        db_handler.create_tables()
        db_handler.insert_data(final_df)
        db_handler.run_queries()
        
        # Step 6: Visualization
        print("\n6. Generating visualizations...")
        visualizer = ReviewVisualizer(final_df)
        visualizer.generate_all_visualizations()
        
        # Display summary
        display_analysis_summary(final_df)
        
        print("\n=== Pipeline completed successfully! ===")
        print("✓ All data files saved to data/ folder")
        print("✓ Visualizations saved to reports/ folder")
        print("✓ Data stored in PostgreSQL database")
        
    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
        import traceback
        traceback.print_exc()

def display_analysis_summary(df):
    """Display a comprehensive summary of the analysis"""
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY REPORT")
    print("="*60)
    
    # Basic statistics
    print(f"\n📊 BASIC STATISTICS:")
    print(f"Total Reviews Processed: {len(df):,}")
    print(f"Banks Analyzed: {df['bank'].nunique()}")
    
    # Rating analysis
    print(f"\n⭐ RATING ANALYSIS:")
    rating_summary = df.groupby('bank').agg({
        'rating': ['mean', 'count'],
        'sentiment_score': 'mean'
    }).round(2)
    print(rating_summary)
    
    # Sentiment analysis
    print(f"\n😊 SENTIMENT ANALYSIS:")
    sentiment_summary = df.groupby(['bank', 'sentiment_label']).size().unstack(fill_value=0)
    print(sentiment_summary)
    
    # Theme analysis
    print(f"\n🎯 THEME DISTRIBUTION:")
    for bank in df['bank'].unique():
        bank_data = df[df['bank'] == bank]
        print(f"\n{bank}:")
        theme_counts = bank_data['theme'].value_counts()
        for theme, count in theme_counts.items():
            percentage = (count / len(bank_data)) * 100
            print(f"  {theme}: {count} reviews ({percentage:.1f}%)")
    
    # Key insights
    print(f"\n🔍 KEY INSIGHTS:")
    for bank in df['bank'].unique():
        bank_data = df[df['bank'] == bank]
        avg_rating = bank_data['rating'].mean()
        pos_sentiment = len(bank_data[bank_data['sentiment_label'] == 'POSITIVE'])
        pos_percentage = (pos_sentiment / len(bank_data)) * 100
        
        print(f"\n{bank}:")
        print(f"  • Average Rating: {avg_rating:.2f}/5.0")
        print(f"  • Positive Sentiment: {pos_percentage:.1f}%")
        
        # Top theme
        top_theme = bank_data['theme'].value_counts().index[0]
        print(f"  • Most Common Theme: {top_theme}")

if __name__ == "__main__":
    main()
"""
Main orchestrator script for the Fintech Reviews Analysis Project
"""
import sys
import os
import pandas as pd
import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime

# Add scripts directory to path
sys.path.append('scripts')

# Import with try-catch to provide better error messages
try:
    from scraper import scrape_play_store_reviews
    from preprocessor import preprocess_reviews
    from sentiment_analyzer import SentimentAnalyzer
    from thematic_analyzer import ThematicAnalyzer
    from database_handler import DatabaseHandler
    from visualizer import ReviewVisualizer
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all required modules are in the 'scripts' directory:")
    print("  - scraper.py")
    print("  - preprocessor.py")
    print("  - sentiment_analyzer.py")
    print("  - thematic_analyzer.py")
    print("  - database_handler.py")
    print("  - visualizer.py")
    sys.exit(1)

# Configure logging
def setup_logging(log_file: str = 'logs/pipeline.log'):
    """Configure logging for the pipeline"""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def ensure_directories():
    """Ensure all required directories exist"""
    try:
        directories = ['data', 'reports', 'logs', 'backups']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory created/verified: {directory}/")
        print("✓ All directories verified")
    except OSError as e:
        logger.error(f"Failed to create directories: {e}")
        raise

def save_dataframe(df: pd.DataFrame, filename: str, description: str) -> bool:
    """Save DataFrame with confirmation message and backup"""
    try:
        # Create backup if file exists
        filepath = f'data/{filename}'
        if os.path.exists(filepath):
            backup_path = f'backups/{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            os.makedirs('backups', exist_ok=True)
            df.to_csv(backup_path, index=False)
            logger.info(f"Backup created: {backup_path}")
        
        # Save new file
        df.to_csv(filepath, index=False)
        logger.info(f"DataFrame saved: {filepath} ({description})")
        print(f"✓ {description} saved to data/{filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        print(f"❌ Failed to save {filename}: {e}")
        return False

def validate_dataframe(df: pd.DataFrame, step_name: str) -> bool:
    """Validate DataFrame structure and content"""
    if df is None:
        logger.error(f"{step_name}: DataFrame is None")
        return False
    
    if df.empty:
        logger.warning(f"{step_name}: DataFrame is empty")
        return True  # Return True to allow empty data flow if expected
    
    required_columns = ['review_text', 'rating', 'bank']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"{step_name}: Missing required columns: {missing_columns}")
        return False
    
    # Check for null values in critical columns
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        logger.warning(f"{step_name}: Found null values - {null_counts.to_dict()}")
    
    logger.info(f"{step_name}: DataFrame validated - {len(df)} rows, {len(df.columns)} columns")
    return True

def display_step_progress(step_num: int, step_name: str, status: str = "start"):
    """Display and log step progress"""
    if status == "start":
        message = f"\n{step_num}. {step_name}..."
        print(message)
        logger.info(message.strip())
    elif status == "success":
        message = f"  ✓ {step_name} completed successfully"
        print(message)
        logger.info(message.strip())
    elif status == "error":
        message = f"  ✗ {step_name} failed"
        print(message)
        logger.error(message.strip())
    elif status == "warning":
        message = f"  ⚠ {step_name} completed with warnings"
        print(message)
        logger.warning(message.strip())

def main():
    """Main pipeline execution function"""
    print("=" * 60)
    print("FINETECH REVIEWS ANALYSIS PIPELINE")
    print("=" * 60)
    
    # Initialize variables
    pipeline_data = {}
    success_steps = []
    failed_steps = []
    
    try:
        # Step 0: Setup
        display_step_progress(0, "Initializing pipeline", "start")
        ensure_directories()
        display_step_progress(0, "Initializing pipeline", "success")
        success_steps.append("Initialization")
        
        # Step 1: Data Collection
        display_step_progress(1, "Scraping reviews from Google Play Store", "start")
        try:
            reviews_df = scrape_play_store_reviews()
            if validate_dataframe(reviews_df, "Scraping"):
                if save_dataframe(reviews_df, 'raw_reviews.csv', 'Raw reviews'):
                    pipeline_data['raw'] = reviews_df
                    display_step_progress(1, "Scraping reviews from Google Play Store", "success")
                    success_steps.append("Data Collection")
                else:
                    display_step_progress(1, "Scraping reviews from Google Play Store", "error")
                    failed_steps.append("Data Collection - Save failed")
            else:
                display_step_progress(1, "Scraping reviews from Google Play Store", "error")
                failed_steps.append("Data Collection - Validation failed")
        except Exception as e:
            logger.error(f"Scraping failed: {e}\n{traceback.format_exc()}")
            display_step_progress(1, "Scraping reviews from Google Play Store", "error")
            failed_steps.append(f"Data Collection - {str(e)[:50]}...")
            # If scraping fails, try to load existing data
            try:
                if os.path.exists('data/raw_reviews.csv'):
                    logger.info("Attempting to load existing raw data...")
                    reviews_df = pd.read_csv('data/raw_reviews.csv')
                    pipeline_data['raw'] = reviews_df
                    display_step_progress(1, "Loaded existing raw data", "warning")
                    success_steps.append("Data Collection (from file)")
            except Exception as load_error:
                logger.error(f"Failed to load existing data: {load_error}")
        
        # Step 2: Data Preprocessing (only if we have data)
        if 'raw' in pipeline_data and not pipeline_data['raw'].empty:
            display_step_progress(2, "Preprocessing data", "start")
            try:
                cleaned_df = preprocess_reviews(pipeline_data['raw'])
                if validate_dataframe(cleaned_df, "Preprocessing"):
                    if save_dataframe(cleaned_df, 'cleaned_reviews.csv', 'Cleaned reviews'):
                        pipeline_data['cleaned'] = cleaned_df
                        display_step_progress(2, "Preprocessing data", "success")
                        success_steps.append("Data Preprocessing")
                    else:
                        display_step_progress(2, "Preprocessing data", "error")
                        failed_steps.append("Data Preprocessing - Save failed")
                else:
                    display_step_progress(2, "Preprocessing data", "error")
                    failed_steps.append("Data Preprocessing - Validation failed")
            except Exception as e:
                logger.error(f"Preprocessing failed: {e}\n{traceback.format_exc()}")
                display_step_progress(2, "Preprocessing data", "error")
                failed_steps.append(f"Data Preprocessing - {str(e)[:50]}...")
        else:
            logger.warning("Skipping preprocessing: No raw data available")
            display_step_progress(2, "Preprocessing data (skipped)", "warning")
        
        # Step 3: Sentiment Analysis (only if we have cleaned data)
        if 'cleaned' in pipeline_data and not pipeline_data['cleaned'].empty:
            display_step_progress(3, "Performing sentiment analysis", "start")
            try:
                sentiment_analyzer = SentimentAnalyzer()
                analyzed_df = sentiment_analyzer.analyze_reviews(pipeline_data['cleaned'])
                if validate_dataframe(analyzed_df, "Sentiment Analysis"):
                    if save_dataframe(analyzed_df, 'analyzed_reviews.csv', 'Sentiment analysis results'):
                        pipeline_data['analyzed'] = analyzed_df
                        display_step_progress(3, "Performing sentiment analysis", "success")
                        success_steps.append("Sentiment Analysis")
                    else:
                        display_step_progress(3, "Performing sentiment analysis", "error")
                        failed_steps.append("Sentiment Analysis - Save failed")
                else:
                    display_step_progress(3, "Performing sentiment analysis", "error")
                    failed_steps.append("Sentiment Analysis - Validation failed")
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}\n{traceback.format_exc()}")
                display_step_progress(3, "Performing sentiment analysis", "error")
                failed_steps.append(f"Sentiment Analysis - {str(e)[:50]}...")
        else:
            logger.warning("Skipping sentiment analysis: No cleaned data available")
            display_step_progress(3, "Sentiment analysis (skipped)", "warning")
        
        # Step 4: Thematic Analysis (only if we have analyzed data)
        if 'analyzed' in pipeline_data and not pipeline_data['analyzed'].empty:
            display_step_progress(4, "Performing thematic analysis", "start")
            try:
                thematic_analyzer = ThematicAnalyzer()
                final_df = thematic_analyzer.analyze_themes(pipeline_data['analyzed'])
                if validate_dataframe(final_df, "Thematic Analysis"):
                    if save_dataframe(final_df, 'final_analyzed_reviews.csv', 'Final analyzed data'):
                        pipeline_data['final'] = final_df
                        display_step_progress(4, "Performing thematic analysis", "success")
                        success_steps.append("Thematic Analysis")
                    else:
                        display_step_progress(4, "Performing thematic analysis", "error")
                        failed_steps.append("Thematic Analysis - Save failed")
                else:
                    display_step_progress(4, "Performing thematic analysis", "error")
                    failed_steps.append("Thematic Analysis - Validation failed")
            except Exception as e:
                logger.error(f"Thematic analysis failed: {e}\n{traceback.format_exc()}")
                display_step_progress(4, "Performing thematic analysis", "error")
                failed_steps.append(f"Thematic Analysis - {str(e)[:50]}...")
        else:
            logger.warning("Skipping thematic analysis: No analyzed data available")
            display_step_progress(4, "Thematic analysis (skipped)", "warning")
        
        # Step 5: Database Storage (only if we have final data)
        if 'final' in pipeline_data and not pipeline_data['final'].empty:
            display_step_progress(5, "Storing data in PostgreSQL", "start")
            try:
                db_handler = DatabaseHandler()
                db_handler.create_tables()
                db_handler.insert_data(pipeline_data['final'])
                db_handler.run_queries()
                display_step_progress(5, "Storing data in PostgreSQL", "success")
                success_steps.append("Database Storage")
            except Exception as e:
                logger.error(f"Database operations failed: {e}\n{traceback.format_exc()}")
                display_step_progress(5, "Storing data in PostgreSQL", "error")
                failed_steps.append(f"Database Storage - {str(e)[:50]}...")
        else:
            logger.warning("Skipping database storage: No final data available")
            display_step_progress(5, "Database storage (skipped)", "warning")
        
        # Step 6: Visualization (only if we have final data)
        if 'final' in pipeline_data and not pipeline_data['final'].empty:
            display_step_progress(6, "Generating visualizations", "start")
            try:
                visualizer = ReviewVisualizer(pipeline_data['final'])
                visualizer.generate_all_visualizations()
                display_step_progress(6, "Generating visualizations", "success")
                success_steps.append("Visualization")
            except Exception as e:
                logger.error(f"Visualization failed: {e}\n{traceback.format_exc()}")
                display_step_progress(6, "Generating visualizations", "error")
                failed_steps.append(f"Visualization - {str(e)[:50]}...")
        else:
            logger.warning("Skipping visualization: No final data available")
            display_step_progress(6, "Visualization (skipped)", "warning")
        
        # Display summary if we have final data
        if 'final' in pipeline_data and not pipeline_data['final'].empty:
            display_analysis_summary(pipeline_data['final'])
        
        # Pipeline completion report
        print("\n" + "=" * 60)
        print("PIPELINE EXECUTION REPORT")
        print("=" * 60)
        print(f"\n✅ SUCCESSFUL STEPS ({len(success_steps)}):")
        for step in success_steps:
            print(f"  • {step}")
        
        if failed_steps:
            print(f"\n❌ FAILED STEPS ({len(failed_steps)}):")
            for step in failed_steps:
                print(f"  • {step}")
        
        print(f"\n📊 FINAL STATUS:")
        if failed_steps:
            print(f"  Pipeline completed with {len(failed_steps)} error(s)")
            print(f"  Check logs/pipeline.log for detailed error information")
        else:
            print("  ✓ All steps completed successfully!")
            print("  ✓ Data files saved to data/ folder")
            print("  ✓ Visualizations saved to reports/ folder")
            print("  ✓ Data stored in PostgreSQL database")
        
    except KeyboardInterrupt:
        logger.warning("Pipeline execution interrupted by user")
        print("\n\n⚠ Pipeline execution interrupted by user")
        print("Partial results may be available in data/ folder")
    except Exception as e:
        logger.critical(f"Critical pipeline error: {e}\n{traceback.format_exc()}")
        print(f"\n❌ CRITICAL PIPELINE ERROR: {e}")
        print("Check logs/pipeline.log for detailed error information")

def display_analysis_summary(df: pd.DataFrame):
    """Display a comprehensive summary of the analysis"""
    try:
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY REPORT")
        print("=" * 60)
        
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
        if 'sentiment_label' in df.columns:
            sentiment_summary = df.groupby(['bank', 'sentiment_label']).size().unstack(fill_value=0)
            print(sentiment_summary)
        else:
            print("  Sentiment labels not available")
        
        # Theme analysis
        print(f"\n🎯 THEME DISTRIBUTION:")
        if 'theme' in df.columns:
            for bank in df['bank'].unique():
                bank_data = df[df['bank'] == bank]
                print(f"\n{bank}:")
                theme_counts = bank_data['theme'].value_counts()
                for theme, count in theme_counts.items():
                    percentage = (count / len(bank_data)) * 100
                    print(f"  {theme}: {count} reviews ({percentage:.1f}%)")
        else:
            print("  Theme analysis not available")
        
        # Key insights
        print(f"\n🔍 KEY INSIGHTS:")
        for bank in df['bank'].unique():
            bank_data = df[df['bank'] == bank]
            avg_rating = bank_data['rating'].mean()
            
            print(f"\n{bank}:")
            print(f"  • Average Rating: {avg_rating:.2f}/5.0")
            
            if 'sentiment_label' in df.columns:
                pos_sentiment = len(bank_data[bank_data['sentiment_label'] == 'POSITIVE'])
                pos_percentage = (pos_sentiment / len(bank_data)) * 100
                print(f"  • Positive Sentiment: {pos_percentage:.1f}%")
            
            if 'theme' in df.columns and not bank_data['theme'].isna().all():
                top_theme = bank_data['theme'].value_counts().index[0]
                print(f"  • Most Common Theme: {top_theme}")
        
    except Exception as e:
        logger.error(f"Error displaying summary: {e}")
        print(f"\n⚠ Could not generate full analysis summary: {e}")

if __name__ == "__main__":
    main()
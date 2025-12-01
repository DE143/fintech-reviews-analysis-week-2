from google_play_scraper import app, reviews, Sort
import pandas as pd
from datetime import datetime
import time

def scrape_play_store_reviews():
    """
    Scrape reviews from Google Play Store for three Ethiopian banks.
    
    The package IDs have been updated to the currently active apps
    on the Google Play Store to resolve the 404 errors.
    """
    
    # Updated Bank app IDs based on current Google Play Store packages
    bank_apps = {
        # Commercial Bank of Ethiopia Mobile Banking
        'Commercial Bank of Ethiopia': 'com.combanketh.mobilebanking',
        # Bank of Abyssinia BoA Mobile Banking
        'Bank of Abyssinia': 'com.boa.boaMobileBanking',
        # Dashen Bank Super App
        'Dashen Bank': 'com.dashen.dashensuperapp'
    }
    
    all_reviews = []
    
    # Define required columns for a robust DataFrame, even if empty
    required_columns = ['review_text', 'rating', 'date', 'bank', 'source', 'review_id']
    
    for bank_name, app_id in bank_apps.items():
        print(f"Scraping reviews for {bank_name}...")
        
        try:
            # Get app info
            app_info = app(app_id)
            print(f"App: {app_info['title']}")
            print(f"Rating: {app_info['score']:.1f}")
            print(f"Installs: {app_info['installs']}")
            
            # Scrape reviews (collecting up to 500 reviews)
            review_batch, continuation_token = reviews(
                app_id,
                lang='en',
                country='et', # Targeting Ethiopian reviews/language for relevance
                sort=Sort.MOST_RELEVANT,
                count=500,
                filter_score_with=None # Get reviews regardless of score
            )
            
            for rev in review_batch:
                all_reviews.append({
                    'review_text': rev['content'],
                    'rating': rev['score'],
                    'date': rev['at'].strftime('%Y-%m-%d'),
                    'bank': bank_name,
                    'source': 'Google Play Store',
                    'review_id': rev['reviewId']
                })
            
            print(f"Collected {len(review_batch)} reviews for {bank_name}")
            time.sleep(2)  # Be respectful to the servers
            
        except Exception as e:
            # This catch now handles 404s and other scraping errors
            print(f"Error scraping {bank_name}: {e}")
            continue
    
    # Create DataFrame
    if not all_reviews:
        # If no reviews, create an empty DataFrame with the defined structure
        df = pd.DataFrame(columns=required_columns)
    else:
        df = pd.DataFrame(all_reviews)
        
    print(f"Total reviews collected: {len(df)}")
    
    return df

if __name__ == "__main__":
    # Ensure the data directory exists before saving
    os.makedirs('../data', exist_ok=True)
    reviews_df = scrape_play_store_reviews()
    reviews_df.to_csv('data/raw_reviews.csv', index=False)
    print("Reviews saved to data/raw_reviews.csv")
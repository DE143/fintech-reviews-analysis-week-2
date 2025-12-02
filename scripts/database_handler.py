import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# --- Database Configuration (Based on typical setup) ---
class DatabaseHandler:
    def __init__(self):
        # Assuming database connection details are in environment variables
        self.db_params = {
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'ethio143go'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'fintech_reviews')
        }
        
        # Construct the database URI (using the corrected format from the previous step)
        self.db_uri = (
            f"postgresql://{self.db_params['user']}:{self.db_params['password']}@"
            f"{self.db_params['host']}:{self.db_params['port']}/{self.db_params['database']}"
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.db_uri,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        # Check if database exists, if not, create it
        try:
            if not database_exists(self.engine.url):
                create_database(self.engine.url)
                logger.info(f"Created database: {self.db_params['database']}")
            else:
                logger.info(f"Database exists: {self.db_params['database']}")
        except Exception as e:
            logger.error(f"Database setup error: {e}")
            raise
        
        self.Base = declarative_base()
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """
        Defines and creates the database schema.
        
        Crucially, tables with foreign key dependencies (reviews) must be
        dropped before the tables they depend on (banks) to avoid the error.
        """
        logger.info("Creating database tables...")
        
        # 1. Define Table Schemas (Declarative Base is helpful for explicit DDL)
        
        class Bank(self.Base):
            __tablename__ = 'banks'
            bank_id = Column(Integer, primary_key=True)
            bank_name = Column(String(255), unique=True, nullable=False)
            source = Column(String(100))
            reviews = relationship("Review", back_populates="bank")
        
        class Review(self.Base):
            __tablename__ = 'reviews'
            review_id = Column(Text, primary_key=True)
            bank_id = Column(Integer, ForeignKey('banks.bank_id', ondelete='CASCADE'), nullable=False)
            review_text = Column(Text, nullable=False)
            rating = Column(Integer, nullable=False)
            sentiment_label = Column(String(50))
            sentiment_score = Column(Float)
            theme = Column(String(100))
            date = Column(DateTime)
            created_at = Column(DateTime, default=datetime.now)
            
            bank = relationship("Bank", back_populates="reviews")
        
        try:
            # 2. Drop tables in dependency order (child before parent)
            # This resolves the "DependentObjectsStillExist" error
            logger.info("Dropping existing tables if they exist...")
            Review.__table__.drop(self.engine, checkfirst=True)
            Bank.__table__.drop(self.engine, checkfirst=True)
            
            # 3. Create tables
            logger.info("Creating new tables...")
            self.Base.metadata.create_all(self.engine)
            
            # Create indexes for performance
            with self.engine.connect() as conn:
                conn.execute(text("CREATE INDEX idx_reviews_bank_id ON reviews(bank_id)"))
                conn.execute(text("CREATE INDEX idx_reviews_rating ON reviews(rating)"))
                conn.execute(text("CREATE INDEX idx_reviews_sentiment ON reviews(sentiment_label)"))
                conn.execute(text("CREATE INDEX idx_reviews_date ON reviews(date)"))
                conn.commit()
            
            logger.info("Tables created successfully!")
            print("✓ Database tables created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            print(f"❌ Error creating tables: {e}")
            raise
    
    def insert_data(self, df):
        """
        Inserts analyzed data into the 'banks' and 'reviews' tables.
        
        Args:
            df (pd.DataFrame): The final analyzed DataFrame.
            
        Returns:
            int: Number of reviews inserted
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for insertion")
            print("⚠ No data to insert (DataFrame is empty)")
            return 0
        
        logger.info(f"Inserting data: {len(df)} rows")
        print(f"📊 Preparing to insert {len(df)} reviews...")
        
        try:
            # Ensure required columns exist
            required_columns = ['bank', 'review_text', 'rating', 'review_id']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                error_msg = f"Missing required columns: {missing_columns}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Add source column if not present
            if 'source' not in df.columns:
                df['source'] = 'Google Play Store'
            
            # Add date column if not present
            if 'date' not in df.columns:
                df['date'] = pd.to_datetime('today')
            
            # Add default sentiment if not present
            if 'sentiment_label' not in df.columns:
                df['sentiment_label'] = 'NEUTRAL'
            
            if 'sentiment_score' not in df.columns:
                df['sentiment_score'] = 0.0
            
            if 'theme' not in df.columns:
                df['theme'] = 'General'
            
            # 1. Prepare 'banks' data: Unique bank names and source
            bank_df = df[['bank', 'source']].drop_duplicates().reset_index(drop=True)
            
            # Rename 'bank' column to 'bank_name' to match the Bank model
            bank_df = bank_df.rename(columns={'bank': 'bank_name'}) 
            
            bank_df.index.name = 'bank_id' # Set index name for later use
            bank_df = bank_df.reset_index().rename(columns={'index': 'bank_id'})
            bank_df['bank_id'] = bank_df['bank_id'] + 1 # Start IDs from 1
            
            logger.info(f"Prepared {len(bank_df)} unique banks for insertion")
            
            # Insert bank data
            bank_df.to_sql('banks', self.engine, if_exists='append', index=False)
            logger.info(f"Inserted {len(bank_df)} banks")
            
            # 2. Create bank_id map
            bank_id_map = bank_df.set_index('bank_name')['bank_id'].to_dict()
            
            # 3. Prepare 'reviews' data with foreign key
            reviews_df = df.copy()
            # Map the bank name from the original DF ('bank' column) to the new bank_id
            reviews_df['bank_id'] = reviews_df['bank'].map(bank_id_map)
            
            # Check for any unmapped banks
            unmapped = reviews_df[reviews_df['bank_id'].isna()]
            if not unmapped.empty:
                logger.warning(f"{len(unmapped)} reviews have unmapped banks")
            
            # Select and rename columns for the reviews table
            reviews_df = reviews_df[[
                'review_id', 'bank_id', 'review_text', 'rating', 'sentiment_label', 
                'sentiment_score', 'theme', 'date'
            ]].dropna(subset=['bank_id', 'review_id', 'review_text'])
            
            # Convert date column to datetime object for proper storage
            reviews_df['date'] = pd.to_datetime(reviews_df['date'], errors='coerce')
            
            # Drop rows with invalid dates
            reviews_df = reviews_df.dropna(subset=['date'])
            
            logger.info(f"Prepared {len(reviews_df)} reviews for insertion")
            
            # Insert review data in chunks to handle large datasets
            chunk_size = 1000
            total_inserted = 0
            
            for i in range(0, len(reviews_df), chunk_size):
                chunk = reviews_df.iloc[i:i + chunk_size]
                chunk.to_sql('reviews', self.engine, if_exists='append', index=False)
                total_inserted += len(chunk)
                logger.info(f"Inserted chunk {i//chunk_size + 1}: {len(chunk)} reviews")
            
            logger.info(f"Data insertion completed: {total_inserted} reviews inserted")
            print(f"✓ Successfully inserted {total_inserted} reviews into database")
            
            return total_inserted
            
        except Exception as e:
            logger.error(f"Error inserting data: {e}")
            print(f"❌ Error inserting data: {e}")
            raise
    
    def run_queries(self):
        """
        Runs example SQL queries to demonstrate functionality.
        """
        logger.info("Running analytical queries...")
        print("🔍 Running database queries...")
        
        try:
            with self.engine.connect() as connection:
                # Query 1: Summary statistics
                query_1 = text("""
                SELECT 
                    COUNT(*) as total_reviews,
                    COUNT(DISTINCT bank_id) as unique_banks,
                    ROUND(AVG(rating), 2) as avg_rating,
                    MIN(date) as earliest_review,
                    MAX(date) as latest_review
                FROM reviews;
                """)
                
                result_1 = connection.execute(query_1)
                summary = result_1.fetchone()
                
                print("\n" + "="*60)
                print("DATABASE SUMMARY STATISTICS")
                print("="*60)
                print(f"Total Reviews: {summary[0]:,}")
                print(f"Unique Banks: {summary[1]}")
                print(f"Average Rating: {summary[2]:.2f}/5")
                print(f"Date Range: {summary[3].strftime('%Y-%m-%d') if summary[3] else 'N/A'} to {summary[4].strftime('%Y-%m-%d') if summary[4] else 'N/A'}")
                
                # Query 2: Detailed bank statistics
                query_2 = text("""
                SELECT 
                    b.bank_name, 
                    COUNT(r.review_id) AS total_reviews, 
                    ROUND(AVG(r.rating), 2) AS average_rating,
                    ROUND(SUM(CASE WHEN r.sentiment_label = 'POSITIVE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as positive_pct
                FROM reviews r
                JOIN banks b ON r.bank_id = b.bank_id
                GROUP BY b.bank_name
                ORDER BY average_rating DESC;
                """)
                
                result_2 = connection.execute(query_2)
                print("\n" + "="*60)
                print("BANK PERFORMANCE ANALYSIS")
                print("="*60)
                print(f"{'Bank Name':<20} {'Reviews':<10} {'Avg Rating':<12} {'Positive %':<12}")
                print("-"*60)
                
                for row in result_2:
                    print(f"{row[0]:<20} {row[1]:<10} {row[2]:<12} {row[3]:<12.1f}%")
                
                # Query 3: Sentiment distribution
                query_3 = text("""
                SELECT 
                    sentiment_label,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews), 1) as percentage
                FROM reviews
                GROUP BY sentiment_label
                ORDER BY count DESC;
                """)
                
                result_3 = connection.execute(query_3)
                print("\n" + "="*60)
                print("SENTIMENT DISTRIBUTION")
                print("="*60)
                for row in result_3:
                    print(f"{row[0]:<15} {row[1]:<10} reviews ({row[2]:.1f}%)")
                
                # Query 4: Top themes
                query_4 = text("""
                SELECT 
                    theme,
                    COUNT(*) as count,
                    ROUND(AVG(rating), 2) as avg_rating
                FROM reviews
                WHERE theme IS NOT NULL AND theme != 'General'
                GROUP BY theme
                ORDER BY count DESC
                LIMIT 10;
                """)
                
                result_4 = connection.execute(query_4)
                print("\n" + "="*60)
                print("TOP 10 THEMES")
                print("="*60)
                for row in result_4:
                    print(f"{row[0]:<25} {row[1]:<8} reviews (Avg: {row[2]:.1f}/5)")
                
                # Query 5: Recent reviews
                query_5 = text("""
                SELECT 
                    b.bank_name,
                    LEFT(r.review_text, 50) || '...' as preview,
                    r.rating,
                    r.sentiment_label,
                    r.date
                FROM reviews r
                JOIN banks b ON r.bank_id = b.bank_id
                ORDER BY r.date DESC
                LIMIT 5;
                """)
                
                result_5 = connection.execute(query_5)
                print("\n" + "="*60)
                print("MOST RECENT REVIEWS")
                print("="*60)
                for row in result_5:
                    print(f"{row[0]}: '{row[1]}' ({row[2]}/5, {row[3]}) - {row[4].strftime('%Y-%m-%d')}")
                
                # Query 6: Rating distribution
                query_6 = text("""
                SELECT 
                    rating,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews), 1) as percentage
                FROM reviews
                GROUP BY rating
                ORDER BY rating DESC;
                """)
                
                result_6 = connection.execute(query_6)
                print("\n" + "="*60)
                print("RATING DISTRIBUTION")
                print("="*60)
                for row in result_6:
                    stars = '★' * int(row[0]) + '☆' * (5 - int(row[0]))
                    print(f"{stars} ({row[0]}/5): {row[1]:<8} reviews ({row[2]:.1f}%)")
        
        except Exception as e:
            logger.error(f"Error running queries: {e}")
            print(f"❌ Error running queries: {e}")
            raise
        
        finally:
            print("\n" + "="*60)
            print("QUERIES COMPLETED SUCCESSFULLY")
            print("="*60)
            logger.info("All queries executed successfully")
    
    def get_record_counts(self):
        """
        Get basic record counts from database for verification
        
        Returns:
            dict: Dictionary with record counts
        """
        counts = {}
        try:
            with self.engine.connect() as connection:
                # Total reviews
                result = connection.execute(text("SELECT COUNT(*) FROM reviews;"))
                counts['total_reviews'] = result.fetchone()[0]
                
                # Banks count
                result = connection.execute(text("SELECT COUNT(*) FROM banks;"))
                counts['total_banks'] = result.fetchone()[0]
                
                # Reviews per bank
                result = connection.execute(text("""
                    SELECT b.bank_name, COUNT(r.review_id) as review_count
                    FROM banks b
                    LEFT JOIN reviews r ON b.bank_id = r.bank_id
                    GROUP BY b.bank_name
                    ORDER BY review_count DESC;
                """))
                counts['reviews_per_bank'] = dict(result.fetchall())
                
                logger.info(f"Retrieved database counts: {counts['total_reviews']} reviews, {counts['total_banks']} banks")
                
        except Exception as e:
            logger.error(f"Error getting record counts: {e}")
            counts['error'] = str(e)
        
        return counts
    
    def close(self):
        """Close database connections"""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


if __name__ == '__main__':
    # Setup logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    
    # This block is for testing the database setup independently
    print("="*60)
    print("DATABASE HANDLER TEST")
    print("="*60)
    
    try:
        db_handler = DatabaseHandler()
        
        # Test table creation
        print("\n1. Creating tables...")
        db_handler.create_tables()
        
        # Create mock data
        print("\n2. Generating mock data...")
        from datetime import datetime, timedelta
        import numpy as np
        
        mock_df = pd.DataFrame({
            'bank': ['Commercial Bank of Ethiopia', 'Commercial Bank of Ethiopia', 
                    'Bank of Abyssinia', 'Dashen Bank', 'Awash Bank'],
            'source': ['Google Play Store'] * 5,
            'review_text': [
                'Excellent mobile banking app with great features',
                'The app crashes frequently, needs improvement',
                'User-friendly interface and reliable service',
                'Slow transaction processing, please fix',
                'Best banking experience in Ethiopia!'
            ],
            'rating': [5, 1, 4, 2, 5],
            'sentiment_label': ['POSITIVE', 'NEGATIVE', 'POSITIVE', 'NEGATIVE', 'POSITIVE'],
            'sentiment_score': [0.9, 0.1, 0.7, 0.3, 0.95],
            'theme': ['Functionality', 'Performance', 'UI/UX', 'Performance', 'Overall Experience'],
            'date': [datetime.now() - timedelta(days=i) for i in range(5)],
            'review_id': [str(i) for i in range(1, 6)]
        })
        
        # Test data insertion
        print(f"\n3. Inserting {len(mock_df)} mock reviews...")
        inserted_count = db_handler.insert_data(mock_df)
        print(f"   Inserted {inserted_count} reviews")
        
        # Test queries
        print("\n4. Running analytical queries...")
        db_handler.run_queries()
        
        # Test record counts
        print("\n5. Testing record counts...")
        counts = db_handler.get_record_counts()
        print(f"   Total reviews in DB: {counts.get('total_reviews', 0)}")
        print(f"   Total banks in DB: {counts.get('total_banks', 0)}")
        
        # Clean up
        db_handler.close()
        
        print("\n" + "="*60)
        print("DATABASE TEST COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
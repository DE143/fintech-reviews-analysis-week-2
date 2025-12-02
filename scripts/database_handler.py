import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, text # <--- ADDED 'text' HERE
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime # Added datetime import for the __main__ block

# Load environment variables
load_dotenv()

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
        
        # Create engine
        self.engine = create_engine(self.db_uri)
        
        # Check if database exists, if not, create it
        if not database_exists(self.engine.url):
            create_database(self.engine.url)
        
        self.Base = declarative_base()
        
    def create_tables(self):
        """
        Defines and creates the database schema.
        
        Crucially, tables with foreign key dependencies (reviews) must be
        dropped before the tables they depend on (banks) to avoid the error.
        """
        
        # 1. Define Table Schemas (Declarative Base is helpful for explicit DDL)
        
        class Bank(self.Base):
            __tablename__ = 'banks'
            bank_id = Column(Integer, primary_key=True)
            bank_name = Column(String(255), unique=True, nullable=False)
            source = Column(String(100))

        class Review(self.Base):
            __tablename__ = 'reviews'
            review_id = Column(Text, primary_key=True)
            bank_id = Column(Integer, ForeignKey('banks.bank_id'), nullable=False) # Foreign Key
            review_text = Column(Text, nullable=False)
            rating = Column(Integer, nullable=False)
            sentiment_label = Column(String(50))
            sentiment_score = Column(Float)
            theme = Column(String(100))
            date = Column(DateTime)
        
        # 2. Drop tables in dependency order (child before parent)
        # This resolves the "DependentObjectsStillExist" error
        Review.__table__.drop(self.engine, checkfirst=True)
        Bank.__table__.drop(self.engine, checkfirst=True)
        
        # 3. Create tables
        self.Base.metadata.create_all(self.engine)
        print("Tables created successfully!")

    def insert_data(self, df):
        """
        Inserts analyzed data into the 'banks' and 'reviews' tables.
        
        Args:
            df (pd.DataFrame): The final analyzed DataFrame.
        """
        
        # 1. Prepare 'banks' data: Unique bank names and source
        bank_df = df[['bank', 'source']].drop_duplicates().reset_index(drop=True)
        
        # **FIX 1: Rename 'bank' column to 'bank_name' to match the Bank model**
        bank_df = bank_df.rename(columns={'bank': 'bank_name'}) 
        
        bank_df.index.name = 'bank_id' # Set index name for later use
        bank_df = bank_df.reset_index().rename(columns={'index': 'bank_id'})
        bank_df['bank_id'] = bank_df['bank_id'] + 1 # Start IDs from 1
        
        # Insert bank data
        bank_df.to_sql('banks', self.engine, if_exists='append', index=False)
        
        # 2. Create bank_id map (Use the original 'bank' column for mapping)
        # We use 'bank_name' (the renamed column) to create the map
        bank_id_map = bank_df.set_index('bank_name')['bank_id'].to_dict()
        
        # 3. Prepare 'reviews' data with foreign key
        reviews_df = df.copy()
        # Map the bank name from the original DF ('bank' column) to the new bank_id
        reviews_df['bank_id'] = reviews_df['bank'].map(bank_id_map)
        
        # Select and rename columns for the reviews table
        reviews_df = reviews_df[[
            'review_id', 'bank_id', 'review_text', 'rating', 'sentiment_label', 
            'sentiment_score', 'theme', 'date'
        ]]
        
        # Convert date column to datetime object for proper storage
        reviews_df['date'] = pd.to_datetime(reviews_df['date'])

        # Insert review data
        reviews_df.to_sql('reviews', self.engine, if_exists='append', index=False)
        
        print("Data inserted successfully!")

    def run_queries(self):
        """
        Runs example SQL queries to demonstrate functionality.
        """
        query_1 = """
        SELECT b.bank_name, count(r.review_id) AS total_reviews, 
               AVG(r.rating) AS average_rating
        FROM reviews r
        JOIN banks b ON r.bank_id = b.bank_id
        GROUP BY b.bank_name
        ORDER BY average_rating DESC;
        """
        
        query_2 = """
        SELECT b.bank_name, r.theme, COUNT(*) as theme_count
        FROM reviews r
        JOIN banks b ON r.bank_id = b.bank_id
        WHERE r.sentiment_label = 'NEGATIVE'
        GROUP BY b.bank_name, r.theme
        ORDER BY b.bank_name, theme_count DESC;
        """
        
        with self.engine.connect() as connection:
            # **FIX 2: Wrap the raw SQL string with text() for SQLAlchemy 2.0 style execution**
            result_1 = connection.execute(text(query_1)) 
            print("\n--- Summary of Average Ratings and Review Count ---")
            for row in result_1:
                print(f"Bank: {row[0]}, Reviews: {row[1]}, Avg. Rating: {row[2]:.2f}")

            # **FIX 2: Wrap the raw SQL string with text()**
            result_2 = connection.execute(text(query_2))
            print("\n--- Top Negative Themes by Bank ---")
            current_bank = None
            for row in result_2:
                if row[0] != current_bank:
                    print(f"\nBank: {row[0]}")
                    current_bank = row[0]
                print(f"  - {row[1]}: {row[2]} negative reviews")
        
        print("\nExample queries executed successfully.")


if __name__ == '__main__':
    # This block is for testing the database setup independently
    # Note: Requires environment variables set up locally to run.
    print("Running database handler test...")
    db_handler = DatabaseHandler()
    db_handler.create_tables()
    # Mock data load:
    mock_df = pd.DataFrame({
        'bank': ['CBE', 'CBE', 'BOA'],
        'source': ['GPS', 'GPS', 'GPS'],
        'review_text': ['good', 'bad', 'okay'],
        'rating': [5, 1, 3],
        'sentiment_label': ['POSITIVE', 'NEGATIVE', 'POSITIVE'],
        'sentiment_score': [0.9, 0.1, 0.5],
        'theme': ['Functionality', 'Performance', 'UI/UX'],
        'date': [datetime.now()] * 3,
        'review_id': ['1', '2', '3']
    })
    db_handler.insert_data(mock_df)
    db_handler.run_queries()
    print("Database test completed.")
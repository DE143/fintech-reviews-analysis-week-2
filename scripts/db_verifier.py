"""
Database verification module for Fintech Reviews Analysis Project
Verifies database integrity by comparing source data with database contents
"""
import pandas as pd
import psycopg2
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

class DatabaseVerifier:
    """Verifies database contents against source data"""
    
    def __init__(self, db_uri: str):
        """
        Initialize DatabaseVerifier with database URI
        
        Args:
            db_uri: SQLAlchemy database URI
        """
        self.db_uri = db_uri
        self.engine = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.engine = create_engine(self.db_uri)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to database for verification")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
    
    def get_database_counts(self) -> Dict[str, Any]:
        """
        Get record counts from database for verification
        
        Returns:
            Dictionary with database counts
        """
        counts = {}
        try:
            if not self.engine:
                self.connect()
            
            with self.engine.connect() as connection:
                # Get total number of reviews
                result = connection.execute(text("SELECT COUNT(*) FROM reviews;"))
                counts['total_reviews'] = result.fetchone()[0]
                
                # Get total number of banks
                result = connection.execute(text("SELECT COUNT(*) FROM banks;"))
                counts['total_banks'] = result.fetchone()[0]
                
                # Get counts per bank
                result = connection.execute(text("""
                    SELECT b.bank_name, COUNT(r.review_id) as review_count 
                    FROM reviews r
                    JOIN banks b ON r.bank_id = b.bank_id
                    GROUP BY b.bank_name 
                    ORDER BY review_count DESC;
                """))
                bank_counts = result.fetchall()
                counts['bank_counts'] = dict(bank_counts)
                
                # Get unique banks count
                counts['unique_banks'] = len(counts['bank_counts'])
                
                # Get sentiment distribution
                try:
                    result = connection.execute(text("""
                        SELECT sentiment_label, COUNT(*) 
                        FROM reviews 
                        GROUP BY sentiment_label
                        ORDER BY COUNT(*) DESC;
                    """))
                    sentiment_counts = result.fetchall()
                    counts['sentiment_counts'] = dict(sentiment_counts)
                except Exception as e:
                    logger.warning(f"Could not get sentiment counts: {e}")
                    counts['sentiment_counts'] = {}
                
                # Get theme distribution
                try:
                    result = connection.execute(text("""
                        SELECT theme, COUNT(*) 
                        FROM reviews 
                        WHERE theme IS NOT NULL AND theme != 'General'
                        GROUP BY theme
                        ORDER BY COUNT(*) DESC
                        LIMIT 10;
                    """))
                    theme_counts = result.fetchall()
                    counts['theme_counts'] = dict(theme_counts)
                except Exception as e:
                    logger.warning(f"Could not get theme counts: {e}")
                    counts['theme_counts'] = {}
                
                # Get rating distribution
                try:
                    result = connection.execute(text("""
                        SELECT rating, COUNT(*) 
                        FROM reviews 
                        GROUP BY rating
                        ORDER BY rating DESC;
                    """))
                    rating_counts = result.fetchall()
                    counts['rating_counts'] = dict(rating_counts)
                except Exception as e:
                    logger.warning(f"Could not get rating counts: {e}")
                    counts['rating_counts'] = {}
                
                logger.info(f"Database counts retrieved: {counts['total_reviews']} total reviews")
                
        except Exception as e:
            logger.error(f"Error getting database counts: {e}")
            counts['error'] = str(e)
        
        return counts
    
    def get_source_counts(self, source_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get record counts from source dataframe
        
        Args:
            source_df: Source DataFrame to verify against
            
        Returns:
            Dictionary with source counts
        """
        counts = {}
        
        try:
            if source_df is None or source_df.empty:
                counts['error'] = "Source DataFrame is empty or None"
                return counts
            
            counts['total_reviews'] = len(source_df)
            
            if 'bank' in source_df.columns:
                bank_counts = source_df['bank'].value_counts().to_dict()
                counts['bank_counts'] = bank_counts
                counts['unique_banks'] = len(bank_counts)
            else:
                counts['bank_counts'] = {}
                counts['unique_banks'] = 0
            
            if 'sentiment_label' in source_df.columns:
                sentiment_counts = source_df['sentiment_label'].value_counts().to_dict()
                counts['sentiment_counts'] = sentiment_counts
            else:
                counts['sentiment_counts'] = {}
            
            if 'theme' in source_df.columns:
                theme_counts = source_df['theme'].value_counts().to_dict()
                counts['theme_counts'] = theme_counts
            else:
                counts['theme_counts'] = {}
            
            if 'rating' in source_df.columns:
                rating_counts = source_df['rating'].value_counts().to_dict()
                counts['rating_counts'] = rating_counts
            else:
                counts['rating_counts'] = {}
            
            # Count unique review texts (to detect duplicates)
            if 'review_text' in source_df.columns:
                counts['unique_review_texts'] = source_df['review_text'].nunique()
            else:
                counts['unique_review_texts'] = 0
            
            logger.info(f"Source counts calculated: {counts['total_reviews']} total reviews")
            
        except Exception as e:
            logger.error(f"Error calculating source counts: {e}")
            counts['error'] = str(e)
        
        return counts
    
    def compare_counts(self, db_counts: Dict[str, Any], source_counts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare database counts with source counts
        
        Args:
            db_counts: Database record counts
            source_counts: Source DataFrame record counts
            
        Returns:
            Dictionary with comparison results and mismatches
        """
        comparison = {
            'integrity_check': True,
            'mismatches': [],
            'details': {},
            'summary': {}
        }
        
        try:
            # Compare total review counts
            db_total = db_counts.get('total_reviews', 0)
            source_total = source_counts.get('total_reviews', 0)
            
            comparison['details']['total_reviews'] = {
                'database': db_total,
                'source': source_total,
                'match': db_total == source_total,
                'difference': abs(db_total - source_total)
            }
            
            if db_total != source_total:
                comparison['integrity_check'] = False
                comparison['mismatches'].append(
                    f"Total review count mismatch: DB={db_total}, Source={source_total} (Diff: {db_total - source_total})"
                )
            
            # Compare unique banks count
            db_unique_banks = db_counts.get('unique_banks', 0)
            source_unique_banks = source_counts.get('unique_banks', 0)
            
            comparison['details']['unique_banks'] = {
                'database': db_unique_banks,
                'source': source_unique_banks,
                'match': db_unique_banks == source_unique_banks,
                'difference': abs(db_unique_banks - source_unique_banks)
            }
            
            if db_unique_banks != source_unique_banks:
                comparison['integrity_check'] = False
                comparison['mismatches'].append(
                    f"Unique banks count mismatch: DB={db_unique_banks}, Source={source_unique_banks}"
                )
            
            # Compare bank-specific counts
            db_banks = db_counts.get('bank_counts', {})
            source_banks = source_counts.get('bank_counts', {})
            
            # Find common and different banks
            all_banks = set(list(db_banks.keys()) + list(source_banks.keys()))
            bank_matches = []
            bank_mismatches = []
            
            for bank in all_banks:
                db_count = db_banks.get(bank, 0)
                source_count = source_banks.get(bank, 0)
                
                if db_count == source_count:
                    bank_matches.append({
                        'bank': bank,
                        'database': db_count,
                        'source': source_count,
                        'match': True
                    })
                else:
                    bank_mismatches.append({
                        'bank': bank,
                        'database': db_count,
                        'source': source_count,
                        'match': False,
                        'difference': db_count - source_count
                    })
            
            comparison['details']['bank_counts'] = {
                'matches': bank_matches,
                'mismatches': bank_mismatches,
                'total_matches': len(bank_matches),
                'total_mismatches': len(bank_mismatches)
            }
            
            # Add mismatches to main list
            for mismatch in bank_mismatches:
                comparison['mismatches'].append(
                    f"Bank '{mismatch['bank']}' count mismatch: DB={mismatch['database']}, Source={mismatch['source']} (Diff: {mismatch['difference']})"
                )
            
            # Create summary statistics
            comparison['summary'] = {
                'database_total': db_total,
                'source_total': source_total,
                'database_banks': db_unique_banks,
                'source_banks': source_unique_banks,
                'total_mismatches': len(comparison['mismatches']),
                'bank_matches': len(bank_matches),
                'bank_mismatches': len(bank_mismatches),
                'data_integrity': 'PASS' if comparison['integrity_check'] else 'FAIL',
                'match_percentage': round(len(bank_matches) / max(len(all_banks), 1) * 100, 1)
            }
            
            logger.info(f"Count comparison completed: Integrity check {'PASSED' if comparison['integrity_check'] else 'FAILED'}")
            
        except Exception as e:
            logger.error(f"Error comparing counts: {e}")
            comparison['integrity_check'] = False
            comparison['mismatches'].append(f"Comparison error: {str(e)}")
            comparison['summary']['data_integrity'] = 'ERROR'
        
        return comparison
    
    def run_simple_queries(self) -> Dict[str, Any]:
        """
        Run simple verification queries against the live database
        
        Returns:
            Dictionary with query results
        """
        queries = {}
        
        try:
            if not self.engine:
                self.connect()
            
            with self.engine.connect() as connection:
                # Query 1: Total rows in reviews table
                result = connection.execute(text("SELECT COUNT(*) as total_rows FROM reviews;"))
                queries['total_rows'] = result.fetchone()[0]
                
                # Query 2: Counts per bank
                result = connection.execute(text("""
                    SELECT b.bank_name, COUNT(r.review_id) as review_count 
                    FROM reviews r
                    JOIN banks b ON r.bank_id = b.bank_id
                    GROUP BY b.bank_name 
                    ORDER BY review_count DESC;
                """))
                queries['counts_per_bank'] = result.fetchall()
                
                # Query 3: Average rating per bank
                result = connection.execute(text("""
                    SELECT b.bank_name, ROUND(AVG(r.rating), 2) as avg_rating 
                    FROM reviews r
                    JOIN banks b ON r.bank_id = b.bank_id
                    GROUP BY b.bank_name 
                    ORDER BY avg_rating DESC;
                """))
                queries['avg_rating_per_bank'] = result.fetchall()
                
                # Query 4: Date range of reviews
                result = connection.execute(text("""
                    SELECT MIN(date), MAX(date) 
                    FROM reviews;
                """))
                date_range = result.fetchone()
                queries['date_range'] = {
                    'min': date_range[0],
                    'max': date_range[1]
                }
                
                # Query 5: Database size information
                try:
                    result = connection.execute(text("""
                        SELECT 
                            pg_size_pretty(pg_database_size(current_database())) as db_size,
                            pg_size_pretty(pg_total_relation_size('reviews')) as reviews_size,
                            pg_size_pretty(pg_total_relation_size('banks')) as banks_size;
                    """))
                    size_info = result.fetchone()
                    queries['database_size'] = {
                        'total': size_info[0],
                        'reviews': size_info[1],
                        'banks': size_info[2]
                    }
                except:
                    queries['database_size'] = {'error': 'Size query not supported'}
                
                logger.info("Simple verification queries executed successfully")
                
        except Exception as e:
            logger.error(f"Error running verification queries: {e}")
            queries['error'] = str(e)
        
        return queries
    
    def verify_database_contents(self, source_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Main verification function - compares source data with database
        
        Args:
            source_df: Source DataFrame to verify against
            
        Returns:
            Dictionary with complete verification results
        """
        results = {
            'verification_timestamp': datetime.now().isoformat(),
            'source_data_shape': source_df.shape if source_df is not None else None,
            'source_columns': list(source_df.columns) if source_df is not None else [],
            'record_counts': {},
            'simple_queries': {},
            'verification_summary': {},
            'integrity_check': False
        }
        
        try:
            # Connect to database
            self.connect()
            
            # Get counts from database
            db_counts = self.get_database_counts()
            results['record_counts']['database'] = db_counts
            
            # Get counts from source
            source_counts = self.get_source_counts(source_df)
            results['record_counts']['source'] = source_counts
            
            # Compare counts
            comparison = self.compare_counts(db_counts, source_counts)
            results['comparison'] = comparison
            results['integrity_check'] = comparison['integrity_check']
            
            # Run simple queries for quick verification
            simple_queries = self.run_simple_queries()
            results['simple_queries'] = simple_queries
            
            # Create verification summary
            summary = {
                'verification_time': results['verification_timestamp'],
                'database_connection': 'SUCCESS',
                'source_rows': results['source_data_shape'][0] if results['source_data_shape'] else 0,
                'source_columns': len(results['source_columns']),
                'database_rows': db_counts.get('total_reviews', 0),
                'database_banks': db_counts.get('unique_banks', 0),
                'simple_queries_executed': len(simple_queries) if 'error' not in simple_queries else 0,
                'total_mismatches': len(comparison.get('mismatches', [])),
                'data_integrity': 'PASS' if comparison['integrity_check'] else 'FAIL'
            }
            
            # Add comparison summary if available
            if 'summary' in comparison:
                summary.update(comparison['summary'])
            
            results['verification_summary'] = summary
            
            logger.info(f"Database verification completed: {summary.get('data_integrity', 'UNKNOWN')}")
            
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            results['error'] = str(e)
            results['integrity_check'] = False
            results['verification_summary'] = {
                'verification_time': results['verification_timestamp'],
                'database_connection': 'FAILED',
                'error': str(e),
                'data_integrity': 'ERROR'
            }
        
        finally:
            # Disconnect from database
            self.disconnect()
        
        return results
    
    def save_verification_report(self, verification_results: Dict[str, Any], 
                                 filename: str = None) -> str:
        """
        Save verification results to a text file
        
        Args:
            verification_results: Results from verify_database_contents
            filename: Optional custom filename
            
        Returns:
            Path to the saved report file
        """
        try:
            os.makedirs('verification', exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"db_verification_report_{timestamp}.txt"
            
            filepath = f"verification/{filename}"
            
            with open(filepath, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("DATABASE VERIFICATION REPORT\n")
                f.write("=" * 80 + "\n\n")
                
                # Basic information
                f.write("BASIC INFORMATION\n")
                f.write("-" * 80 + "\n")
                f.write(f"Verification Time: {verification_results.get('verification_timestamp', 'N/A')}\n")
                f.write(f"Source Data Shape: {verification_results.get('source_data_shape', 'N/A')}\n")
                f.write(f"Source Columns: {', '.join(verification_results.get('source_columns', []))}\n")
                f.write(f"Database Integrity Check: {'PASSED' if verification_results.get('integrity_check', False) else 'FAILED'}\n\n")
                
                # Record counts
                f.write("RECORD COUNTS COMPARISON\n")
                f.write("-" * 80 + "\n")
                
                record_counts = verification_results.get('record_counts', {})
                
                # Database counts
                if 'database' in record_counts:
                    db_counts = record_counts['database']
                    f.write("\nDATABASE COUNTS:\n")
                    f.write(f"  Total Reviews: {db_counts.get('total_reviews', 'N/A'):,}\n")
                    f.write(f"  Total Banks: {db_counts.get('total_banks', 'N/A'):,}\n")
                    f.write(f"  Unique Banks: {db_counts.get('unique_banks', 'N/A'):,}\n")
                
                # Source counts
                if 'source' in record_counts:
                    source_counts = record_counts['source']
                    f.write("\nSOURCE DATA COUNTS:\n")
                    f.write(f"  Total Reviews: {source_counts.get('total_reviews', 'N/A'):,}\n")
                    f.write(f"  Unique Banks: {source_counts.get('unique_banks', 'N/A'):,}\n")
                    f.write(f"  Unique Review Texts: {source_counts.get('unique_review_texts', 'N/A'):,}\n")
                
                # Simple queries results
                f.write("\n" + "-" * 80 + "\n")
                f.write("DATABASE QUERY RESULTS\n")
                f.write("-" * 80 + "\n")
                
                simple_queries = verification_results.get('simple_queries', {})
                
                if 'total_rows' in simple_queries:
                    f.write(f"\nTotal Rows in Database: {simple_queries['total_rows']:,}\n")
                
                if 'counts_per_bank' in simple_queries:
                    f.write("\nCounts Per Bank:\n")
                    for bank, count in simple_queries['counts_per_bank']:
                        f.write(f"  {bank}: {count:,} reviews\n")
                
                if 'avg_rating_per_bank' in simple_queries:
                    f.write("\nAverage Rating Per Bank:\n")
                    for bank, avg_rating in simple_queries['avg_rating_per_bank']:
                        f.write(f"  {bank}: {avg_rating}/5.0\n")
                
                if 'database_size' in simple_queries:
                    size_info = simple_queries['database_size']
                    f.write("\nDatabase Size Information:\n")
                    if 'total' in size_info:
                        f.write(f"  Total Database Size: {size_info.get('total', 'N/A')}\n")
                    if 'reviews' in size_info:
                        f.write(f"  Reviews Table Size: {size_info.get('reviews', 'N/A')}\n")
                    if 'banks' in size_info:
                        f.write(f"  Banks Table Size: {size_info.get('banks', 'N/A')}\n")
                
                # Mismatches if any
                comparison = verification_results.get('comparison', {})
                mismatches = comparison.get('mismatches', [])
                if mismatches:
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("MISMATCHES DETECTED\n")
                    f.write("-" * 80 + "\n")
                    for mismatch in mismatches:
                        f.write(f"• {mismatch}\n")
                else:
                    f.write("\n" + "-" * 80 + "\n")
                    f.write("NO MISMATCHES DETECTED\n")
                    f.write("-" * 80 + "\n")
                    f.write("✓ All counts match between source and database\n")
                
                # Summary
                f.write("\n" + "-" * 80 + "\n")
                f.write("VERIFICATION SUMMARY\n")
                f.write("-" * 80 + "\n")
                
                summary = verification_results.get('verification_summary', {})
                for key, value in summary.items():
                    # Format the key for display
                    display_key = key.replace('_', ' ').title()
                    
                    # Format values appropriately
                    if isinstance(value, float):
                        if '%' in display_key:
                            f.write(f"{display_key}: {value:.1f}%\n")
                        else:
                            f.write(f"{display_key}: {value:.2f}\n")
                    elif isinstance(value, int):
                        if 'rows' in key or 'count' in key or 'matches' in key:
                            f.write(f"{display_key}: {value:,}\n")
                        else:
                            f.write(f"{display_key}: {value}\n")
                    else:
                        f.write(f"{display_key}: {value}\n")
            
            logger.info(f"Verification report saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save verification report: {e}")
            return ""

# Example standalone usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("="*80)
    print("DATABASE VERIFIER - STANDALONE TEST")
    print("="*80)
    
    # Example configuration - using same as DatabaseHandler
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    db_uri = (
        f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'ethio143go')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'fintech_reviews')}"
    )
    
    # Load source data
    try:
        source_file = 'data/final_analyzed_reviews.csv'
        if os.path.exists(source_file):
            source_df = pd.read_csv(source_file)
            print(f"✓ Loaded source data: {len(source_df):,} rows, {len(source_df.columns)} columns")
            
            # Create verifier and run verification
            verifier = DatabaseVerifier(db_uri)
            print("\nRunning database verification...")
            results = verifier.verify_database_contents(source_df)
            
            # Print summary
            print("\n" + "="*80)
            print("VERIFICATION RESULTS")
            print("="*80)
            
            if results.get('integrity_check'):
                print("✅ DATABASE INTEGRITY VERIFIED SUCCESSFULLY!")
            else:
                print("❌ DATABASE INTEGRITY CHECK FAILED")
                if 'mismatches' in results.get('comparison', {}):
                    print("\nMismatches found:")
                    for mismatch in results['comparison']['mismatches']:
                        print(f"  • {mismatch}")
            
            # Display key statistics
            summary = results.get('verification_summary', {})
            print(f"\n📊 KEY STATISTICS:")
            print(f"  Source Rows: {summary.get('source_rows', 0):,}")
            print(f"  Database Rows: {summary.get('database_rows', 0):,}")
            print(f"  Source Banks: {summary.get('source_banks', 0):,}")
            print(f"  Database Banks: {summary.get('database_banks', 0):,}")
            print(f"  Match Percentage: {summary.get('match_percentage', 0):.1f}%")
            print(f"  Total Mismatches: {summary.get('total_mismatches', 0):,}")
            
            # Save report
            report_file = verifier.save_verification_report(results, "verification_test.txt")
            print(f"\n📄 Verification report saved to: {report_file}")
            
        else:
            print(f"⚠ Source file not found: {source_file}")
            print("Creating mock data for testing...")
            
            # Create mock data for testing
            from datetime import datetime, timedelta
            import numpy as np
            
            source_df = pd.DataFrame({
                'bank': ['CBE'] * 50 + ['BOA'] * 30 + ['Awash'] * 20,
                'review_text': [f'Review {i}' for i in range(100)],
                'rating': np.random.randint(1, 6, 100),
                'sentiment_label': np.random.choice(['POSITIVE', 'NEUTRAL', 'NEGATIVE'], 100),
                'theme': np.random.choice(['UI/UX', 'Performance', 'Security', 'Features'], 100),
                'date': [datetime.now() - timedelta(days=i) for i in range(100)],
                'review_id': [str(i) for i in range(100)]
            })
            
            print(f"Created mock data: {len(source_df):,} rows")
            
            # Create verifier and run verification
            verifier = DatabaseVerifier(db_uri)
            print("\nRunning database verification with mock data...")
            results = verifier.verify_database_contents(source_df)
            
            # Display results
            print(f"\nVerification completed: {'PASS' if results.get('integrity_check') else 'FAIL'}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("VERIFICATION TEST COMPLETED")
    print("="*80)
    
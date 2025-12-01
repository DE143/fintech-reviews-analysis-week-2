import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import numpy as np
import os

class ReviewVisualizer:
    def __init__(self, df):
        self.df = df
        # Ensure matplotlib style is compatible with current versions
        try:
            plt.style.use('seaborn-v0_8')
        except:
            plt.style.use('seaborn') # Fallback if v0_8 is not available
        
    def _ensure_report_directory(self, path='reports'):
        """Ensures the output directory exists."""
        os.makedirs(path, exist_ok=True)
        
    def plot_rating_distribution(self):
        """Plot rating distribution by bank"""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        for i, bank in enumerate(self.df['bank'].unique()):
            bank_data = self.df[self.df['bank'] == bank]
            rating_counts = bank_data['rating'].value_counts().sort_index()
            
            axes[i].bar(rating_counts.index, rating_counts.values, color='skyblue', alpha=0.7)
            axes[i].set_title(f'{bank} - Rating Distribution')
            axes[i].set_xlabel('Rating')
            axes[i].set_ylabel('Count')
            axes[i].set_xticks(range(1, 6))
        
        plt.tight_layout()
        plt.savefig('reports/rating_distribution.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        print("✓ Rating distribution saved")
    
    def plot_sentiment_analysis(self):
        """Plot sentiment analysis results"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Sentiment by bank
        sentiment_by_bank = pd.crosstab(self.df['bank'], self.df['sentiment_label'])
        sentiment_by_bank.plot(kind='bar', ax=ax1, color=['red', 'gray', 'green'])
        ax1.set_title('Sentiment Distribution by Bank')
        ax1.set_ylabel('Number of Reviews')
        ax1.legend(title='Sentiment')
        ax1.tick_params(axis='x', rotation=45)
        
        # Average sentiment score by bank
        avg_sentiment = self.df.groupby('bank')['sentiment_score'].mean()
        avg_sentiment.plot(kind='bar', ax=ax2, color='lightcoral')
        ax2.set_title('Average Sentiment Score by Bank')
        ax2.set_ylabel('Average Sentiment Score')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('reports/sentiment_analysis.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        print("✓ Sentiment analysis saved")
    
    def plot_theme_analysis(self):
        """Plot theme distribution"""
        plt.figure(figsize=(12, 6))
        
        theme_by_bank = pd.crosstab(self.df['bank'], self.df['theme'])
        theme_by_bank.plot(kind='bar', stacked=True)
        plt.title('Theme Distribution by Bank')
        plt.ylabel('Number of Reviews')
        plt.xlabel('Bank')
        plt.legend(title='Themes', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig('reports/theme_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Theme analysis saved")
    
    def create_wordclouds(self):
        """Create word clouds for each bank"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # Check if 'cleaned_text' column exists
        if 'cleaned_text' not in self.df.columns:
            print("⚠️ Skipping word cloud generation: 'cleaned_text' column not found.")
            plt.close(fig)
            return

        for i, bank in enumerate(self.df['bank'].unique()):
            bank_data = self.df[self.df['bank'] == bank]
            text = ' '.join(bank_data['cleaned_text'].astype(str))
            
            wordcloud = WordCloud(
                width=400, 
                height=300, 
                background_color='white',
                max_words=50
            ).generate(text)
            
            axes[i].imshow(wordcloud, interpolation='bilinear')
            axes[i].set_title(f'{bank} - Common Words')
            axes[i].axis('off')
        
        plt.tight_layout()
        plt.savefig('reports/wordclouds.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
        print("✓ Word clouds saved")
    
    def plot_rating_comparison(self):
        """Plot overall rating comparison"""
        plt.figure(figsize=(10, 6))
        
        rating_comparison = self.df.groupby('bank')['rating'].mean().sort_values(ascending=False)
        colors = ['green' if x > 3 else 'orange' if x > 2 else 'red' for x in rating_comparison.values]
        
        bars = plt.bar(rating_comparison.index, rating_comparison.values, color=colors, alpha=0.7)
        plt.title('Average Rating Comparison Across Banks')
        plt.ylabel('Average Rating (1-5)')
        plt.xticks(rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('reports/rating_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Rating comparison saved")
    
    def plot_sentiment_trends(self):
        """Plot sentiment trends over time if date data is available"""
        if 'date' not in self.df.columns:
            print("⚠️ Skipping sentiment trends: 'date' column not found.")
            return
            
        try:
            # Convert date and aggregate by month
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df['month'] = self.df['date'].dt.to_period('M')
            
            monthly_sentiment = self.df.groupby(['month', 'bank'])['sentiment_score'].mean().unstack()
            
            plt.figure(figsize=(12, 6))
            for bank in monthly_sentiment.columns:
                plt.plot(monthly_sentiment.index.astype(str), monthly_sentiment[bank], marker='o', label=bank)
            
            plt.title('Monthly Average Sentiment Trends by Bank')
            plt.ylabel('Average Sentiment Score')
            plt.xlabel('Month')
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('reports/sentiment_trends.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ Sentiment trends saved")
        except Exception as e:
            print(f"⚠️ Could not create sentiment trends: {e}")
    
    def generate_all_visualizations(self):
        """Generate all visualizations"""
        print("Generating visualizations...")
        
        # Ensure the output directory exists
        self._ensure_report_directory('reports')
        
        # Generate all plots
        self.plot_rating_distribution()
        self.plot_sentiment_analysis()
        self.plot_theme_analysis()
        self.create_wordclouds()
        self.plot_rating_comparison()
        self.plot_sentiment_trends()
        
        print("✅ All visualizations saved to reports/ folder!")

if __name__ == "__main__":
    # Load final data - use correct path for standalone execution
    try:
        df = pd.read_csv('data/final_analyzed_reviews.csv')
    except FileNotFoundError:
        print("Error: Could not find 'data/final_analyzed_reviews.csv'. Ensure the main pipeline was run successfully.")
        exit()
    
    # Generate visualizations
    visualizer = ReviewVisualizer(df)
    visualizer.generate_all_visualizations()
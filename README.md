# 📱 Fintech App Reviews Analytics

> Advanced customer experience analysis for Ethiopian mobile banking applications using NLP and data engineering

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12%2B-blue)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Completed-success)]()

## 📊 Project Overview

This project analyzes Google Play Store reviews for three major Ethiopian banking applications to identify customer satisfaction drivers, pain points, and provide data-driven recommendations for mobile banking improvements.

### 🏦 Banks Analyzed
- **Commercial Bank of Ethiopia (CBE)** - Market leader with 5M+ installs
- **Bank of Abyssinia (BOA)** - Growing digital banking presence
- **Dashen Bank** - Technology-focused modern banking

### 🎯 Business Objectives
- Identify key drivers of customer satisfaction and dissatisfaction
- Provide actionable insights for product improvement
- Enable competitive benchmarking across banking apps
- Support strategic roadmap development for digital banking
## 📁 Project Structure

```text
fintech-reviews-analysis/
│
├── data/ # Data files
│   ├── raw_reviews.csv # Raw scraped data
│   ├── cleaned_reviews.csv # Preprocessed data
│   ├── analyzed_reviews.csv # Sentiment analysis results
│   └── final_analyzed_reviews.csv # Complete analysis
│
├── scripts/ # Analysis scripts
│   ├── scraper.py # Google Play Store data collection
│   ├── preprocessor.py # Data cleaning and preprocessing
│   ├── sentiment_analyzer.py # NLP sentiment analysis (DistilBERT)
│   ├── thematic_analyzer.py # Thematic analysis and categorization
│   ├── database_handler.py # PostgreSQL database operations
│   └── visualizer.py # Data visualization generation
│
├── reports/ # Generated outputs
│   ├── *.png # Analysis visualizations
│   └── *.docx # Professional reports
│
├── database/ # Database schema and setup
│   └── schema.sql # PostgreSQL database schema
│
├── tests/ # Unit tests
│   └── test_sentiment.py # Test cases for sentiment analysis
│
├── main.py # Main pipeline orchestrator
├── create_interim_report.py # Interim report generator
├── create_final_report.py # Final report generator
├── requirements.txt # Python dependencies
├── .gitignore # Git ignore rules
├── LICENSE # MIT License
└── README.md # This documentation

```
## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Git

### Installation
 # **Clone the repository**
 ```
git clone https://github.com/DE143/fintech-reviews-analysis.git
cd fintech-reviews-analysis
```
```
Create virtual environment
python -m venv venv
```
```
 Windows:
venv\Scripts\activate
```
```
 Mac/Linux:
source venv/bin/activate
```
```
 Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```
```
 Setup PostgreSQL

 Create database
createdb bank_reviews
```
```
 Set environment variable
export DB_PASSWORD=your_password
Windows: set DB_PASSWORD=your_password
```
Run Complete Pipeline
```
python main.py
```
 Run Individual Components

 Data collection
 ```
python scripts/scraper.py
```
 Preprocessing
 ```
python scripts/preprocessor.py
```
 Sentiment analysis
 ```
python scripts/sentiment_analyzer.py
```
 Thematic analysis
 ```
python scripts/thematic_analyzer.py
```
 Database integration
 ```
python scripts/database_handler.py
```
 Visualization generation
 ```
python scripts/visualizer.py
```
 Report generation
 ```
python create_interim_report.py
```
```
python create_final_report.py
```
## 🚀 Database Schema
```
-- Banks table
CREATE TABLE banks (
    bank_id SERIAL PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL,
    app_name VARCHAR(100) NOT NULL
);
```
```
-- Reviews table
CREATE TABLE reviews (
    review_id VARCHAR(100) PRIMARY KEY,
    bank_id INTEGER REFERENCES banks(bank_id),
    review_text TEXT,
    cleaned_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_date DATE,
    sentiment_label VARCHAR(20),
    sentiment_score FLOAT,
    theme VARCHAR(50),
    keywords TEXT,
    source VARCHAR(50)
);
```
## Key Technologies

- **Web Scraping:**  
  `google-play-scraper` library for collecting Google Play Store reviews.

- **Data Processing:**  
  `pandas`, `numpy` for data cleaning, transformation, and analysis.

- **NLP / Sentiment Analysis:**  
  Hugging Face **Transformers** (DistilBERT) for high-accuracy sentiment classification.

- **Thematic Analysis:**  
  `spaCy` and `scikit-learn` (TF-IDF, clustering) for topic extraction and categorization.

- **Database:**  
  **PostgreSQL** with `psycopg2` for structured data storage and querying.

- **Visualization:**  
  `matplotlib`, `seaborn`, and `wordcloud` for analytical charts and insights.

- **Reporting:**  
  `python-docx` for generating professional **interim** and **final** reports.

## 📊 Analysis Results

### 🔍 Key Findings

- **Performance Variations:**  
  Dashen Bank leads with an average rating of **4.04/5.0**, compared to **CBE (2.70)** and **BOA (2.11)**.

- **Sentiment Analysis:**  
  Dashen Bank shows **68.2% positive sentiment**, significantly higher than competitors (~19%).

- **Primary Pain Points:**  
  Performance issues, functionality limitations, and UX challenges.

- **Satisfaction Drivers:**  
  Transaction speed, security features, and intuitive interface design.

---

### 📄 Sample Analysis Output

| Bank                          | Average Rating | Positive Sentiment | Top Theme       |
|------------------------------|----------------|----------------------|-----------------|
| **Dashen Bank**               | 4.04/5.0       | 68.2%               | User Experience |
| **Commercial Bank of Ethiopia** | 2.70/5.0     | 19.8%               | Functionality   |
| **Bank of Abyssinia**        | 2.11/5.0       | 18.4%               | Performance     |

---

### 📊 Visualizations Generated

- Rating distribution by bank  
- Sentiment analysis comparison  
- Thematic analysis charts  
- Word clouds for each bank  
- Performance benchmarking  
- Trend analysis over time  

---

## 📈 Business Impact

### 🎯 Expected Outcomes

- **20–30%** reduction in negative reviews within 6 months  
- **15–25%** improvement in app store ratings  
- Improved customer retention & satisfaction  
- More informed, **data-driven product development**  

### 🧭 Strategic Recommendations

- **Immediate (0–3 months):**  
  Performance optimization, error handling improvements  
- **Short-term (3–6 months):**  
  UX redesign, feature enhancements  
- **Long-term (6–12 months):**  
  AI-powered features, advanced security improvements  

---

## 📋 Project Deliverables

### ✅ Completed

- **Data Pipeline:** End-to-end automated pipeline  
- **Sentiment Analysis:** DistilBERT transformer applied  
- **Database Integration:** PostgreSQL with structured schema  
- **Visualizations:** Full suite of analytical plots  
- **Reports:** Interim and final professional reports  
- **Documentation:** Full technical documentation  

---

## 📄 Reports Generated

- **Customer_Experience_Analytics_Interim_Report.docx**  
  *4-page progress report*

- **Customer_Experience_Analytics_Final_Report.docx**  
  *10-page comprehensive analysis*

##  🔍 Sample Code Usage
from scripts.scraper import scrape_play_store_reviews
from scripts.sentiment_analyzer import SentimentAnalyzer
from scripts.database_handler import DatabaseHandler

# Collect data
reviews_df = scrape_play_store_reviews()

# Analyze sentiment
analyzer = SentimentAnalyzer()
analyzed_df = analyzer.analyze_reviews(reviews_df)

# Store in database
db = DatabaseHandler()
db.create_tables()
db.insert_data(analyzed_df)

# Query results
results = db.execute_query("""
    SELECT bank_name, AVG(rating) as avg_rating 
    FROM reviews 
    JOIN banks ON reviews.bank_id = banks.bank_id 
    GROUP BY bank_name
""")

## 📝 Methodology

### 📥 Data Collection

- **Source:** Google Play Store official reviews  
- **Sample Size:** 1,500+ reviews (500 per bank)  
- **Period:** Recent user submissions  
- **Quality:** No duplicates, fully cleaned and processed  

---

### 🔬 Analysis Techniques

- **Sentiment Analysis:**  
  `distilbert-base-uncased-finetuned-sst-2-english` transformer model  

- **Thematic Analysis:**  
  TF-IDF keyword extraction + manual clustering for theme discovery  

- **Statistical Analysis:**  
  Rating distributions, frequency analysis, sentiment correlations  

- **Comparative Analysis:**  
  Cross-bank benchmarking of ratings, sentiments, and themes  

---

## 📄 License

This project is licensed under the **MIT License** — see the `LICENSE` file for details.

---

## 🙏 Acknowledgments

- Google Play Scraper library by **JoMingyu**  
- **Hugging Face** for transformer-based NLP models  
- **PostgreSQL** community for robust database tools  
- **10 Academy** for project structure, guidance, and mentorship  

---

## 📞 Contact

**Project Maintainer:** Derese Ewunet 
**Email:** derese641735.ew@gmail.com.com  
**GitHub:** [@DE143](https://github.com/DE143)  

---

## 📊 Project Status

| Component            | Status        | Notes                        |
|----------------------|---------------|------------------------------|
| Data Collection      | ✅ Complete   | 1,500+ reviews collected     |
| Preprocessing        | ✅ Complete   | Clean, structured dataset    |
| Sentiment Analysis   | ✅ Complete   | DistilBERT implementation    |
| Thematic Analysis    | ✅ Complete   | TF-IDF theme extraction      |
| Database Integration | ✅ Complete   | PostgreSQL operational       |
| Visualization        | ✅ Complete   | Full set of charts           |
| Reports              | ✅ Complete   | Interim + final reports      |
| Testing              | ✅ Complete   | Unit tests implemented       |

---

<div align="center">

⭐ **If you found this project useful, please consider giving it a star on GitHub!** ⭐

<img src="https://api.star-history.com/svg?repos=DE143/fintech-reviews-analysis&type=Timeline" width="600">

</div>

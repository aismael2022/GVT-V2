# 🚀 GVT-V2: Google Trends TV Personality Scraper

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aismael2022/GVT-V2/blob/main/GVT-V2_Colab.ipynb)

A powerful scraper that extracts trending TV personalities from Google Trends and analyzes their search popularity using NLP.

## 📌 Features

- **Trend Extraction**: Scrapes real-time trending names from Google Trends TV
- **Person Verification**: Uses spaCy NLP to filter only real people
- **Search Analytics**: Enriches data with Google Search result counts
- **Auto-Saving**: Exports to timestamped Excel files
- **Multi-Language Support**: Detects name languages automatically

## 🛠 Installation

### Prerequisites
- Python 3.8+
- Google Chrome browser
- Stable internet connection

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/aismael2022/GVT-V2.git
cd GVT-V2

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg

## 🏃‍♂️ Usage
python V4_test.py

## 🚀 Expected Output
🌐 Loading Google Trends TV...
🔄 Processing...
🔍 Found 25 trending names
📊 Analyzing search popularity...
✅ Saved to google_trends_tv_results_09_06_2024_03-45PM.xlsx
⏱️ Total runtime: 45.72s

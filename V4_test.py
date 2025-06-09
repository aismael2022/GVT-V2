import os
import re
import sys
import time
import random
import datetime
import warnings
import pyfiglet
import pandas as pd
import numpy as np
from functools import lru_cache
from langdetect import detect
import spacy
from spacy.language import Language
import subprocess
from datetime import datetime
from transformers.pipelines import pipeline
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, Any, Union, Optional
from spacy.language import Language


# Suppress unnecessary warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# --------- Model Loading with Cache --------- #
#@lru_cache(maxsize=None)
# Type alias for clarity (if using transformers)
if 'Optional' not in dir():
    Optional = Union[Any, None]  # Fallback definition

# For transformer models (replace with actual type if needed)
TransformerModel = Any

def load_models() -> Dict[str, Union[Language, TransformerModel, None]]:
    """Cache-loaded NLP models with proper typing support."""
    models: Dict[str, Union[Language, TransformerModel, None]] = {
        'spacy': None,
        'transformer': None
    }
    
    models['spacy'] = load_spacy_model()
    return models

def load_spacy_model() -> Union[Language, None]:
    """Load spaCy model with fallback logic."""
    model_names = ['en_core_web_lg', 'en_core_web_sm']
    ascii_art = pyfiglet.figlet_format("NOVA ClIP", font="standard")
    print(ascii_art)
    for model_name in model_names:
        try:
            print(f"🔄 Loading {model_name}...")
            return spacy.load(model_name)
        except OSError:
            print(f"⚠️ Downloading {model_name}...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model_name],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return spacy.load(model_name)
            except Exception as e:
                print(f"⚠️ Download failed: {e}")
                continue
    
    print("❌ All model load attempts failed")
    return None

# Runtime loading
models = load_models()
nlp = models['spacy']  # type: Union[Language, None]
ner_pipeline = models['transformer']  # type: Union[Any, None]

# --------- Core Text Processing --------- #
def clean_name(name: str) -> str:
    """Enhanced name cleaner with Unicode support"""
    if not name:
        return ""
        
    # Preserve letters, spaces, apostrophes, and Unicode chars
    name = re.sub(r"[^\w\s'\u00C0-\u017F]", "", str(name), flags=re.UNICODE)
    # Remove lonely apostrophes but keep valid ones (O'Connor)
    name = re.sub(r"(?<!\w)'(?!\w)", "", name)
    # Normalize and trim
    return re.sub(r"\s+", " ", name).strip()

def is_person(text: str) -> bool:
    """Multi-layered person detection with safe model access"""
    text = clean_name(text)
    if not text or len(text) < 2 or text.isdigit():
        return False

    # Exclusion patterns
    non_person_terms = {
        'tv', 'show', 'movie', 'film', 'series', 'season',
        'song', 'music', 'award', 'channel', 'network',
        'episode', 'live', 'stream', 'premiere', 'finale'
    }
    
    text_lower = text.lower()
    if any(term in text_lower for term in non_person_terms):
        return False

    # SpaCy NER (with null check)
    if nlp is not None:  # Explicit check before calling
        try:
            doc = nlp(text)
            if any(ent.label_ in ("PER", "PERSON") for ent in doc.ents):
                return True
        except Exception as e:
            print(f"⚠️ SpaCy error: {e}")
    else:
        print("⚠️ SpaCy model not available")

    # Transformer NER (existing null check is fine)
    if ner_pipeline:
        try:
            entities = ner_pipeline(text) or []
            for ent in entities:
                if getattr(ent, "entity_group", None) == "PER" or \
                   (isinstance(ent, dict) and ent.get("entity_group") == "PER"):
                    return True
        except Exception as e:
            print(f"⚠️ Transformer error: {e}")

    # Western name pattern
    if (re.fullmatch(r'([A-Z][a-z]+)(?:\s+[A-Z][a-z]+){0,3}', text) and
        not any(w.lower() in {'the', 'and', 'of'} for w in text.split())):
        return True

    # Initial-based names
    if re.fullmatch(r'([A-Z]\.\s*)+[A-Z][a-z]+', text):
        return True

    return False

# --------- Scraping Functions --------- #
def configure_driver() -> webdriver.Chrome:
    """Configure Chrome WebDriver with stealth options"""
    options = Options()
    options.add_argument("--window-size=900,300")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

def scrape_trends(driver: webdriver.Chrome, timeout: int = 30, max_names: int = 25) -> set:
    """Core scraping logic with improved element detection"""
    names = set()
    start = time.time()
    
    while (time.time() - start) < timeout and len(names) < max_names:
        try:
            items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.NJfIwe a.vcW2ic[jsname='thYVgf']")
                )
            )
            names.update(clean_name(item.text) for item in items if item.text)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"⚠️ Scraping iteration error: {e}")
            break
            
    return names

def extract_search_result_with_tools_click(url: str) -> str:
    """Extracts search results count from Google search with Tools click"""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1000,400")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        print(f"🌐 Opening: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        # Click Tools button
        tools_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[text()='Tools' or text()='الأدوات']")
            )
        )
        tools_button.click()
        time.sleep(random.uniform(2, 4))

        # Get result stats
        result_stats = wait.until(
            EC.presence_of_element_located((By.ID, "result-stats"))
        )
        raw_text = result_stats.text
        
        # Extract number with regex
        match = re.search(r'About ([\d,]+)', raw_text)
        if match:
            return match.group(1).replace(",", "")
        return "0"
        
    except Exception as e:
        print(f"⚠️ Search error on {url}: {str(e)[:100]}...")  # Truncate long error messages
        return "N/A"
    finally:
        if driver:
            driver.quit()

def stage_one_extract_and_save() -> str:
    """Main scraping function with better error handling"""
    driver = None
    try:
        driver = configure_driver()
        driver.get("https://trends.google.com/tv/?geo=US&rows=5&cols=5")
        print("🔄 Processing...")
        
        names = scrape_trends(driver)
        if not names:
            print("❌ No names collected")
            return ""

        # Process and save data
        data = []
        for name in names:
            try:
                lang = detect(name) if len(name) > 3 else "und"
                data.append({
                    "Name": name,
                    #"Language": lang,
                    "Is Person": is_person(name),
                    "Link": f"https://www.google.com/search?q={'+'.join(name.split())}&hl=en&gl=us"
                })
            except Exception as e:
                print(f"⚠️ Name processing error: {e}")

        df = pd.DataFrame(data)
        #filename = f"google_trends_tv_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%d_%m_%Y_%I-%M%p")
        filename = os.path.join(script_dir, f"google_trends_tv_results_{timestamp}.xlsx")
        df.to_excel(filename, index=False)
        return filename

    except Exception as e:
        print(f"❌ Fatal scraping error: {e}")
        return ""
    finally:
        if driver:
            driver.quit()

# --------- Search Enrichment --------- #
def stage_two_enrich_search_results(filename: str) -> None:
    """Enhanced search enrichment with better error handling"""
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return

    try:
        df = pd.read_excel(filename)
        
        # Initialize Search Results column if needed
        if "Search Results" not in df.columns:
            df["Search Results"] = np.nan

        total = len(df)
        for count, (idx, row) in enumerate(df.iterrows(), 1):
            # Skip already processed rows
            if pd.notna(row["Search Results"]) and row["Search Results"] not in ["", "N/A"]:
                print(f"✅ Row {count}/{total}: Already processed")
                continue

            print(f"\n🔍 Processing {count}/{total}: {row['Name']}")
            
            # Skip non-person entries
            if not row['Is Person']:
                df.at[idx, "Search Results"] = "Not a person - skipped"
                df.to_excel(filename, index=False)
                continue
                
            # Process search results
            result = extract_search_result_with_tools_click(str(row['Link']))
            df.at[idx, "Search Results"] = result
            df.to_excel(filename, index=False)
            
            # Random delay between requests
            sleep_time = random.randint(5, 15)
            print(f"⏳ Sleeping {sleep_time} seconds...")
            time.sleep(sleep_time)

        print("\n✅ Enrichment complete!")
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        
# --------- Main Execution --------- #
if __name__ == "__main__":
    print("🌐 Loading Google Trends TV...")
    start_time = time.time()
    
    try:
        results_file = stage_one_extract_and_save()
        if results_file:
            print(f"\n🔄 Getting Google Search Results...")
            time.sleep(10)
            stage_two_enrich_search_results(results_file)
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical failure: {e}")
    finally:
        print(f"\n⏱️ Total runtime: {time.time()-start_time:.2f}s")

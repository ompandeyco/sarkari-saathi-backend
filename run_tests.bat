@echo off
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
python pipeline/scrape_schemes.py
python pipeline/embed_and_store.py
python test_api.py

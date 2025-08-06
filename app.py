# app.py

import os
from flask import Flask, render_template, request, redirect, url_for
from scraper import SnkrdunkScraper # 從 scraper.py 匯入我們的類別
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    """渲染首頁"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """處理搜尋請求，執行爬蟲並顯示結果"""
    card_name = request.form.get('card_name')
    if not card_name:
        return redirect(url_for('index'))

    # 從環境變數讀取帳號密碼
    user_email = os.getenv('SNKRDUNK_EMAIL')
    user_password = os.getenv('SNKRDUNK_PASSWORD')

    if not user_email or not user_password:
        return "錯誤：請在 .env 檔案中設定 SNKRDUNK_EMAIL 和 SNKRDUNK_PASSWORD", 500

    scraper = None
    scraped_data = []
    try:
        # 建立爬蟲實例並執行
        # 注意：我們呼叫的函式完全一樣，但 scraper.login() 現在變得更智慧了
        scraper = SnkrdunkScraper(user_email, user_password)
        if scraper.login():
            scraped_data = scraper.search_and_scrape(card_name, max_results=10)
    except Exception as e:
        print(f"Flask 路由處理中發生嚴重錯誤: {e}")
    finally:
        # 無論成功或失敗，都確保瀏覽器被關閉
        if scraper:
            scraper.close()
            
    # 將抓取到的資料傳給 results.html 樣板進行渲染
    return render_template('results.html', results=scraped_data, query=card_name)

if __name__ == '__main__':
    # 啟動 Flask 伺服器
    app.run(debug=True, host='0.0.0.0', port=5001)
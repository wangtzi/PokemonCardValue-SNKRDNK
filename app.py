import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g
from scraper import SnkrdunkScraper
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- 新增的資料庫設定 ---
# 資料庫檔案會被儲存在 /data/history.db
# /data 將是我們從 OpenShift 掛載進來的持久化儲存目錄
DATABASE_PATH = '/data/history.db'

def get_db():
    """開啟一個新的資料庫連線，如果目前請求中還沒有的話"""
    db = getattr(g, '_database', None)
    if db is None:
        # 確保 /data 這個目錄存在
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row # 讓查詢結果可以像字典一樣用欄位名存取
    return db

@app.teardown_appcontext
def close_connection(exception):
    """在請求結束時自動關閉資料庫連線"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """初始化資料庫，建立表格"""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        print("✅ 資料庫表格已成功初始化。")

# --- 修改後的路由 ---

@app.route('/')
def index():
    """渲染首頁，並顯示最新的 10 筆搜尋紀錄"""
    db = get_db()
    cur = db.execute('SELECT term, timestamp FROM history ORDER BY timestamp DESC LIMIT 10')
    history = cur.fetchall()
    return render_template('index.html', history=history)

@app.route('/search', methods=['POST'])
def search():
    """處理搜尋請求，執行爬蟲，儲存紀錄並顯示結果"""
    card_name = request.form.get('card_name')
    if not card_name:
        return redirect(url_for('index'))

    # --- 新增：儲存搜尋紀錄到資料庫 ---
    try:
        db = get_db()
        db.execute('INSERT INTO history (term) VALUES (?)', (card_name,))
        db.commit()
        print(f"📝 已將搜尋詞 '{card_name}' 存入資料庫。")
    except Exception as e:
        print(f"❌ 存儲搜尋紀錄時發生錯誤: {e}")
    # --- 結束新增 ---

    user_email = os.getenv('SNKRDUNK_EMAIL')
    user_password = os.getenv('SNKRDUNK_PASSWORD')

    if not user_email or not user_password:
        return "錯誤：請在 .env 檔案中設定 SNKRDUNK_EMAIL 和 SNKRDUNK_PASSWORD", 500

    scraper = None
    scraped_data = []
    try:
        scraper = SnkrdunkScraper(user_email, user_password)
        if scraper.login():
            scraped_data = scraper.search_and_scrape(card_name, max_results=10)
    except Exception as e:
        print(f"Flask 路由處理中發生嚴重錯誤: {e}")
    finally:
        if scraper:
            scraper.close()
            
    return render_template('results.html', results=scraped_data, query=card_name)

# --- 應用程式啟動時初始化資料庫 ---
# schema.sql 檔案
try:
    init_db()
except sqlite3.OperationalError:
    print("資料庫表格已存在，跳過初始化。")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

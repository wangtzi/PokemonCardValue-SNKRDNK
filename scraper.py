# scraper.py

import time
import pickle  # <<< NEW: 匯入 pickle 模組，用來序列化儲存 cookies
import os      # <<< NEW: 匯入 os 模組，用來檢查檔案是否存在
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SnkrdunkScraper:
    # <<< MODIFIED: 在初始化時，可以指定 cookie 檔案的路徑
    def __init__(self, username, password, cookie_path="cookies.pkl"):
        self.base_url = "https://snkrdunk.com/en"
        self.username = username
        self.password = password
        self.cookie_path = cookie_path  # <<< NEW
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        print("✅ 瀏覽器驅動已成功啟動 (無頭模式)。")

    # <<< NEW: 儲存 cookies 的新函式
    def save_cookies(self):
        """將當前的 cookies 儲存到檔案"""
        try:
            with open(self.cookie_path, 'wb') as file:
                pickle.dump(self.driver.get_cookies(), file)
            print(f"✅ Cookies 已成功儲存至 {self.cookie_path}")
        except Exception as e:
            print(f"❌ 儲存 Cookies 時發生錯誤: {e}")

    # <<< NEW: 載入 cookies 的新函式
    def load_cookies(self):
        """從檔案載入 cookies"""
        if not os.path.exists(self.cookie_path):
            print(" bilgilendirme: Cookie 檔案不存在，將執行完整登入。")
            return False
            
        try:
            with open(self.cookie_path, 'rb') as file:
                cookies = pickle.load(file)
                # 必須先訪問一次網站的網域，才能設定 cookie
                self.driver.get(self.base_url)
                for cookie in cookies:
                    # 有些 cookie 屬性 webdriver 不接受，要移除以避免錯誤
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    self.driver.add_cookie(cookie)
            print("✅ Cookies 已成功載入。")
            return True
        except Exception as e:
            print(f"❌ 載入 Cookies 失敗: {e}，將執行完整登入。")
            return False

    # <<< NEW: 檢查是否處於登入狀態的新函式
    def is_logged_in(self):
        """檢查目前是否為登入狀態"""
        print("🔍 正在檢查登入狀態...")
        self.driver.get(self.base_url)
        time.sleep(1) # 給頁面一點時間反應
        try:
            # 尋找登入後才會出現的帳戶連結
            self.driver.find_element(By.CSS_SELECTOR, "a[href='/en/account']")
            print("🔍 狀態檢查：已登入。")
            return True
        except:
            print("🔍 狀態檢查：未登入。")
            return False

    # <<< REWRITTEN: 全新重寫的智慧登入函式
    def login(self):
        """
        整合性的登入函式：先嘗試載入 cookie，若無效再執行完整登入。
        """
        # 1. 嘗試載入 cookies
        if self.load_cookies():
            # 2. 驗證 cookie 是否有效 (是否真的登入了)
            if self.is_logged_in():
                return True # Cookie 有效，登入成功！
        
        # 3. 如果 cookie 無效或不存在，執行完整的表單登入
        print("--- Cookie 無效或不存在，執行完整表單登入流程 ---")
        login_url = f"{self.base_url}/login?slide=right"
        self.driver.get(login_url)
        try:
            email_field = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
            email_field.send_keys(self.username)
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button.button-rc-bk[type='submit']")
            login_button.click()
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/en/account']")))
            print("🎉 完整登入成功！")
            
            # 4. 登入成功後，儲存新的 cookies 以供下次使用
            self.save_cookies()
            return True
        except Exception as e:
            print(f"❌ 完整登入失敗: {e}")
            self.driver.save_screenshot("login_error.png")
            return False

    def search_and_scrape(self, card_name, max_results=10):
        # 這個函式維持原樣，不需要變動
        print(f"\n--- 開始搜尋卡片: {card_name} ---")
        try:
            self.driver.get(self.base_url)
            print("✅ 已導航至首頁。")

            print("⏳ 正在等待並點擊搜尋 ICON...")
            search_icon_selector = "a[href='/en/search']"
            search_icon = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, search_icon_selector)))
            search_icon.click()
            print("✅ 已點擊搜尋 ICON。")
            
            print("⏳ 正在尋找搜尋框...")
            search_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "search-field")))
            search_input.send_keys(card_name)
            search_input.send_keys(Keys.RETURN)
            print(f"✅ 已在搜尋框輸入 '{card_name}' 並送出。")
            
            print("⏳ 正在等待並點擊 'TCG' 標籤頁...")
            tcg_tab_xpath = "//div[contains(text(), 'Streetwear & TCG')]"
            tcg_tab = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, tcg_tab_xpath)))
            tcg_tab.click()
            print("✅ 已點擊 'TCG' 標籤頁。")

            print("⏳ 正在等待搜尋結果載入 (等待第一張卡片出現)...")
            product_item_selector = "li.product__item"
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, product_item_selector)))
            time.sleep(1) 
            print("✅ 搜尋結果已載入。")
            
            card_elements = self.driver.find_elements(By.CSS_SELECTOR, product_item_selector)
            if not card_elements:
                print("⚠️ 找不到任何卡片項目。")
                return []

            print(f"🔍 找到 {len(card_elements)} 個結果，將為您解析前 {max_results} 個。")
            results = []
            for card in card_elements[:max_results]:
                try:
                    name = card.find_element(By.CLASS_NAME, "product__item-name").text
                    price = card.find_element(By.CLASS_NAME, "product__item-price").text
                    image_url = card.find_element(By.TAG_NAME, "img").get_attribute("src")
                    results.append({"name": name, "price": price, "image_url": image_url})
                except Exception:
                    continue
            return results

        except Exception as e:
            print(f"❌ 搜尋或抓取過程中發生錯誤: {e}")
            self.driver.save_screenshot("search_error.png")
            print(f"📷 錯誤截圖已儲存至 'search_error.png'。")
            return []

    def close(self):
        # 這個函式維持原樣，不需要變動
        if self.driver:
            self.driver.quit()
            print("\n✅ 瀏覽器驅動已關閉。")
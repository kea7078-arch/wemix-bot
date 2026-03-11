import requests
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# 설정
SLACK_URL = os.environ['SLACK_WEBHOOK_URL']
TARGET_LIKES = 50
BASE_URL = "https://wemix.com/ko/community"
DB_FILE = "last_counts.json"

def load_history():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 크롬 설정
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

try:
    driver.get(BASE_URL)
    time.sleep(7)
    
    # 30번 스크롤
    for _ in range(30):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    history = load_history()
    updated_posts = []
    current_results = {}

    # 카드 추출 및 분석
    post_elements = driver.find_elements(By.XPATH, "//div[contains(., 'Views')]")
    for post in post_elements:
        try:
            lines = [l.strip() for l in post.text.split('\n') if l.strip()]
            v_idx = next((i for i, s in enumerate(lines) if 'Views' in s), -1)
            if v_idx != -1:
                title = lines[v_idx - 3]
                likes = int(''.join(filter(str.isdigit, lines[v_idx + 1])))
                if likes >= TARGET_LIKES and not title.isdigit():
                    old_likes = history.get(title, 0)
                    if likes > old_likes:
                        status = "신규 발견" if old_likes == 0 else f"상승 ({old_likes} → {likes})"
                        updated_posts.append({"title": title, "likes": likes, "status": status})
                    current_results[title] = likes
        except: continue

    driver.quit()

    if updated_posts:
        for p in updated_posts:
            msg = {"text": f"📈 *[위믹스 변동]*\n*{p['status']}*\n👉 {p['title']}\n❤️ {p['likes']}개"}
            requests.post(SLACK_URL, json=msg)
        save_history(current_results)
except Exception as e:
    print(f"Error: {e}")

import requests
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 1. 설정
SLACK_URL = os.environ.get('SLACK_WEBHOOK_URL')
TARGET_LIKES = 50 
BASE_URL = "https://wemix.com/ko/community"
DB_FILE = "last_counts.json"

def load_history():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except: return {}
    return {}

def save_history(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 2. 브라우저 설정
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("🚀 실전 감시 모드 가동...")
    driver.get(BASE_URL)
    time.sleep(15)

    # 스크롤 35번으로 충분한 데이터 확보
    for i in range(35):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)

    history = load_history()
    updated_posts = []
    current_results = {}

    # 3. 데이터 및 링크 추출
    all_links = driver.find_elements(By.TAG_NAME, "a")
    link_map = {l.text.strip(): l.get_attribute('href') for l in all_links if l.text.strip()}

    body_text = driver.find_element(By.TAG_NAME, "body").text
    lines = [l.strip() for l in body_text.split('\n') if l.strip()]
    
    for i in range(len(lines)):
        if 'Views' in lines[i]:
            try:
                title = lines[i-3]
                likes = int(''.join(filter(str.isdigit, lines[i+1])))
                
                if likes >= TARGET_LIKES and not title.isdigit():
                    old_likes = history.get(title, 0)
                    
                    if likes > old_likes:
                        status = "🆕 신규 발견" if old_likes == 0 else f"📈 상승 ({old_likes}→{likes})"
                        
                        # 제목 매칭 링크 찾기
                        post_link = link_map.get(title, BASE_URL)
                        if post_link == BASE_URL:
                            for k, v in link_map.items():
                                if title in k or k in title:
                                    post_link = v
                                    break
                        
                        updated_posts.append({
                            "title": title, "likes": likes, "status": status, "link": post_link
                        })
                    current_results[title] = likes
            except: continue

    driver.quit()

    # 4. 슬랙 전송
    if updated_posts:
        print(f"✅ {len(updated_posts)}건의 소식 전송 중...")
        for p in updated_posts:
            msg = {
                "text": (
                    f"🔥 *[위믹스 핫글 알림]*\n"
                    f"*{p['status']}*\n"
                    f"👉 *제목:* {p['title']}\n"
                    f"❤️ *좋아요:* {p['likes']}개\n"
                    f"🔗 *바로가기:* <{p['link']}|클릭해서 게시글 보기>"
                )
            }
            requests.post(SLACK_URL, json=msg)
            time.sleep(0.5)
        save_history(current_results)
    else:
        print("📭 아직 새로운 핫글이 없습니다.")

except Exception as e:
    print(f"❌ 에러: {e}")
    if 'driver' in locals(): driver.quit()

import requests
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 1. 설정 (테스트를 위해 기준을 5개로 낮춤)
SLACK_URL = os.environ.get('SLACK_WEBHOOK_URL')
TARGET_LIKES = 5 # 테스트를 위해 5개로 낮췄습니다. 50으로 다시 바꾸지 마세요!
BASE_URL = "https://wemix.com/ko/community"
DB_FILE = "last_counts.json"

def load_history():
    return {} # 무조건 빈 수첩을 반환해서 모든 글을 '신규'로 인식하게 함

# 2. 브라우저 설정
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print(f"🔗 {BASE_URL} 접속 중...")
    driver.get(BASE_URL)
    time.sleep(20) # 로딩 시간을 20초로 더 늘림

    # 스크롤 30번
    for i in range(30):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

    updated_posts = []
    
    # 3. 데이터 추출 및 로그 기록
    body_text = driver.find_element(By.TAG_NAME, "body").text
    lines = [l.strip() for l in body_text.split('\n') if l.strip()]
    
    print(f"📊 탐색된 전체 문장 수: {len(lines)}")
    print("--- [수색 시작] ---")

    for i in range(len(lines)):
        if 'Views' in lines[i]:
            try:
                # 봇이 무엇을 찾았는지 로그에 무조건 찍습니다.
                raw_title = lines[i-3]
                raw_likes = int(''.join(filter(str.isdigit, lines[i+1])))
                print(f"👀 발견: 제목({raw_title[:15]}...) / 좋아요({raw_likes})")
                
                if raw_likes >= TARGET_LIKES and not raw_title.isdigit():
                    updated_posts.append({"title": raw_title, "likes": raw_likes, "status": "📢 테스트 발송"})
            except: continue

    driver.quit()

    # 4. 슬랙 전송 결과 확인
    if updated_posts:
        print(f"🎯 알림 대상 {len(updated_posts)}건 발견! 슬랙으로 쏩니다.")
        for p in updated_posts:
            msg = {"text": f"🧪 *[테스트 알림]*\n👉 {p['title']}\n❤️ {p['likes']}개"}
            res = requests.post(SLACK_URL, json=msg)
            print(f"📤 전송 결과: {res.status_code} (200이면 성공)")
    else:
        print("❌ 5개 넘는 좋아요 게시글도 못 찾았습니다. 사이트 구조를 다시 확인해야 합니다.")

except Exception as e:
    print(f"❌ 에러: {e}")
    if 'driver' in locals(): driver.quit()

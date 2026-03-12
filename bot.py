import requests
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 1. 테스트 설정 (0개 이상이면 무조건 발송)
SLACK_URL = os.environ.get('SLACK_WEBHOOK_URL')
TARGET_LIKES = 0  # <--- 테스트를 위해 0으로 설정했습니다!
BASE_URL = "https://wemix.com/ko/community"
DB_FILE = "last_counts.json"

def load_history():
    return {} # 무조건 빈 수첩으로 시작 (모든 글 발송)

# 2. 브라우저 설정
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("🔗 슬랙 연결 테스트 시작...")
    driver.get(BASE_URL)
    time.sleep(10)

    body_text = driver.find_element(By.TAG_NAME, "body").text
    lines = [l.strip() for l in body_text.split('\n') if l.strip()]
    
    found_count = 0
    for i in range(len(lines)):
        if 'Views' in lines[i]:
            try:
                title = lines[i-3]
                likes = int(''.join(filter(str.isdigit, lines[i+1])))
                
                # 테스트: 발견하는 족족 슬랙 전송 (최대 3개만)
                if found_count < 3:
                    msg = {"text": f"✅ *[슬랙 연결 성공!]*\n👉 *제목:* {title}\n❤️ *좋아요:* {likes}개"}
                    res = requests.post(SLACK_URL, json=msg)
                    print(f"📤 전송 시도: {title[:10]}... 결과: {res.status_code}")
                    found_count += 1
            except: continue

    driver.quit()
    print(f"\n✨ 테스트 종료. 슬랙 채널을 확인해 보세요!")

except Exception as e:
    print(f"❌ 에러: {e}")
    if 'driver' in locals(): driver.quit()

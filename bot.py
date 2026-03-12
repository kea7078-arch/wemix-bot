import requests
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 1. 테스트 설정
SLACK_URL = os.environ.get('SLACK_WEBHOOK_URL')
BASE_URL = "https://wemix.com/ko/community"

# 2. 브라우저 설정
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("🔗 링크 추출 테스트 시작...")
    driver.get(BASE_URL)
    time.sleep(12)

    # 링크 수집
    all_links = driver.find_elements(By.TAG_NAME, "a")
    link_map = {l.text.strip(): l.get_attribute('href') for l in all_links if l.text.strip()}

    body_text = driver.find_element(By.TAG_NAME, "body").text
    lines = [l.strip() for l in body_text.split('\n') if l.strip()]
    
    count = 0
    for i in range(len(lines)):
        if 'Views' in lines[i] and count < 3: # 딱 3개만 테스트
            try:
                title = lines[i-3]
                likes = int(''.join(filter(str.isdigit, lines[i+1])))
                
                # 링크 찾기
                post_link = link_map.get(title, BASE_URL)
                if post_link == BASE_URL:
                    for k, v in link_map.items():
                        if title in k or k in title:
                            post_link = v
                            break

                msg = {
                    "text": f"🧪 *[링크 테스트]*\n👉 *제목:* {title}\n❤️ *좋아요:* {likes}개\n🔗 *바로가기:* <{post_link}|클릭해서 게시글 보기>"
                }
                res = requests.post(SLACK_URL, json=msg)
                print(f"📤 전송 시도: {title[:10]}... 결과: {res.status_code}")
                count += 1
            except: continue

    driver.quit()
    print("🏁 테스트 종료! 슬랙을 확인해 보세요.")

except Exception as e:
    print(f"❌ 에러: {e}")
    if 'driver' in locals(): driver.quit()

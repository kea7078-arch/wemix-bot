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
    """수첩 파일이 비어있거나 없어도 에러 없이 작동하게 합니다."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content: # 파일이 비어있으면
                    return {}
                return json.loads(content)
        except Exception as e:
            print(f"⚠️ 수첩 읽기 실패(새로 시작): {e}")
            return {}
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

print("🌐 브라우저 준비 중...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print(f"🔗 {BASE_URL} 접속 중...")
    driver.get(BASE_URL)
    time.sleep(15) # 로딩 대기

    # 스크롤 30번
    for i in range(30):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)

    history = load_history()
    updated_posts = []
    current_results = {}

    # 3. 데이터 추출 (가장 안전한 전체 텍스트 방식)
    body_text = driver.find_element(By.TAG_NAME, "body").text
    lines = [l.strip() for l in body_text.split('\n') if l.strip()]
    
    print(f"📊 탐색된 문장 수: {len(lines)}")

    for i in range(len(lines)):
        if 'Views' in lines[i]:
            try:
                # 위믹스 커뮤니티 구조에 맞춘 인덱스 추적
                title = lines[i-3]
                likes = int(''.join(filter(str.isdigit, lines[i+1])))
                
                if likes >= TARGET_LIKES and not title.isdigit():
                    old_likes = history.get(title, 0)
                    if likes > old_likes:
                        status = "🆕 신규" if old_likes == 0 else f"📈 상승 ({old_likes}→{likes})"
                        updated_posts.append({"title": title, "likes": likes, "status": status})
                    current_results[title] = likes
            except: continue

    driver.quit()

    # 4. 슬랙 전송
    if updated_posts:
        print(f"✅ {len(updated_posts)}건의 소식을 찾았습니다!")
        if not SLACK_URL:
            print("❌ 에러: 슬랙 주소(Secret)가 설정되지 않았습니다.")
        else:
            for p in updated_posts:
                msg = {"text": f"🚨 *[위믹스 감시]*\n*{p['status']}*\n👉 *{p['title']}*\n❤️ 좋아요: {p['likes']}개"}
                res = requests.post(SLACK_URL, json=msg)
                print(f"📤 슬랙 전송 결과: {res.status_code}")
        save_history(current_results)
    else:
        print("📭 변동 사항이 없어 알림을 보내지 않았습니다.")

except Exception as e:
    print(f"❌ 실행 중 오류: {e}")
    if 'driver' in locals(): driver.quit()

import pandas as pd
from playwright.sync_api import sync_playwright
import os
from tqdm import tqdm

# 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(CURRENT_DIR, '백엔드입력용_의원정보_정당정정본.csv')
OUTPUT_CSV = os.path.join(os.path.dirname(CURRENT_DIR), '백엔드입력용_의원정보통합_정당정정본.csv')

df = pd.read_csv(INPUT_CSV)
df['image_url'] = ''

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for i, row in tqdm(df.iterrows(), total=len(df), desc="의원 이미지 수집 중"):
        name = row['이름']
        try:
            url = f"https://open.assembly.go.kr/portal/assm/search/memberView.do?memName={name}"
            page.goto(url, timeout=15000)
            page.wait_for_selector("div.info-con.present img", timeout=5000)
            img_url = page.locator("div.info-con.present img").get_attribute("src")
            if img_url:
                if img_url.startswith('/'):
                    img_url = 'https://open.assembly.go.kr' + img_url
                df.at[i, 'image_url'] = img_url
        except Exception as e:
            print(f"❌ {name}: {e}")

    browser.close()

df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"✅ 완료! 저장 위치: {OUTPUT_CSV}")



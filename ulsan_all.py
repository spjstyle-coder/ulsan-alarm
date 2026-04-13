import os
import smtplib
import re
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
 
 
def make_driver():
    """실제 Chrome 브라우저처럼 동작하는 드라이버 생성"""
    options = Options()
    options.add_argument('--headless')           # 화면 없이 실행
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36')
    driver = webdriver.Chrome(options=options)
    return driver
 
 
def parse_date(raw_date_text):
    """다양한 날짜 형식 처리 (범위면 시작일만 추출)"""
    cleaned = re.sub(r'[^\d.\-]', ' ', raw_date_text.strip())
    cleaned = cleaned.split()[0].strip()
    cleaned = cleaned.replace('.', '-')
    cleaned = re.sub(r'-+', '-', cleaned).strip('-')
 
    for fmt, target in [('%Y-%m-%d', cleaned[:10]),
                        ('%y-%m-%d', cleaned[:8]),
                        ('%m-%d',    cleaned[:5])]:
        try:
            parsed = datetime.strptime(target, fmt)
            if fmt == '%m-%d':
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
    return None
 
 
def scrape_utp(driver):
    """울산테크노파크 지원사업공고"""
    url = "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401"
    try:
        driver.get(url)
        time.sleep(3)
 
        items = driver.find_elements(By.CSS_SELECTOR, "dl.info_list dt a")
        date_items = driver.find_elements(By.CSS_SELECTOR, "dl.info_list dd.date")
 
        print(f"\n[DEBUG] UTP 제목 개수: {len(items)}, 날짜 개수: {len(date_items)}")
        if date_items:
            print(f"[DEBUG] UTP 첫 번째 날짜: '{date_items[0].text.strip()}'")
 
        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        for i in range(min(len(items), len(date_items))):
            name = items[i].text.strip()
            raw_date = date_items[i].text.strip()
            post_date = parse_date(raw_date)
            if post_date and post_date >= one_week_ago:
                href = items[i].get_attribute('href') or url
                text += f"- [{post_date.strftime('%Y-%m-%d')}] {name}  링크: {href}\n"
 
        return text if text else "최근 일주일 내 신규 공고 없음\n"
    except Exception as e:
        return f"수집 중 오류 발생: {e}\n"
 
 
def scrape_uepa(driver):
    """울산경제일자리진흥원 지원사업"""
    url = "https://www.uepa.or.kr/sub/?mcode=0403010000"
    try:
        driver.get(url)
        time.sleep(3)
 
        items = driver.find_elements(By.CSS_SELECTOR, "strong.tit")
        date_items = driver.find_elements(By.CSS_SELECTOR, "ul.item_list li span")
 
        print(f"\n[DEBUG] UEPA 제목 개수: {len(items)}, 날짜 개수: {len(date_items)}")
        if date_items:
            print(f"[DEBUG] UEPA 첫 번째 날짜: '{date_items[0].text.strip()}'")
 
        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        for i in range(min(len(items), len(date_items))):
            name = items[i].text.strip()
            raw_date = date_items[i].text.strip()
            post_date = parse_date(raw_date)
            if post_date and post_date >= one_week_ago:
                try:
                    parent_a = items[i].find_element(By.XPATH, "./ancestor::a")
                    href = parent_a.get_attribute('href') or url
                except:
                    href = url
                text += f"- [{post_date.strftime('%Y-%m-%d')}] {name}  링크: {href}\n"
 
        return text if text else "최근 일주일 내 신규 공고 없음\n"
    except Exception as e:
        return f"수집 중 오류 발생: {e}\n"
 
 
def scrape_ccei(driver):
    """울산창조경제혁신센터 공지사항"""
    url = "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do"
    try:
        driver.get(url)
        time.sleep(3)
 
        items = driver.find_elements(By.CSS_SELECTOR, "ul#notice_list li a")
        date_items = driver.find_elements(By.CSS_SELECTOR, "ul#notice_list li span.date")
 
        print(f"\n[DEBUG] CCEI 제목 개수: {len(items)}, 날짜 개수: {len(date_items)}")
        if date_items:
            print(f"[DEBUG] CCEI 첫 번째 날짜: '{date_items[0].text.strip()}'")
 
        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        for i in range(min(len(items), len(date_items))):
            name = items[i].text.strip()
            raw_date = date_items[i].text.strip()
            post_date = parse_date(raw_date)
            if post_date and post_date >= one_week_ago:
                href = items[i].get_attribute('href') or url
                if href.startswith('/'):
                    href = "https://ccei.creativekorea.or.kr" + href
                text += f"- [{post_date.strftime('%Y-%m-%d')}] {name}  링크: {href}\n"
 
        return text if text else "최근 일주일 내 신규 공고 없음\n"
    except Exception as e:
        return f"수집 중 오류 발생: {e}\n"
 
 
# ----------------------------------------------------------------
# 메인 실행
# ----------------------------------------------------------------
print("브라우저 시작 중...")
driver = make_driver()
 
try:
    content = f"--- [최근 7일 기준] 울산 혁신기관 통합 알림 ({datetime.now().strftime('%Y-%m-%d')}) ---\n"
    content += "\n[울산테크노파크]\n" + scrape_utp(driver)
    content += "\n[울산경제일자리진흥원]\n" + scrape_uepa(driver)
    content += "\n[울산창조경제혁신센터]\n" + scrape_ccei(driver)
finally:
    driver.quit()
    print("브라우저 종료")
 
print("\n" + "=" * 50)
print("[최종 이메일 내용 미리보기]")
print(content)
print("=" * 50)
 
# HTML 본문
html_body_text = content.replace('\n', '<br>')
html_content = f"""
<html>
<body style="font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #004792; border-bottom: 2px solid #004792; padding-bottom: 10px;">
            🚀 오늘의 울산 기업지원 통합 알림
        </h2>
        <p style="font-size: 14px; color: #666;">안녕하세요, <b>MJ 기업성장연구소</b>입니다.<br>
        오늘({datetime.now().strftime('%Y-%m-%d')}) 업데이트된 소식을 전해드립니다.</p>
 
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-top: 15px;">
            {html_body_text}
        </div>
 
        <div style="margin-top: 30px; text-align: center;">
            <a href="https://www.utp.or.kr" style="background-color: #004792; color: white;
               padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                전체 공고 확인하기
            </a>
        </div>
 
        <footer style="margin-top: 40px; font-size: 12px; color: #999; text-align: center;
                border-top: 1px solid #eee; padding-top: 15px;">
            본 메일은 시스템에 의해 자동 발송되었습니다.<br>
            문의: onej@ulsan-uic.kr | MJ 기업성장연구소
        </footer>
    </div>
</body>
</html>
"""
 
naver_id = os.environ.get('NAVER_ID')
naver_pw = os.environ.get('NAVER_PW')
receive_email = "onej@ulsan-uic.kr"
 
msg = MIMEText(html_content, 'html')
msg['Subject'] = f"🚀 [울산 통합알림] 오늘의 신규 지원사업 ({datetime.now().strftime('%m/%d')})"
msg['From'] = f"{naver_id}@naver.com"
msg['To'] = receive_email
 
try:
    server = smtplib.SMTP_SSL('smtp.naver.com', 465)
    server.login(naver_id, naver_pw)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    print("HTML 메일 발송 성공!")
except Exception as e:
    print(f"발송 실패: {e}")

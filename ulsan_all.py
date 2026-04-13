import os
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time


def make_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(options=options)


def parse_date(raw):
    """2026-04-13 또는 2026.04.13 형식 처리"""
    cleaned = re.sub(r'[^\d]', '-', raw.strip())
    cleaned = re.sub(r'-+', '-', cleaned).strip('-')
    for fmt in ('%Y-%m-%d', '%y-%m-%d'):
        try:
            return datetime.strptime(cleaned[:10], fmt)
        except ValueError:
            continue
    return None


def scrape_utp(driver):
    """
    울산테크노파크
    구조: table > tr > td.subject a (제목) + td[3] (날짜, 2026-04-13 형식)
    """
    url = "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401"
    try:
        driver.get(url)
        time.sleep(3)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        count = 0

        for a in soup.select('td.subject a'):
            tr = a.find_parent('tr')
            if not tr:
                continue
            tds = tr.find_all('td')
            if len(tds) < 4:
                continue
            name = a.get_text().strip()
            raw_date = tds[3].get_text().strip()
            post_date = parse_date(raw_date)
            if post_date and post_date >= one_week_ago:
                href = a.get('href', '')
                # 상대경로 → 절대경로 변환
                if href.startswith('..'):
                    href = 'https://www.utp.or.kr/' + href.lstrip('./')
                elif href.startswith('/'):
                    href = 'https://www.utp.or.kr' + href
                text += f"- [{raw_date}] {name}\n  링크: {href}\n"
                count += 1

        print(f"[UTP] 최근 7일 공고 수: {count}")
        return text if text else "최근 일주일 내 신규 공고 없음\n"
    except Exception as e:
        return f"수집 중 오류: {e}\n"


def scrape_uepa(driver):
    """
    울산경제일자리진흥원
    구조: table > tr > td.tit a (제목, href=?mcode=...&no=XXX) + td.date (날짜, 2026-04-10 형식)
    """
    url = "https://www.uepa.or.kr/sub/?mcode=0403010000"
    try:
        driver.get(url)
        time.sleep(3)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        count = 0

        for td_date in soup.select('td.date'):
            raw_date = td_date.get_text().strip()
            post_date = parse_date(raw_date)
            if not post_date:
                continue
            tr = td_date.find_parent('tr')
            if not tr:
                continue
            td_tit = tr.find('td', class_='tit')
            if not td_tit:
                continue
            a = td_tit.find('a')
            if not a:
                continue
            name = a.get_text().strip()
            href = a.get('href', '')
            if href.startswith('?'):
                href = 'https://www.uepa.or.kr/sub/' + href
            elif href.startswith('/'):
                href = 'https://www.uepa.or.kr' + href

            if post_date >= one_week_ago:
                text += f"- [{raw_date}] {name}\n  링크: {href}\n"
                count += 1

        print(f"[UEPA] 최근 7일 공고 수: {count}")
        return text if text else "최근 일주일 내 신규 공고 없음\n"
    except Exception as e:
        return f"수집 중 오류: {e}\n"


def scrape_ccei(driver):
    """
    울산창조경제혁신센터
    구조: table.tbl1 > tr > td[2] a.tb_title (제목, onclick=fnDetailPage(no, ...))
                              + td[4] (날짜, 2026.04.13 형식)
    링크: /ulsan/custom/notice_view.do?no=XXX 로 구성
    """
    url = "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do"
    try:
        driver.get(url)
        time.sleep(3)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        table = soup.find('table', class_='tbl1')
        if not table:
            return "수집 중 오류: tbl1 테이블을 찾을 수 없음\n"

        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        count = 0

        for tr in table.find_all('tr')[1:]:  # 헤더(tr[0]) 제외
            tds = tr.find_all('td')
            if len(tds) < 5:
                continue

            # 제목: td[2] 안의 a 태그
            a = tds[2].find('a', class_='tb_title')
            if not a:
                continue
            # span(새글 표시 N) 제거 후 제목 추출
            for span in a.find_all('span'):
                span.decompose()
            name = a.get_text().strip()

            # 날짜: td[4]
            raw_date = tds[4].get_text().strip()
            post_date = parse_date(raw_date)
            if not post_date:
                continue

            # onclick에서 공고 번호 추출 → 링크 구성
            onclick = a.get('onclick', '')
            nums = re.findall(r'\d+', onclick)
            if nums:
                link = f"https://ccei.creativekorea.or.kr/ulsan/custom/notice_view.do?no={nums[0]}"
            else:
                link = url

            if post_date >= one_week_ago:
                text += f"- [{raw_date}] {name}\n  링크: {link}\n"
                count += 1

        print(f"[CCEI] 최근 7일 공고 수: {count}")
        return text if text else "최근 일주일 내 신규 공고 없음\n"
    except Exception as e:
        return f"수집 중 오류: {e}\n"


# ----------------------------------------------------------------
# 메인 실행
# ----------------------------------------------------------------
print("브라우저 시작...")
driver = make_driver()

try:
    content = f"--- [최근 7일 기준] 울산 혁신기관 통합 알림 ({datetime.now().strftime('%Y-%m-%d')}) ---\n"
    content += "\n[울산테크노파크]\n"      + scrape_utp(driver)
    content += "\n[울산경제일자리진흥원]\n" + scrape_uepa(driver)
    content += "\n[울산창조경제혁신센터]\n" + scrape_ccei(driver)
finally:
    driver.quit()
    print("브라우저 종료")

print("\n" + "="*50)
print("[최종 이메일 내용 미리보기]")
print(content)
print("="*50)

# HTML 본문
html_body_text = content.replace('\n', '<br>')
html_content = f"""
<html>
<body style="font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333;">
  <div style="max-width:600px; margin:0 auto; padding:20px;
              border:1px solid #ddd; border-radius:8px;">
    <h2 style="color:#004792; border-bottom:2px solid #004792; padding-bottom:10px;">
      🚀 오늘의 울산 기업지원 통합 알림
    </h2>
    <p style="font-size:14px; color:#666;">
      안녕하세요, <b>MJ 기업성장연구소</b>입니다.<br>
      오늘({datetime.now().strftime('%Y-%m-%d')}) 업데이트된 소식을 전해드립니다.
    </p>
    <div style="background:#f9f9f9; padding:15px; border-radius:5px; margin-top:15px;">
      {html_body_text}
    </div>
    <div style="margin-top:30px; text-align:center;">
      <a href="https://www.utp.or.kr"
         style="background:#004792; color:white; padding:10px 20px;
                text-decoration:none; border-radius:5px;">
        전체 공고 확인하기
      </a>
    </div>
    <footer style="margin-top:40px; font-size:12px; color:#999;
                   text-align:center; border-top:1px solid #eee; padding-top:15px;">
      본 메일은 시스템에 의해 자동 발송되었습니다.<br>
      문의: onej@ulsan-uic.kr | MJ 기업성장연구소
    </footer>
  </div>
</body>
</html>
"""

naver_id = os.environ.get('NAVER_ID')
naver_pw  = os.environ.get('NAVER_PW')
receive_email = "onej@ulsan-uic.kr"

msg = MIMEText(html_content, 'html')
msg['Subject'] = f"🚀 [울산 통합알림] 오늘의 신규 지원사업 ({datetime.now().strftime('%m/%d')})"
msg['From'] = f"{naver_id}@naver.com"
msg['To']   = receive_email

try:
    server = smtplib.SMTP_SSL('smtp.naver.com', 465)
    server.login(naver_id, naver_pw)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    print("메일 발송 성공!")
except Exception as e:
    print(f"발송 실패: {e}")

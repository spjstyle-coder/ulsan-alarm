import os
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
 
 
# ============================================================
# ★ 원하는 키워드를 여기에 추가/수정 하세요 ★
# 공고 제목에 아래 키워드 중 하나라도 포함되면 메일에 표시됩니다.
# 키워드가 비어있으면 모든 공고를 표시합니다.
# ============================================================
KEYWORDS = [
    "창업",
    "지원사업",
    "모집",
    "공모",
    "R&D",
    "바우처",
    "보조금",
    "연구",
    "스타트업",
    "기업지원",
    "재직자",
    "재직자 교육",
    ]

# ★ 제외할 키워드 - 여기 포함된 공고는 메일에서 빠집니다 ★
EXCLUDE_KEYWORDS = [
    "채용",
    "직원",
    "입찰",
    "결과",
    "평가",
]
 
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
    cleaned = re.sub(r'[^\d]', '-', raw.strip())
    cleaned = re.sub(r'-+', '-', cleaned).strip('-')
    for fmt in ('%Y-%m-%d', '%y-%m-%d'):
        try:
            return datetime.strptime(cleaned[:10], fmt)
        except ValueError:
            continue
    return None
 
 
def is_match(title):
    # 제외 키워드가 하나라도 포함되면 무조건 제외
    if any(kw in title for kw in EXCLUDE_KEYWORDS):
        return False
    # 포함 키워드 중 하나라도 있으면 통과
    if not KEYWORDS:
        return True
    return any(kw in title for kw in KEYWORDS)
 
 
def make_item(date_str, title, link):
    """공고 1건을 HTML 한 줄로 만들기 (제목이 링크)"""
    return (
        f'<tr>'
        f'<td style="padding:8px 12px; color:#888; white-space:nowrap; font-size:13px;">{date_str}</td>'
        f'<td style="padding:8px 12px;">'
        f'<a href="{link}" target="_blank" '
        f'style="color:#004792; text-decoration:none; font-size:14px;">{title}</a>'
        f'</td>'
        f'</tr>'
    )
 

def scrape_uic(driver):
    url = "https://www.ulsan-uic.kr/cop/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000091"
    try:
        driver.get(url)
        time.sleep(3)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
 
        one_week_ago = datetime.now() - timedelta(days=7)
        items = []
 
        for a in soup.select('td.subject a'):
            tr = a.find_parent('tr')
            tds = tr.find_all('td') if tr else []
            if len(tds) < 4:
                continue
            title = a.get_text().strip()
            raw_date = tds[3].get_text().strip()
            post_date = parse_date(raw_date)
            if not post_date or post_date < one_week_ago:
                continue
            if not is_match(title):
                continue
            href = a.get('href', '')
            if href.startswith('..'):
                href = 'https://www.ulsan-uic.kr/' + href.lstrip('./')
            elif href.startswith('/'):
                href = 'https://www.ulsan-uic.kr' + href
            items.append(make_item(raw_date, title, href))
 
        print(f"[UIC] 매칭 공고 수: {len(items)}")
        return items
    except Exception as e:
        print(f"[UIC] 오류: {e}")
        return []


def scrape_utp(driver):
    url = "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401"
    try:
        driver.get(url)
        time.sleep(3)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
 
        one_week_ago = datetime.now() - timedelta(days=7)
        items = []
 
        for a in soup.select('td.subject a'):
            tr = a.find_parent('tr')
            tds = tr.find_all('td') if tr else []
            if len(tds) < 4:
                continue
            title = a.get_text().strip()
            raw_date = tds[3].get_text().strip()
            post_date = parse_date(raw_date)
            if not post_date or post_date < one_week_ago:
                continue
            if not is_match(title):
                continue
            href = a.get('href', '')
            if href.startswith('..'):
                href = 'https://www.utp.or.kr/' + href.lstrip('./')
            elif href.startswith('/'):
                href = 'https://www.utp.or.kr' + href
            items.append(make_item(raw_date, title, href))
 
        print(f"[UTP] 매칭 공고 수: {len(items)}")
        return items
    except Exception as e:
        print(f"[UTP] 오류: {e}")
        return []
 
 
def scrape_uepa(driver):
    url = "https://www.uepa.or.kr/sub/?mcode=0403010000"
    try:
        driver.get(url)
        time.sleep(3)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
 
        one_week_ago = datetime.now() - timedelta(days=7)
        items = []
 
        for td_date in soup.select('td.date'):
            raw_date = td_date.get_text().strip()
            post_date = parse_date(raw_date)
            if not post_date or post_date < one_week_ago:
                continue
            tr = td_date.find_parent('tr')
            td_tit = tr.find('td', class_='tit') if tr else None
            a = td_tit.find('a') if td_tit else None
            if not a:
                continue
            title = a.get_text().strip()
            if not is_match(title):
                continue
            href = a.get('href', '')
            if href.startswith('?'):
                href = 'https://www.uepa.or.kr/sub/' + href
            elif href.startswith('/'):
                href = 'https://www.uepa.or.kr' + href
            items.append(make_item(raw_date, title, href))
 
        print(f"[UEPA] 매칭 공고 수: {len(items)}")
        return items
    except Exception as e:
        print(f"[UEPA] 오류: {e}")
        return []
 
 
def scrape_ccei(driver):
    url = "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do"
    try:
        driver.get(url)
        time.sleep(3)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
 
        table = soup.find('table', class_='tbl1')
        if not table:
            return []
 
        one_week_ago = datetime.now() - timedelta(days=7)
        items = []
 
        for tr in table.find_all('tr')[1:]:
            tds = tr.find_all('td')
            if len(tds) < 5:
                continue
            a = tds[2].find('a', class_='tb_title')
            if not a:
                continue
            for span in a.find_all('span'):
                span.decompose()
            title = a.get_text().strip()
            raw_date = tds[4].get_text().strip()
            post_date = parse_date(raw_date)
            if not post_date or post_date < one_week_ago:
                continue
            if not is_match(title):
                continue
            onclick = a.get('onclick', '')
            nums = re.findall(r'\d+', onclick)
            link = (f"https://ccei.creativekorea.or.kr/ulsan/custom/notice_view.do?no={nums[0]}"
                    if nums else url)
            items.append(make_item(raw_date, title, link))
 
        print(f"[CCEI] 매칭 공고 수: {len(items)}")
        return items
    except Exception as e:
        print(f"[CCEI] 오류: {e}")
        return []
 
def scrape_uipa(driver):
    from bs4 import BeautifulSoup
    url = "https://uipa.or.kr/webuser/notice/list.html"
    try:
        driver.get(url)
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ===== 진단 출력 =====
        tables = soup.find_all("table")
        print(f"[UIPA 진단] table 개수: {len(tables)}")
        for i, t in enumerate(tables[:2]):
            rows = t.find_all("tr")
            print(f"[UIPA 진단] table[{i}] tr 개수: {len(rows)}")
            for tr in rows[:3]:
                tds = tr.find_all("td")
                ths = tr.find_all("th")
                print(f"  th수:{len(ths)} td수:{len(tds)}")
                for j, td in enumerate(tds):
                    a = td.find("a")
                    cls = str(td.get("class", ""))
                    txt = td.get_text().strip()[:30]
                    has_a = (a is not None)
                    print("    td[" + str(j) + "] class=" + cls + ": " + repr(txt) + " a=" + str(has_a))
        import re
        date_pat = re.compile(r"202[0-9][.\-]\d{2}[.\-]\d{2}")
        print(f"\n[UIPA 진단] 날짜 패턴 포함 태그:")
        for tag in soup.find_all(string=date_pat)[:5]:
            p = tag.parent
            print(f"  <{p.name} class={p.get("class")}> '{tag.strip()}'")
        # =====================

        one_week_ago = datetime.now() - timedelta(days=7)
        items = []
        for tr in soup.select("table tr"):
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            a = None
            for td in tds:
                a_tag = td.find("a", href=True)
                if a_tag:
                    a = a_tag
                    break
            if not a:
                continue
            for tag in a.find_all(["img", "span"]):
                tag.decompose()
            title = a.get_text().strip()
            if not title:
                continue
            raw_date = tds[-1].get_text().strip()
            post_date = parse_date(raw_date)
            if not post_date or post_date < one_week_ago:
                continue
            if not is_match(title):
                continue
            href = a.get("href", "")
            link = ("https://uipa.or.kr" + href) if href.startswith("/") else href or url
            items.append(make_item(raw_date, title, link))

        print(f"[UIPA] 매칭 공고 수: {len(items)}")
        return items
    except Exception as e:
        print(f"[UIPA] 오류: {e}")
        return []

def make_section_html(site_name, items, site_url):
    """사이트별 섹션 HTML 생성"""
    if items:
        rows = '\n'.join(items)
        table_html = f'''
        <table style="width:100%; border-collapse:collapse;">
          <thead>
            <tr style="background:#f0f4fa;">
              <th style="padding:8px 12px; text-align:left; font-size:12px; color:#555; font-weight:bold; white-space:nowrap; border-bottom:2px solid #004792;">공고일자</th>
              <th style="padding:8px 12px; text-align:left; font-size:12px; color:#555; font-weight:bold; border-bottom:2px solid #004792;">공고명</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>'''
    else:
        table_html = '<p style="color:#999; font-size:13px; padding:8px 12px;">최근 7일 내 해당 키워드 공고 없음</p>'
 
    return f'''
    <div style="margin-bottom:24px;">
      <div style="background:#004792; color:white; padding:8px 14px;
                  border-radius:6px 6px 0 0; font-size:14px; font-weight:bold;">
        <a href="{site_url}" target="_blank"
           style="color:white; text-decoration:none;">🔗 {site_name}</a>
      </div>
      <div style="border:1px solid #ddd; border-top:none; border-radius:0 0 6px 6px;">
        {table_html}
      </div>
    </div>'''
 
 
# ----------------------------------------------------------------
# 메인 실행
# 키워드 명 넣고 싶을 때 330 줄에 이부분을 넣으면 됨 : 키워드 <b style="color:#004792;">[ {keyword_str} ]</b> 관련
# ----------------------------------------------------------------
print("브라우저 시작...")
driver = make_driver()
 
try:
    uic_items  = scrape_uic(driver)
    utp_items  = scrape_utp(driver)
    uepa_items = scrape_uepa(driver)
    ccei_items = scrape_ccei(driver)
    uipa_items = scrape_uipa(driver)
finally:
    driver.quit()
    print("브라우저 종료")
 
total = len(uic_items) + len(utp_items) + len(uepa_items) + len(ccei_items) + len(uipa_items)
today = datetime.now().strftime('%Y-%m-%d')
keyword_str = ', '.join(KEYWORDS) if KEYWORDS else '전체'
 
print(f"\n총 매칭 공고: {total}개 (키워드: {keyword_str})")
 
# 섹션별 HTML
uic_html  = make_section_html("울산산학융합원",
    uic_items, "https://www.ulsan-uic.kr/cop/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000091")
utp_html  = make_section_html("울산테크노파크",
    utp_items, "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401")
uepa_html = make_section_html("울산경제일자리진흥원",
    uepa_items, "https://www.uepa.or.kr/sub/?mcode=0403010000")
ccei_html = make_section_html("울산창조경제혁신센터",
    ccei_items, "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do")
uipa_html = make_section_html("울산정보산업진흥원",
    uipa_items, "https://uipa.or.kr/webuser/notice/list.html")
 
html_content = f"""
<html>
<body style="font-family:'Malgun Gothic',sans-serif; line-height:1.6; color:#333; background:#f4f6f8;">
  <div style="max-width:640px; margin:0 auto; padding:24px;">
 
    <div style="background:white; border-radius:10px; padding:24px;
                box-shadow:0 2px 8px rgba(0,0,0,0.08);">
 
      <h2 style="color:#004792; border-bottom:2px solid #004792;
                 padding-bottom:10px; margin-top:0;">
        🚀 오늘의 울산 혁신기관 기업지원사업 통합 알림
      </h2>
 
      <p style="font-size:14px; color:#555;">
        안녕하세요. <b style="color:#006400;"> 울산산학융합원 장원석 팀장</b>입니다.<br>
        <b>{today}</b> 기준 최근 7일 신규 공고 중 기업지원 관련 키워드로 검색된
                <b style="color:#e44;">{total}건</b>의 정보를 안내드립니다.
        <br>
      </p>

      <h2 style="color:#004792; border-bottom:2px solid #004792;
                 padding-bottom:10px; margin-top:0;">
      </h2>

      
      {utp_html}
      {uepa_html}
      {ccei_html}
      {uipa_html}
 
      <p style="font-size:12px; color:#aaa; text-align:center; margin-top:24px;">
        본 메일은 울산산학융합원의 사업에 직간접적으로 참여한 기업 담당자에게 시스템에 의해 자동 발송됩니다.<br>
        수신을 원치 않으시면 아래의 메일로 수신거부 메일을 주시면 명단에서 제외하겠습니다.<br>
        문의: onej@ulsan-uic.kr | 울산산학융합원 장원석 팀장(support billy, bhin)
      </p>
    </div>
 
  </div>
</body>
</html>
"""
 
naver_id = os.environ.get('NAVER_ID')
naver_pw  = os.environ.get('NAVER_PW')
# ★ 수신자 목록 - 추가/삭제 여기서만 하세요 ★
receive_emails = [
    "onej@ulsan-uic.kr",
    #"doyun900@ulsan-uic.kr",
    #"uic.jang@gmail.com",
    #"bhin@ulsan-uic.kr", 
]
try:
    server = smtplib.SMTP_SSL('smtp.naver.com', 465)
    server.login(naver_id, naver_pw)
 
    for email in receive_emails:
        msg = MIMEText(html_content, 'html')
        msg['Subject'] = f"🚀 [울산 통합알림] 울산 혁신기관 기업지원사업 통합 알림 {total}건 ({today})"
        msg['From'] = f"{naver_id}@naver.com"
        msg['To'] = email
        server.sendmail(msg['From'], email, msg.as_string())
        print(f"발송 완료: {email}")
 
    server.quit()
    print("전체 메일 발송 성공!")
except Exception as e:
    print(f"발송 실패: {e}")

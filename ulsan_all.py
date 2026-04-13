import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import re
from datetime import datetime, timedelta


def parse_date(raw_date_text):
    """다양한 날짜 형식을 처리합니다."""
    cleaned = re.sub(r'[^\d.\-]', ' ', raw_date_text.strip())
    # 날짜 범위(예: 2026.04.07 ~ 2026.04.17)에서 시작일만 추출
    cleaned = cleaned.split()[0].strip()
    cleaned = cleaned.replace('.', '-')
    cleaned = re.sub(r'-+', '-', cleaned).strip('-')

    formats_to_try = [
        ('%Y-%m-%d', cleaned[:10]),
        ('%y-%m-%d', cleaned[:8]),
        ('%m-%d',    cleaned[:5]),
    ]
    for fmt, target in formats_to_try:
        try:
            parsed = datetime.strptime(target, fmt)
            if fmt == '%m-%d':
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
    return None


def get_data(url, selector, date_selector, base_view_url=None):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')

        items = soup.select(selector)
        date_items = soup.select(date_selector)

        print(f"\n[DEBUG] URL: {url}")
        print(f"[DEBUG] 제목 개수: {len(items)}, 날짜 개수: {len(date_items)}")
        if date_items:
            print(f"[DEBUG] 첫 번째 날짜 원본값: '{date_items[0].get_text().strip()}'")
        else:
            print(f"[DEBUG] ⚠️  날짜 셀렉터({date_selector})로 아무것도 못 찾음!")
        if not items:
            print(f"[DEBUG] ⚠️  제목 셀렉터({selector})로 아무것도 못 찾음!")

        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        found_count = 0
        loop_range = min(len(items), len(date_items))

        for i in range(loop_range):
            name = items[i].get_text().strip()
            raw_date = date_items[i].get_text().strip()
            post_date = parse_date(raw_date)

            if post_date is None:
                print(f"[DEBUG] 날짜 파싱 실패: '{raw_date}' (항목: {name[:20]})")
                continue

            if post_date >= one_week_ago:
                raw_href = items[i].get('href', '') or items[i].get('onclick', '')
                data_id = re.findall(r'\d+', raw_href)

                link = url
                if data_id and base_view_url:
                    link = base_view_url + data_id[-1]

                text += f"- [{post_date.strftime('%Y-%m-%d')}] {name}  링크: {link}\n"
                found_count += 1

        print(f"[DEBUG] 최근 7일 이내 공고 수: {found_count}")
        return text if text else "최근 일주일 내 신규 공고 없음\n"

    except Exception as e:
        return f"수집 중 오류 발생: {e}\n"


def get_uepa_data():
    """
    울산경제일자리진흥원은 메인 슬라이드 방식이라
    지원사업 목록 페이지를 직접 스크래핑합니다.
    """
    url = "https://www.uepa.or.kr/sub/?mcode=0403010000"
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 제목: strong.tit
        items = soup.select('strong.tit')
        # 날짜: ul.item_list 안의 span (기간 정보)
        date_items = soup.select('ul.item_list li span')

        print(f"\n[DEBUG] UEPA URL: {url}")
        print(f"[DEBUG] 제목 개수: {len(items)}, 날짜 span 개수: {len(date_items)}")
        if date_items:
            print(f"[DEBUG] 첫 번째 날짜 원본값: '{date_items[0].get_text().strip()}'")
        else:
            print(f"[DEBUG] ⚠️  날짜 셀렉터로 아무것도 못 찾음!")

        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        found_count = 0

        for i in range(min(len(items), len(date_items))):
            name = items[i].get_text().strip()
            raw_date = date_items[i].get_text().strip()
            post_date = parse_date(raw_date)

            if post_date is None:
                print(f"[DEBUG] 날짜 파싱 실패: '{raw_date}' ({name[:20]})")
                continue

            if post_date >= one_week_ago:
                parent_a = items[i].find_parent('a')
                href = parent_a.get('href', '') if parent_a else ''
                if href.startswith('/'):
                    link = "https://www.uepa.or.kr" + href
                else:
                    link = href or url
                text += f"- [{post_date.strftime('%Y-%m-%d')}] {name}  링크: {link}\n"
                found_count += 1

        print(f"[DEBUG] 최근 7일 이내 공고 수: {found_count}")
        return text if text else "최근 일주일 내 신규 공고 없음\n"

    except Exception as e:
        return f"수집 중 오류 발생: {e}\n"


# ----------------------------------------------------------------
# 정보 취합
# ----------------------------------------------------------------
content = f"--- [최근 7일 기준] 울산 혁신기관 통합 알림 ({datetime.now().strftime('%Y-%m-%d')}) ---\n"

# 1. 울산테크노파크
# 스크린샷 확인: 제목 = dl.info_list dt a / 날짜 = dl.info_list dd.date
content += "\n[울산테크노파크]\n"
content += get_data(
    "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401",
    "dl.info_list dt a",
    "dl.info_list dd.date",
    "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401&wr_id="
)

# 2. 울산경제일자리진흥원
# 메인은 슬라이드 방식 → 목록 페이지 직접 사용
content += "\n[울산경제일자리진흥원]\n"
content += get_uepa_data()

# 3. 울산창조경제혁신센터
# 스크린샷 확인: 제목 = ul#notice_list li a / 날짜 = ul#notice_list li span.date
content += "\n[울산창조경제혁신센터]\n"
content += get_data(
    "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do",
    "ul#notice_list li a",
    "ul#notice_list li span.date",
    "https://ccei.creativekorea.or.kr/ulsan/custom/notice_view.do?no="
)

# 디버그 출력
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
            <a href="https://www.utp.or.kr" style="background-color: #004792; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                전체 공고 확인하기
            </a>
        </div>

        <footer style="margin-top: 40px; font-size: 12px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 15px;">
            본 메일은 시스템에 의해 자동 발송되었습니다.<br>
            문의: onej@ulsan-uic.kr | MJ 기업성장연구소
        </footer>
    </div>
</body>
</html>
"""

# 메일 발송
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

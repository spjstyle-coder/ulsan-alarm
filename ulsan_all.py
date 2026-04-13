import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import re
from datetime import datetime, timedelta
 
# ============================================================
# [수정1] 날짜 파싱 함수를 별도로 분리
#         여러 날짜 형식을 하나씩 시도해서 성공하면 반환
# ============================================================
def parse_date(raw_date_text):
    """
    다양한 날짜 형식을 처리합니다.
    예: '2026.04.10', '26.04.10', '2026-04-10', '04-10' 등
    """
    # 숫자, 점, 하이픈 외 문자 제거 (괄호, 공백 등)
    cleaned = re.sub(r'[^\d.\-]', '', raw_date_text.strip())
 
    # 점을 하이픈으로 통일
    cleaned = cleaned.replace('.', '-')
 
    # 연속된 하이픈 제거
    cleaned = re.sub(r'-+', '-', cleaned).strip('-')
 
    # 시도할 날짜 형식 목록
    formats_to_try = [
        ('%Y-%m-%d', cleaned[:10]),   # 2026-04-10
        ('%y-%m-%d', cleaned[:8]),    # 26-04-10
        ('%m-%d',    cleaned[:5]),    # 04-10 (연도 없는 경우)
    ]
 
    for fmt, target in formats_to_try:
        try:
            parsed = datetime.strptime(target, fmt)
            # 연도가 없는 경우 현재 연도로 보완
            if fmt == '%m-%d':
                parsed = parsed.replace(year=datetime.now().year)
            return parsed
        except ValueError:
            continue
 
    return None  # 모든 형식 실패
 
# ============================================================
# [수정2] get_data 함수에 디버그 출력 추가
#         셀렉터가 맞는지 / 날짜가 어떻게 오는지 확인 가능
# ============================================================
def get_data(url, selector, date_selector, base_view_url=None):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
 
        items = soup.select(selector)
        date_items = soup.select(date_selector)
 
        # [디버그] 셀렉터가 제대로 작동하는지 확인
        print(f"\n[DEBUG] URL: {url}")
        print(f"[DEBUG] 제목 개수: {len(items)}, 날짜 개수: {len(date_items)}")
        if date_items:
            print(f"[DEBUG] 첫 번째 날짜 원본값: '{date_items[0].get_text().strip()}'")
        else:
            print(f"[DEBUG] ⚠️  날짜 셀렉터({date_selector})로 아무것도 못 찾음!")
        if not items:
            print(f"[DEBUG] ⚠️  제목 셀렉터({selector})로 아무것도 못 찾음!")
 
        # 오늘 기준 7일 전 날짜
        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        found_count = 0
 
        # 데이터 개수가 맞지 않는 경우 대비해 최소 개수 기준으로 반복
        loop_range = min(len(items), len(date_items))
 
        for i in range(loop_range):
            name = items[i].get_text().strip()
            raw_date = date_items[i].get_text().strip()
 
            # [수정3] 개선된 날짜 파싱 함수 사용
            post_date = parse_date(raw_date)
 
            if post_date is None:
                # [디버그] 어떤 날짜가 파싱 실패하는지 확인
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
 
 
# --- 정보 취합 ---
content = f"--- [최근 7일 기준] 울산 혁신기관 통합 알림 ({datetime.now().strftime('%Y-%m-%d')}) ---\n"
 
# 1. 울산테크노파크
content += "\n[울산테크노파크]\n"
content += get_data(
    "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401",
    "td.subject a",
    "td.date",
    "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401&wr_id="
)
 
# 2. 울산경제일자리진흥원
content += "\n[울산경제일자리진흥원]\n"
content += get_data(
    "https://www.uepa.or.kr/board/boardList.do?boardId=NOTICE",
    "td.left a",
    "td:nth-last-child(2)",
    "https://www.uepa.or.kr/board/boardView.do?boardId=NOTICE&dataId="
)
 
# 3. 울산창조경제혁신센터
content += "\n[울산창조경제혁신센터]\n"
content += get_data(
    "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do",
    "td.al a",
    "td.date",
    "https://ccei.creativekorea.or.kr/ulsan/custom/notice_view.do?no="
)
 
# [디버그] 터미널에서 결과 확인 (GitHub Actions 로그에서도 보임)
print("\n" + "="*50)
print("[최종 이메일 내용 미리보기]")
print(content)
print("="*50)
 
# 1. 줄바꿈(\n)을 HTML 줄바꿈(<br>)으로 변환
html_body_text = content.replace('\n', '<br>')
 
# 2. HTML 형식의 본문
html_content = f"""
<html>
<body style="font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #004792; border-bottom: 2px solid #004792; padding-bottom: 10px;">
            🚀 오늘의 울산 기업지원 통합 알림
        </h2>
        <p style="font-size: 14px; color: #666;">안녕하세요, <b>UL 기업성장연구소</b>입니다.<br>
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
            문의: withnansang | UL 기업성장연구소
        </footer>
    </div>
</body>
</html>
"""
 
# 네이버 계정 정보 (GitHub Secrets에서 가져옴)
naver_id = os.environ.get('NAVER_ID')
naver_pw = os.environ.get('NAVER_PW')
receive_email = "onej@ulsan-uic.kr"
 
# 3. 메일 설정
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

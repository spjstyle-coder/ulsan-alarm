import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import re
from datetime import datetime, timedelta

def get_data(url, selector, date_selector, base_view_url=None):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        items = soup.select(selector)
        date_items = soup.select(date_selector)
        
        # 오늘 기준 7일 전 날짜 계산
        one_week_ago = datetime.now() - timedelta(days=7)
        text = ""
        found_count = 0
        
        # 데이터 개수가 맞지 않을 경우를 대비해 최소 개수 기준으로 반복
        loop_range = min(len(items), len(date_items))
        
        for i in range(loop_range):
            name = items[i].get_text().strip()
            raw_date = date_items[i].get_text().strip()
            
            # 날짜 정제: 점(.)을 대시(-)로 바꾸고 숫자/대시만 남김
            date_cleaned = re.sub(r'[^0-9\-]', '-', raw_date.replace('.', '-'))
            # 연속된 대시 정리 (예: -- -> -)
            date_cleaned = re.sub(r'-+', '-', date_cleaned).strip('-')
            
            try:
                # 날짜 형식이 '2026-04-09' 형태인지 확인하여 변환
                post_date = datetime.strptime(date_cleaned[:10], '%Y-%m-%d')
                
                if post_date >= one_week_ago:
                    raw_href = items[i].get('href', '') or items[i].get('onclick', '')
                    data_id = re.findall(r'\d+', raw_href)
                    
                    link = url
                    if data_id and base_view_url:
                        # UTP나 진흥원 등 각 기관 규칙에 따라 마지막 숫자 사용
                        link = base_view_url + data_id[-1]
                    
                    text += f"- [{date_cleaned[:10]}] {name}\n  링크: {link}\n"
                    found_count += 1
            except:
                continue
                
        return text if text else "최근 일주일 내 신규 공고 없음\n"
    except Exception as e:
        return f"수집 중 오류 발생: {e}\n"

# --- 정보 취합 ---
content = f"--- [최근 7일 기준] 울산 혁신기관 통합 알림 ({datetime.now().strftime('%Y-%m-%d')}) ---\n\n"

# 1. 울산테크노파크 (경로 재수정)
content += "[울산테크노파크]\n"
content += get_data(
    "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401",
    "td.subject a", 
    "td.date", # UTP는 날짜 칸에 date 클래스가 있는 경우가 많음
    "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401&wr_id="
)

# 2. 울산경제일자리진흥원
content += "\n[울산경제일자리진흥원]\n"
content += get_data(
    "https://www.uepa.or.kr/board/boardList.do?boardId=NOTICE",
    "td.left a",
    "td:nth-last-child(2)", # 등록일 칸 위치
    "https://www.uepa.or.kr/board/boardView.do?boardId=NOTICE&dataId="
)

# 3. 울산창조경제혁신센터 (이미지 분석 기반 수정)
content += "\n[울산창조경제혁신센터]\n"
content += get_data(
    "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do",
    "td.al a", # 제목 칸
    "td.date", # 또는 td:nth-last-child(2)
    "https://ccei.creativekorea.or.kr/ulsan/custom/notice_view.do?no="
)

print(content) # 이 결과가 터미널에 제목과 함께 잘 나오는지 확인이 최우선입니다!

# --- 메일 발송 로직 (기존과 동일) ---
# ... (생략) ...

print(content)

# --- 메일 발송 ---
naver_id = os.environ.get('NAVER_ID')
naver_pw = os.environ.get('NAVER_PW') # 반드시 애플리케이션 비밀번호 사용
receive_email = "onej@ulsan-uic.kr"

msg = MIMEText(content)
msg['Subject'] = f"[최근7일] 울산 주요기관 지원사업 알림 ({datetime.now().strftime('%m/%d')})"
msg['From'] = f"{naver_id}@naver.com"
msg['To'] = receive_email

try:
    server = smtplib.SMTP_SSL('smtp.naver.com', 465)
    server.login(naver_id, naver_pw)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    print("통합 메일 발송 성공!")
except Exception as e:
    print(f"발송 실패: {e}")

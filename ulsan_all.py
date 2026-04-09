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

# 1. 줄바꿈(\n)을 미리 HTML용 줄바꿈(<br>)으로 바꿔둡니다. (에러 방지 핵심!)
html_body_text = content.replace('\n', '<br>')

# 2. HTML 형식의 본문 만들기 (f-string 내부에 백슬래시가 없도록 수정)
html_content = f"""
<html>
<body style="font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
        <h2 style="color: #004792; border-bottom: 2px solid #004792; padding-bottom: 10px;">
            🚀 오늘의 울산 기업지원 통합 알림
        </h2>
        <p style="font-size: 14px; color: #666;">안녕하세요, <b>MJ 기업성장연구소</b>입니다.<br>
        오늘({datetime.now().strftime('%Y-%m-%d')}) 업데이트된 소식을 전해드립니다.</p>
        
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 5px solid #004792;">
            {html_body_text}
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
            <a href="https://www.utp.or.kr" style="background-color: #004792; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                전체 공고 확인하기
            </a>
        </div>
        
        <footer style="margin-top: 40px; font-size: 12px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
            본 메일은 시스템에 의해 자동 발송되었습니다.<br>
            문의: onej@ulsan-uic.kr | MJ 기업성장연구소
        </footer>
    </div>
</body>
</html>
"""

# 네이버 계정 정보 (GitHub Secrets에서 가져옴)
naver_id = os.environ.get('NAVER_ID')
naver_pw = os.environ.get('NAVER_PW')
receive_email = "onej@ulsan-uic.kr"

# 3. 메일 설정 (MIMEText 형식을 'html'로 설정)
msg = MIMEText(html_content, 'html')
msg['Subject'] = f"🔔 [울산 통합알림] 오늘의 신규 지원사업 ({datetime.now().strftime('%m/%d')})"
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

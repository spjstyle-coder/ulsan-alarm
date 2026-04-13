"""
이 파일을 GitHub에 올리고 Actions에서 실행하면
각 사이트의 실제 HTML을 로그에 출력해줍니다.
"""
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
    driver = webdriver.Chrome(options=options)
    return driver

driver = make_driver()

sites = [
    ("울산테크노파크", "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401"),
    ("울산경제일자리진흥원", "https://www.uepa.or.kr/sub/?mcode=0403010000"),
    ("울산창조경제혁신센터", "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do"),
]

for name, url in sites:
    print(f"\n{'='*60}")
    print(f"[{name}] URL: {url}")
    driver.get(url)
    time.sleep(4)
    html = driver.page_source
    print(f"HTML 길이: {len(html)}")
    print("--- HTML 앞부분 ---")
    print(html[:3000])
    print("--- HTML 끝 ---")

driver.quit()

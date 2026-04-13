"""
각 사이트 전체 HTML을 파일로 저장합니다.
실행 후 생성된 txt 파일들을 Claude에게 공유해주세요.
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
    ("utp", "https://www.utp.or.kr/board/board.php?bo_table=sub0501&menu_group=4&sno=0401"),
    ("uepa", "https://www.uepa.or.kr/sub/?mcode=0403010000"),
    ("ccei", "https://ccei.creativekorea.or.kr/ulsan/custom/notice_list.do"),
]
 
for name, url in sites:
    driver.get(url)
    time.sleep(4)
    html = driver.page_source
    filename = f"{name}_full.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"{name}: {len(html)}자 → {filename} 저장 완료")
 
driver.quit()
print("\n완료! 생성된 utp_full.txt, uepa_full.txt, ccei_full.txt 파일을 Claude에게 업로드해주세요.")
 

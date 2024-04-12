# 필요 패키지 호출
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import time
import re
    
    # 크롤링 시작
"""
driver.get(url)을 통해 검색 페이지 접속하고,
target 변수에 크롤링할 게시글의 수를 바인딩
"""

def main(word, username, password):

    print(word)

    # 크롬 브라우저 열기
    driver = webdriver.Chrome()

    # driver.get('https://www.instagram.com')
    driver.get('https://www.facebook.com/login.php?skip_api_login=1&api_key=124024574287414&kid_directed_site=0&app_id=124024574287414&signed_next=1&next=https%3A%2F%2Fwww.facebook.com%2Fdialog%2Foauth%3Fclient_id%3D124024574287414%26locale%3Dko_KR%26redirect_uri%3Dhttps%253A%252F%252Fwww.instagram.com%252Faccounts%252Fsignup%252F%26response_type%3Dcode%252Cgranted_scopes%26scope%3Demail%26state%3D%257B%2522fbLoginKey%2522%253A%2522arnpt31yzqct5txgwu91851bd6acy5703jq4fg1ve3ddy1oy97q3%2522%252C%2522fbLoginReturnURL%2522%253A%2522%252Ffxcal%252Fdisclosure%252F%253Fnext%253D%25252F%2522%257D%26ret%3Dlogin%26fbapp_pres%3D0%26logger_id%3Db4698f2d-f7d4-488c-9629-c51c29bbbaab%26tp%3Dunspecified&cancel_url=https%3A%2F%2Fwww.instagram.com%2Faccounts%2Fsignup%2F%3Ferror%3Daccess_denied%26error_code%3D200%26error_description%3DPermissions%2Berror%26error_reason%3Duser_denied%26state%3D%257B%2522fbLoginKey%2522%253A%2522arnpt31yzqct5txgwu91851bd6acy5703jq4fg1ve3ddy1oy97q3%2522%252C%2522fbLoginReturnURL%2522%253A%2522%252Ffxcal%252Fdisclosure%252F%253Fnext%253D%25252F%2522%257D%23_%3D_&display=page&locale=ko_KR&pl_dbl=0')

    time.sleep(3)

    # 인스타그램에 로그인하기 위한 정보를 설정합니다. (자신의 정보로 대체해야 함)


    # 사용자 이름과 비밀번호 입력 필드를 찾고, 로그인 정보를 입력합니다.
    username_input = driver.find_element(By.NAME, 'email')
    password_input = driver.find_element(By.NAME, 'pass')

    username_input.send_keys(username)
    password_input.send_keys(password)

    # 로그인 버튼을 찾아 클릭합니다.
    login_button = driver.find_element(By.XPATH, '//*[@id="loginbutton"]')
    login_button.click()

    time.sleep(10)

    login_button2 = driver.find_element(By.XPATH, '//*[contains(text(),"님으로 계속")]')
    login_button2.click()

    time.sleep(5)

    login_button3 = driver.find_element(By.XPATH, '//*[text()="나중에 하기"]')
    login_button3.click()

    time.sleep(3)

    # 게시물을 조회할 검색 키워드 입력 요청
    #word = input("검색어를 입력하세요 : ")
    word = str(word)
    url = insta_searching(word)


    # 검색 결과 페이지 열기
    driver.get(url)
    time.sleep(8) # 코드 수행 환경에 따라 페이지가 로드되는 데 시간이 더 걸릴 수 있어 8초로 변경(2022/01/11)

    # 첫 번째 게시물 클릭
    select_first(driver)

    # 본격적으로 데이터 수집 시작
    results = []
    ## 수집할 게시물의 수
    target = 10
    for i in range(target):

        try:
            data = get_content(driver)
            results.append(data)
            move_next(driver)
        except:
            time.sleep(2)
            #move_next(driver)
            break
        time.sleep(2)

    print(results[:2])

    # 결과를 데이터프레임으로 저장
    import pandas as pd
    from datetime import datetime

    date = datetime.today().strftime('%Y-%m-%d')

    results_df = pd.DataFrame(results)
    #results_df.columns = ['content','date','like','place','tags']
    results_df.columns = ['content','date','tags']
    results_df.to_excel('insta_crawling.xlsx')


# 함수 정의: 검색어 조건에 따른 url 생성
def insta_searching(word):
    url = "https://www.instagram.com/explore/tags/" + str(word)
    return url

# 함수 정의: 열린 페이지에서 첫 번째 게시물 클릭 + sleep 메소드 통하여 시차 두기
def select_first(driver):
    first = driver.find_elements(By.CSS_SELECTOR, "div._aagw")[0]
    first.click()
    time.sleep(3)
    
    # 함수 정의: 본문 내용, 작성일자, 좋아요 수, 위치 정보, 해시태그 가져오기
import re
from bs4 import BeautifulSoup

def get_content(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    # 본문 내용
    try:
        content = soup.select('div._a9zs')[0].text
    except:
        content = ''
    # 해시태그
    tags = re.findall(r'#[^\s#,\\]+', content)
    
    # 작성일자
    try:
        date = soup.select('time._a9ze')[0]['datetime'][:10]
    except:    
        date = ''
        
    # 좋아요
    try:
        like = soup.select('div._aacl._aaco._aacw._aacx._aada._aade')[0].findAll('span')[-1].text
    except:
        like = 0
    # 위치
    try:
        place = soup.select('div._aaqm')[0].text
    except:
        place = ''

    #data = [content, date, like, place, tags]
    data = [content, date, tags]
    return data

# 함수 정의: 첫 번째 게시물 클릭 후 다음 게시물 클릭
def move_next(driver):
    try:
        right = driver.find_element(By.CSS_SELECTOR, "div._aaqg._aaqh") # 2022/01/11 수정
        right.click()
        time.sleep(2)
    except:
        return


if __name__ == '__main__':
    word = ""
    username = ""
    password = ""
    main(word, username, password)
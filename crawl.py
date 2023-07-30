from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import json
from bs4 import BeautifulSoup

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location= '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
driver = webdriver.Chrome(options=chrome_options)

with open('./data_crawl.json', 'r') as f:
    data = json.load(f)
# ContentTypeID : 12(관광지) 14(문화시설) 15(축제공연행사) 25(여행코스) 28(레포츠) 38(숙박) 39(음식점)
titles = [item['title'] for item in data['item'] if item['contenttypeid'] == '39'] # 음식점들의 title 값만 가져옴

non_info = []

for title in titles:
    # 필요한 변수 초기화
    phone = ''
    open_close_dic = {}
    info = ''
    driver.get(f"https://map.naver.com/v5/search/{title}")
    
    try: # 바로 검색 결과가 나왔을 때 정보 긁어옴
        # 매장 Iframe으로 이동
        entryiframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe#entryIframe')))
    except: # 검색 결과가 바로 안 나올 때 주소로 다시 검색해서 찾아옴
        for item in data['item']:
            if item['title'] == title:
                address = item['addr1']
        search_text = f' {address}'
        search_input_box = driver.find_element_by_css_selector("div.input_box>input.input_search")
        search_input_box.send_keys(search_text)
        search_input_box.send_keys(Keys.ENTER)
        time.sleep(5)
    time.sleep(3)
    # 매장 Iframe으로 이동
    try:
        driver.switch_to.default_content()
        driver.switch_to.frame('entryIframe')
    except: # 주소로 검색했는데 여러 개 뜰 때 맨 위에 꺼 가져옴
        try: # 아예 검색이 안 될 때
            driver.switch_to.default_content()
            driver.switch_to.frame("searchIframe")
            scroll_container = driver.find_element_by_id("_pcmap_list_scroll_container")
            get_store_li = scroll_container.find_elements_by_css_selector('ul > li')
            get_store_li[0].find_elements_by_css_selector("span[class*='place_bluelink YwYLL']")[0].click()
            time.sleep(3)
            driver.switch_to.default_content()
            driver.switch_to.frame('entryIframe')
        except: # 저장했다가 마지막에 어떤 음식점이 정보가 없는지 출력함 -> 아마 이 가게들은 일일이 찾아서 넣어야 할듯
            non_info.append(title)
            continue
    # 가게 전화번호
    try:        
        phone_class = driver.find_element_by_css_selector("[class*='O8qbU nbXkr']")
        phone = phone_class.find_element_by_css_selector('div.vV_z_ > span:nth-of-type(1)').get_attribute('innerHTML')
        phone = BeautifulSoup(phone, "html.parser").get_text()
    except: # 없음
        phone = ''
    # 가게 시간
    try:
        time.sleep(1)
        time_info_class = driver.find_element_by_css_selector("div[class*='O8qbU pSavy']")
        time_info_class.find_element_by_css_selector('div:nth-of-type(1) > span._UCia > svg').click() # 상세보기 클릭
        time.sleep(2)
        get_time_lists = time_info_class.find_elements_by_css_selector("div[class*='w9QyJ']:not(div[class*='w9QyJ '])") # 영업 시간
        get_closed_lists = time_info_class.find_elements_by_css_selector("div[class*='w9QyJ undefined']") # 휴일
        open_close_dic = {}
        for get_time_list in get_time_lists: # 운영 시간 요일별로 가져옴
            day = get_time_list.find_elements_by_css_selector('span.i8cJw')[0].get_attribute('innerHTML')
            day = BeautifulSoup(day, "html.parser").get_text() # 요일
            time_info = get_time_list.find_elements_by_css_selector('div.H3ua4')[0].get_attribute('innerHTML')
            # time_info = BeautifulSoup(time_info, "html.parser").get_text()
            time_info = time_info.replace("<br>","&") # 운영 시간 정보 -> 구분 편하게 & 로 구분해둠
            open_close_dic[day] = time_info
            
        for get_closed_list in get_closed_lists: # 쉬는날 가져옴
            day = get_closed_list.find_elements_by_css_selector('span.i8cJw')[0].get_attribute('innerHTML')
            day = BeautifulSoup(day, "html.parser").get_text() # 요일
            time_info = get_closed_list.find_elements_by_css_selector('div.H3ua4')[0].get_attribute('innerHTML')
            # time_info = BeautifulSoup(time_info, "html.parser").get_text()
            time_info = time_info.replace("<br>","&") # 운영 시간 정보
            time_info = time_info.replace("<span>","") # 운영 시간 정보
            time_info = time_info.replace("</span>","") # 운영 시간 정보
            open_close_dic[day] = time_info
    except: # 없음
        open_close_dic = {}
    # 가게 정보
    try:
        info_class = driver.find_elements_by_css_selector("div[class*='O8qbU']:not(div[class*='O8qbU '])")
        if len(info_class) == 1:
            tmp = info_class[0].find_element_by_css_selector('span.place_blind').get_attribute('innerHTML')
            if BeautifulSoup(tmp, "html.parser").get_text() == '편의':
                info = info_class[0].find_element_by_css_selector('div.vV_z_').get_attribute('innerHTML')
                info = BeautifulSoup(info, "html.parser").get_text()
        else:
            for info_one in info_class:
                tmp = info_one.find_element_by_css_selector('span.place_blind').get_attribute('innerHTML')
                if BeautifulSoup(tmp, "html.parser").get_text() == '편의':
                    info = info_one.find_element_by_css_selector('div.vV_z_').get_attribute('innerHTML')
                    info = BeautifulSoup(info, "html.parser").get_text()
                    break
    except: # 없음
        info = ''

    # 크롤링한 정보 새로운 속성과 값으로 저장
    for item in data['item']:
        if item['title'] == title:
            item['phone'] = phone
            item['time'] = open_close_dic
            item['info'] = info
            # 확인차 출력
            print(f"title: {title}")
            print(f"phone: {phone}")
            print(f"open_close: {open_close_dic}")
            print(f"info: {info}")
            print("----------------------------------")
            
# 작업 마친 후 파일 저장
with open('./data_crawl.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("***********정보가 없는 가게들")
print(non_info)
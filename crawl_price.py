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
    # driver.get("https://map.naver.com/v5/entry/place/12899219?c=15,0,0,0,dh")
    
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

    # 대표 메뉴 & 가격
    try:
        price_dic = {}
        time.sleep(1)
        time_info_class = driver.find_element_by_css_selector('div.place_fixed_maintab') # 상세보기 클릭
        time_info_class_path = time_info_class.find_element_by_css_selector("div[class*='flicking-camera']")
        path_list = time_info_class_path.find_elements_by_css_selector('a')
        menu_index = 0
        for i in range(len(path_list)):
            tmp = path_list[i].find_element_by_css_selector("span").get_attribute('innerHTML')
            if BeautifulSoup(tmp, "html.parser").get_text() == "메뉴":
                menu_index = i
                break
        path = path_list[i].find_element_by_css_selector("span")
        path.click()
        time.sleep(2)
        get_price = driver.find_element_by_css_selector("div[class*='place_section no_margin']") # 영업 시간
        get_price_list = get_price.find_elements_by_css_selector("ul > li")
        menu = get_price_list[0].find_element_by_css_selector('div.yQlqY > span.lPzHi').get_attribute('innerHTML')
        menu = BeautifulSoup(menu, "html.parser").get_text()
        price = get_price_list[0].find_element_by_css_selector('div.GXS1X').get_attribute('innerHTML')
        price = BeautifulSoup(price, "html.parser").get_text()
        price_dic[menu] = price
    except: # 사진 없을 때
        try:
            get_price_list = driver.find_elements_by_css_selector("div.order_list_inner")
            get_menu_list = get_price_list[0].find_elements_by_css_selector('ul > li')
            menu = get_menu_list[0].find_element_by_css_selector('div.tit').get_attribute('innerHTML')
            menu = BeautifulSoup(menu, "html.parser").get_text()
            price = get_menu_list[0].find_element_by_css_selector('div.price').get_attribute('innerHTML')
            price = BeautifulSoup(price, "html.parser").get_text()
            price_dic[menu] = price
        except:
            try:
                get_price = driver.find_elements_by_css_selector("div[class*='place_section gkWf3']")
                get_price_list = get_price[0].find_elements_by_css_selector("ul > li")
                menu = get_price_list[0].find_element_by_css_selector('div.erVoL > div.MENyI').get_attribute('innerHTML')
                menu = BeautifulSoup(menu, "html.parser").get_text()
                price = get_price_list[0].find_element_by_css_selector('div.Yrsei > div.gl2cc').get_attribute('innerHTML')
                price = BeautifulSoup(price, "html.parser").get_text()
                price_dic[menu] = price
            except:
                price_dic = {}

    # 크롤링한 정보 새로운 속성과 값으로 저장
    for item in data['item']:
        if item['title'] == title:
            item['price'] = price_dic
            # 확인차 출력
            print(f"title: {title}")
            print(f"price: {price_dic}")
            print("----------------------------------")
            
# 작업 마친 후 파일 저장
with open('./data_crawl.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("***********정보가 없는 가게들")
print(non_info)
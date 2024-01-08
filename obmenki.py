import requests
import json
from datetime import datetime as dt
from datetime import timedelta
import pandas as pd
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from fake_useragent import UserAgent
import math
import re
from git import Repo
import csv
from github import Github
import schedule


def main():

    # 24СМИ

    token = '4c8e4b0b9fcfcd8ee6bec3c80cf976e5f103f9e1'
    user_id = '20356'

    headers = {'Authorization': f'Token {token}'}
    url = 'https://cabinet.24smi.info/exchange/v2/informer/stat'

    df = pd.read_csv('obmenki.csv', encoding='utf-8')
    # df.drop(labels = [0], axis = 0, inplace=True)
    # df.to_csv('obmenki.csv', index=False)


    today = dt.today().date()
    yesterday = (today - timedelta(days=1))
    month3 = (today - timedelta(days=90))

    payload = {
    "date_from": f"{today}",
    "date_to": f"{today}",
    "detail": "day",
    "group_by": [
      "date"
    ]
    }
    r = requests.post(url, headers=headers, json=payload)
    data = r.json()
    # print(json.dumps(data, indent=4, ensure_ascii=False))

    dates_list = []
    clicks_list = []
    shows_list = []
    ctr_list = []
    k_list = []

    for i in data['stat']:
        dte = i['stat']['key']
        dates_list.append(dte)
        clicks = int(i['stat']['clicks'])
        clicks_list.append(clicks)
        shows = int(i['stat']['shows'])
        shows_list.append(shows)
        ctr = float(i['stat']['ctr'])
        ctr_list.append(ctr)
        k = float(i['stat']['k'])
        k_list.append(k)


    # СМИ2
    
    # настраиваем опции браузера
    ua = UserAgent()
    options = webdriver.ChromeOptions()
    options.add_argument(ua.random)
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(
        'user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1')
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(options=options)

    driver.get('https://smi2.net/dashboard/login')
    time.sleep(5)

    email_input = driver.find_element(By.XPATH, '//*[@id="vars.user.email"]')
    email_input.send_keys('analytics@kommersant.ru')
    password_input = driver.find_element(By.XPATH, '//*[@id="vars.user.password"]')
    password_input.send_keys('pYXATabaBYca7')
    enter_button = driver.find_element(By.XPATH, '/html/body/div/ui-view/div[1]/div/div[2]/form/button').click()
    time.sleep(8)

    soup = bs(driver.page_source, 'lxml')
    away_clicks1 = soup.findAll('div', 'key-metrics__value ng-binding ng-isolate-scope')
    away_clicks2 = away_clicks1[0].get('lx-tooltip')
    away_clicks = away_clicks2.replace(' ', '')
    away_clicks = int(away_clicks)


    clicks1 = soup.findAll('div', 'key-metrics__value ng-binding ng-isolate-scope')
    clicks2 = clicks1[2].get('lx-tooltip')
    clicks = clicks2.replace(' ', '')
    clicks_smi2 = int(clicks)

    shows = clicks1[3].get('lx-tooltip')
    shows = shows.replace(' ', '')
    shows_smi2 = int(shows)

    ctr1 = soup.findAll('div', 'key-metrics__value ng-binding')
    ctr2 = ctr1[1].text
    ctr3 = ctr2.strip()
    ctr4 = ctr3.split(' ')
    ctr5 = ctr4[0].replace(',', '.')
    ctr_smi2 = float(ctr5)

    k = away_clicks / clicks_smi2
    k = round(k, 1)
    k_smi2 = float(k)
    
    driver.quit()

    # INFOX

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    payload = {
        "lb_inline": "true",
        "lb_login": "analytics@kommersant.ru",
        "lb_password": "gO@ciPAIjFZ4",
        "lb_remember": "true"
    }

    today = dt.now().strftime('%d.%m.%Y')
    url = f'https://adm.infox.sg/reportResourceDaily?id=&dateGroup=day&date1={today}&date2={today}&resourceId=18904&scriptId='

    session = requests.Session()
    session.headers.update(headers)
    response = session.post(url, data=payload)
    soup = bs(response.text, 'lxml')

    pattern = '\xa0'

    shows1 = soup.find('th', string='Итого:').find_next_sibling('th').find_next_sibling('th').text
    shows2 = re.sub(pattern, '', shows1)
    shows_infox = int(shows2)

    clicks1 = soup.find('th', string='Итого:').find_next_sibling('th').find_next_sibling('th').find_next_sibling(
        'th').text
    clicks2 = re.sub(pattern, '', clicks1)
    clicks_infox = int(clicks2)

    ctr1 = clicks_infox / shows_infox * 100
    ctr2 = round(ctr1, 2)
    ctr_infox = float(ctr2)

    url2 = f'https://adm.infox.sg/sgstatClicks?id=&dateGroup=day&date1={today}&date2={today}&domains=kommersant.ru&byDomain=false'
    session = requests.Session()
    session.headers.update(headers)
    response2 = session.post(url2, data=payload)

    soup2 = bs(response2.text, 'lxml')
    k1 = soup2.find('th', string='Всего').find_next_sibling('th').find_next_sibling('th').find_next_sibling(
        'th').find_next_sibling('th').find_next_sibling('th').text
    k2 = k1.replace(',', '.')
    k_infox = float(k2)

    # ЗАПИСЫВАЕМ ДАТАСЕТ И ДОБАВЛЯЕМ К СТАРОМУ НОВУЮ СТРОКУ

    df_last = pd.DataFrame(
    {
        'dates': dates_list,
        '24smi_clicks': clicks_list,
        '24smi_shows': shows_list,
        '24smi_ctr': ctr_list,
        '24smi_k': k_list,
        'smi2_clicks': clicks_smi2,
        'smi2_shows': shows_smi2,
        'smi2_ctr': ctr_smi2,
        'smi2_k': k_smi2,
        'infox_clicks': clicks_infox,
        'infox_shows': shows_infox,
        'infox_ctr': ctr_infox,
        'infox_k': k_infox,
    })

    df = pd.concat([df_last, df], ignore_index=True)
    df.to_csv('obmenki.csv', encoding='utf-8', index=False)
    

    # Путь к локальному репозиторию
    repo_path = '/other'
    
    # Инициализация репозитория
    repo = Repo(repo_path)
    
    # Добавление файла seo_titles.csv
    file_path = '/other/obmenki.csv'
    repo.index.add([file_path])
    
    # Создание коммита
    repo.index.commit('Добавлен файл obmenki.csv')
    
    # Отправка изменений на удаленный репозиторий
    origin = repo.remote('origin')
    origin.push()

# настройка расписания
schedule.every().day.at("23:45", "Europe/Moscow").do(main)

while True:
    schedule.run_pending()
    time.sleep(1)

if __name__ == "__main__":
    main()

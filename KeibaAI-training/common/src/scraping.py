import re
import time
import traceback
from pathlib import Path
from urllib.request import urlopen,Request

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from tqdm.notebook import tqdm
from webdriver_manager.chrome import ChromeDriverManager

DATA_DIR = Path("data")
HTML_RACE_DIR = DATA_DIR / "html" / "race"
HTML_HORSE_DIR = DATA_DIR / "html" / "horse"
HTML_PED_DIR = DATA_DIR / "html" / "ped"
HTML_LEADING_DIR = DATA_DIR / "html" / "leading"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}


def scrape_kaisai_date(from_: str, to_: str, save_dir: Path = None) -> list[str]:
    """
    from_とto_をyyyy-mmの形で指定すると、間の開催日一覧を取得する関数。
    save_dirを指定すると、取得結果がkaisai_date_list.txtとして保存される。
    """
    kaisai_date_list = []
    for date in tqdm(pd.date_range(from_, to_, freq="MS")):
        year = date.year
        month = date.month
        url = f"https://race.netkeiba.com/top/calendar.html?year={year}&month={month}"
        req = Request(url, headers= HEADERS)
        html = urlopen(req).read()  # スクレイピング
        time.sleep(1)  # 絶対忘れないように
        soup = BeautifulSoup(html, "lxml")
        a_list = soup.find("table", class_="Calendar_Table").find_all("a")
        for a in a_list:
            kaisai_date = re.findall(r"kaisai_date=(\d{8})", a["href"])[0]
            kaisai_date_list.append(kaisai_date)
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        with open(save_dir / "kaisai_date_list.txt", "w") as f:
            f.write("\n".join(kaisai_date_list))
    return kaisai_date_list


def scrape_race_id_list(
    kaisai_date_list: list[str], save_dir: Path = None
) -> list[str]:
    """
    開催日（yyyymmdd形式）をリストで入れると、レースid一覧が返ってくる関数。
    save_dirを指定すると、取得結果がrace_id_list.txtとして保存される。
    """
    options = Options()
    # ヘッドレスモード（バックグラウンド）で起動
    options.add_argument("--headless")
    # その他のクラッシュ対策
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver_path = ChromeDriverManager().install()
    race_id_list = []

    with webdriver.Chrome(service=Service(driver_path), options=options) as driver:
        # 要素を取得できない時、最大10秒待つ
        driver.implicitly_wait(10)
        for kaisai_date in tqdm(kaisai_date_list):
            url = f"https://race.netkeiba.com/top/race_list.html?kaisai_date={kaisai_date}"
            try:
                driver.get(url)
                time.sleep(1)
                li_list = driver.find_elements(By.CLASS_NAME, "RaceList_DataItem")
                for li in li_list:
                    href = li.find_element(By.TAG_NAME, "a").get_attribute("href")
                    race_id = re.findall(r"race_id=(\d{12})", href)[0]
                    race_id_list.append(race_id)
            except:
                print(f"stopped at {url}")
                print(traceback.format_exc())
                break
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        with open(save_dir / "race_id_list.txt", "w") as f:
            f.write("\n".join(race_id_list))
    return race_id_list


def scrape_html_race(
    race_id_list: list[str], save_dir: Path = HTML_RACE_DIR, skip: bool = True
) -> list[Path]:
    """
    netkeiba.comのraceページのhtmlをスクレイピングしてsave_dirに保存する関数。
    skip=Trueにすると、すでにhtmlが存在する場合はスキップされる。
    逆に上書きしたい場合は、skip=Falseにする。
    スキップされたhtmlのパスは返り値に含まれない。
    """
    updated_html_path_list = []
    save_dir.mkdir(parents=True, exist_ok=True)
    for race_id in tqdm(race_id_list):
        filepath = save_dir / f"{race_id}.bin"
        # skipがTrueで、かつファイルがすでに存在する場合は飛ばす
        if skip and filepath.is_file():
            print(f"skipped: {race_id}")
        else:
            print(race_id)
            url = f"https://db.netkeiba.com/race/{race_id}"
            req = Request(url, headers= HEADERS)
            html = urlopen(req).read()  # スクレイピング
            
            time.sleep(1)
            with open(filepath, "wb") as f:
                f.write(html)
            updated_html_path_list.append(filepath)
    return updated_html_path_list


def scrape_html_horse(
    horse_id_list: list[str], save_dir: Path = HTML_HORSE_DIR, skip: bool = True
) -> list[Path]:
    """
    netkeiba.comのhorseページのhtmlをスクレイピングしてsave_dirに保存する関数。
    skip=Trueにすると、すでにhtmlが存在する場合はスキップされる。
    逆に上書きしたい場合は、skip=Falseにする。
    スキップされたhtmlのパスは返り値に含まれない。
    """
    updated_html_path_list = []
    save_dir.mkdir(parents=True, exist_ok=True)
    for horse_id in tqdm(horse_id_list):
        filepath = save_dir / f"{horse_id}.bin"
        # skipがTrueで、かつファイルがすでに存在する場合は飛ばす
        if skip and filepath.is_file():
            print(f"skipped: {horse_id}")
        else:
            url = f"https://db.netkeiba.com/horse/{horse_id}"
            req = Request(url, headers= HEADERS)
            html = urlopen(req).read()  # スクレイピング
            time.sleep(1)
            with open(filepath, "wb") as f:
                f.write(html)
            updated_html_path_list.append(filepath)
    return updated_html_path_list


def scrape_html_leading(
    leading_type: str,
    year: int,
    pages: list[int],
    save_dir: Path = HTML_LEADING_DIR,
    skip: bool = True,
) -> list[Path]:
    """
    リーディングページのhtmlをスクレイピングしてsave_dirに保存する関数。
    skip=Trueにすると、すでにhtmlが存在する場合はスキップされる。
    逆に上書きしたい場合は、skip=Falseにする。
    スキップされたhtmlのパスは返り値に含まれない。
    """
    updated_html_path_list = []
    save_dir = save_dir / leading_type
    save_dir.mkdir(parents=True, exist_ok=True)
    for page in tqdm(pages):
        filepath = save_dir / f"{year}_{str(page).zfill(2)}.bin"
        # skipがTrueで、かつファイルがすでに存在する場合は飛ばす
        if skip and filepath.is_file():
            print(f"skipped: {filepath}")
        else:
            url = (
                f"https://db.netkeiba.com//?pid={leading_type}&year={year}&page={page}"
            )
            req = Request(url, headers= HEADERS)
            html = urlopen(req).read()  # スクレイピング
            time.sleep(1)
            with open(filepath, "wb") as f:
                f.write(html)
            updated_html_path_list.append(filepath)
    return updated_html_path_list


def scrape_html_ped(
    horse_id_list: list[str], save_dir: Path = HTML_PED_DIR, skip: bool = True
) -> list[Path]:
    """
    netkeiba.comのpedページのhtmlをスクレイピングしてsave_dirに保存する関数。
    skip=Trueにすると、すでにhtmlが存在する場合はスキップされる。
    逆に上書きしたい場合は、skip=Falseにする。
    スキップされたhtmlのパスは返り値に含まれない。
    """
    updated_html_path_list = []
    save_dir.mkdir(parents=True, exist_ok=True)
    for horse_id in tqdm(horse_id_list):
        filepath = save_dir / f"{horse_id}.bin"
        # skipがTrueで、かつファイルがすでに存在する場合は飛ばす
        if skip and filepath.is_file():
            print(f"skipped: {horse_id}")
        else:
            url = f"https://db.netkeiba.com/horse/ped/{horse_id}"
            req = Request(url, headers= HEADERS)
            html = urlopen(req).read()  # スクレイピング
            time.sleep(1)
            with open(filepath, "wb") as f:
                f.write(html)
            updated_html_path_list.append(filepath)
    return updated_html_path_list

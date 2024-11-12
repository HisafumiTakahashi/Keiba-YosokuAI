import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from tqdm.notebook import tqdm

DATA_DIR = Path("data")
RAWDF_DIR = DATA_DIR / "rawdf"


def create_results(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "results.csv",
) -> pd.DataFrame:
    """
    保存されているraceページのhtmlを読み込んで、レース結果テーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                race_id = html_path.stem
                html = (
                    f.read()
                    .replace(b"<diary_snap_cut>", b"")
                    .replace(b"</diary_snap_cut>", b"")
                )
                soup = BeautifulSoup(html, "lxml").find(
                    "table", class_="race_table_01 nk_tb_common"
                )
                df = pd.read_html(html)[0]

                # horse_id列追加
                horse_id_list = []
                a_list = soup.find_all("a", href=re.compile(r"^/horse/"))
                for a in a_list:
                    horse_id = re.findall(r"\d{10}", a["href"])[0]
                    horse_id_list.append(horse_id)
                df["horse_id"] = horse_id_list

                # jockey_id列追加
                jockey_id_list = []
                a_list = soup.find_all("a", href=re.compile(r"^/jockey/"))
                for a in a_list:
                    jockey_id = re.findall(r"\d{5}", a["href"])[0]
                    jockey_id_list.append(jockey_id)
                df["jockey_id"] = jockey_id_list

                # trainer_id列追加
                trainer_id_list = []
                a_list = soup.find_all("a", href=re.compile(r"^/trainer/"))
                for a in a_list:
                    trainer_id = re.findall(r"\d{5}", a["href"])[0]
                    trainer_id_list.append(trainer_id)
                df["trainer_id"] = trainer_id_list

                # owner_id列追加
                owner_id_list = []
                a_list = soup.find_all("a", href=re.compile(r"^/owner/"))
                for a in a_list:
                    owner_id = re.findall(r"\d{6}", a["href"])[0]
                    owner_id_list.append(owner_id)
                df["owner_id"] = owner_id_list

                # 最初の列にrace_idを挿入
                df.insert(0, "race_id", race_id)
                dfs[race_id] = df
            except IndexError as e:
                print(f"table not found at {race_id}")
                continue
    concat_df = pd.concat(dfs.values())
    concat_df.columns = concat_df.columns.str.replace(" ", "")
    save_dir.mkdir(parents=True, exist_ok=True)
    update_rawdf(
        concat_df,
        key="race_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def create_race_info(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "race_info.csv",
) -> pd.DataFrame:
    """
    保存されているraceページのhtmlを読み込んで、レース情報テーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                # ファイル名からrace_idを取得
                race_id = html_path.stem
                html = f.read()
                soup = BeautifulSoup(html, "lxml").find("div", class_="data_intro")
                info_dict = {}
                info_dict["title"] = soup.find("h1").text
                p_list = soup.find_all("p")
                info_dict["info1"] = re.findall(
                    r"[\w:]+", p_list[0].text.replace(" ", "")
                )
                info_dict["info2"] = re.findall(r"\w+", p_list[1].text)
                df = pd.DataFrame().from_dict(info_dict, orient="index").T
                # 最初の列にrace_idを挿入
                df.insert(0, "race_id", race_id)
                dfs[race_id] = df
            except IndexError as e:
                print(f"table not found at {race_id}")
                continue
            except AttributeError as e:
                print(f"{e} at {race_id}")
                continue
    concat_df = pd.concat(dfs.values())
    concat_df.columns = concat_df.columns.str.replace(" ", "")
    save_dir.mkdir(exist_ok=True, parents=True)
    update_rawdf(
        concat_df,
        key="race_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def create_return_tables(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "return_tables.csv",
) -> pd.DataFrame:
    """
    保存されているraceページのhtmlを読み込んで、払い戻しテーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                html = f.read()
                df_list = pd.read_html(html)
                df = pd.concat([df_list[1], df_list[2]])

                # ファイル名からrace_idを取得
                race_id = html_path.stem
                # 最初の列にrace_idを挿入
                df.insert(0, "race_id", race_id)
                dfs[race_id] = df
            except IndexError as e:
                print(f"table not found at {race_id}")
                continue
    concat_df = pd.concat(dfs.values())
    save_dir.mkdir(exist_ok=True, parents=True)
    update_rawdf(
        concat_df,
        key="race_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def create_horse_results(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "horse_results.csv",
) -> pd.DataFrame:
    """
    保存されているhorseページのhtmlを読み込んで、馬の過去成績テーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                horse_id = html_path.stem
                html = f.read()
                df = pd.read_html(html)[3]
                # 受賞歴がある馬の場合、3番目に受賞歴テーブルが来るため、4番目のデータを取得する
                if df.columns[0] == "受賞歴":
                    df = pd.read_html(html)[4]
                # 新馬の競走馬レビューが付いた場合、次のhtmlへ飛ばす
                elif df.columns[0] == 0:
                    continue
                # 最初の列にrace_idを挿入
                df.insert(0, "horse_id", horse_id)
                dfs[horse_id] = df
            except IndexError as e:
                print(f"table not found at {horse_id}")
                continue
            except ValueError as e:
                print(f"{e} at {horse_id}")
                continue
    concat_df = pd.concat(dfs.values())
    concat_df.columns = concat_df.columns.str.replace(" ", "")
    save_dir.mkdir(parents=True, exist_ok=True)
    update_rawdf(
        concat_df,
        key="horse_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def create_jockey_leading(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "jockey_leading.csv",
) -> pd.DataFrame:
    """
    保存されているjockey_leadingページのhtmlを読み込んで、騎手成績テーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                page_id = html_path.stem
                html = f.read()
                soup = BeautifulSoup(html, "lxml").find("table", class_="nk_tb_common")
                df = pd.read_html(html)[0]
                # マルチインデックスを解除
                df.columns = [
                    "_".join(col) if col[0] != col[1] else col[0] for col in df.columns
                ]
                # jockey_id列追加
                jockey_id_list = []
                a_list = soup.find_all("a", href=re.compile(r"^/jockey/"))
                for a in a_list:
                    jockey_id = re.findall(r"\d{5}", a["href"])[0]
                    jockey_id_list.append(jockey_id)
                df.insert(0, "jockey_id", jockey_id_list)
                # 最初の列にkey列を挿入
                df.insert(0, "page_id", page_id)
                dfs[page_id] = df
            except IndexError as e:
                print(f"table not found at {page_id}")
                continue
    concat_df = pd.concat(dfs.values())
    concat_df.columns = concat_df.columns.str.replace(" ", "")
    save_dir.mkdir(parents=True, exist_ok=True)
    update_rawdf(
        concat_df,
        key="page_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def create_trainer_leading(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "trainer_leading.csv",
) -> pd.DataFrame:
    """
    保存されているtrainer_leadingページのhtmlを読み込んで、騎手成績テーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                page_id = html_path.stem
                html = f.read()
                soup = BeautifulSoup(html, "lxml").find("table", class_="nk_tb_common")
                df = pd.read_html(html)[0]
                # マルチインデックスを解除
                df.columns = [
                    "_".join(col) if col[0] != col[1] else col[0] for col in df.columns
                ]
                # trainer_id列追加
                trainer_id_list = []
                a_list = soup.find_all("a", href=re.compile(r"^/trainer/"))
                for a in a_list:
                    trainer_id = re.findall(r"\d{5}", a["href"])[0]
                    trainer_id_list.append(trainer_id)
                df.insert(0, "trainer_id", trainer_id_list)
                # 最初の列にkey列を挿入
                df.insert(0, "page_id", page_id)
                dfs[page_id] = df
            except IndexError as e:
                print(f"table not found at {page_id}")
                continue
    concat_df = pd.concat(dfs.values())
    concat_df.columns = concat_df.columns.str.replace(" ", "")
    save_dir.mkdir(parents=True, exist_ok=True)
    update_rawdf(
        concat_df,
        key="page_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def create_peds(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "peds.csv",
) -> pd.DataFrame:
    """
    保存されているpedページのhtmlを読み込んで、血統テーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                horse_id = html_path.stem
                html = f.read()
                soup = BeautifulSoup(html, "lxml").find(
                    "table", class_="blood_table detail"
                )
                td_list = soup.find_all("td")
                ped_id_list = []
                for td in td_list:
                    ped_id = re.findall(r"horse/(\w+)", td.find("a")["href"])[0]
                    ped_id_list.append(ped_id)
                df = pd.DataFrame(ped_id_list).T.add_prefix("ped_")
                # 最初の列にhorse_idを挿入
                df.insert(0, "horse_id", horse_id)
                dfs[horse_id] = df
            except IndexError as e:
                print(f"table not found at {horse_id}")
                continue
            except ValueError as e:
                print(f"{e} at {horse_id}")
                continue
    concat_df = pd.concat(dfs.values())
    save_dir.mkdir(parents=True, exist_ok=True)
    update_rawdf(
        concat_df,
        key="horse_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def create_sire_leading(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "sire_leading.csv",
) -> pd.DataFrame:
    """
    保存されているsire_leadingページのhtmlを読み込んで、騎手成績テーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                page_id = html_path.stem
                html = f.read()
                soup = BeautifulSoup(html, "lxml").find("table", class_="nk_tb_common")
                df = pd.read_html(html)[0]
                # マルチインデックスを解除
                df.columns = [
                    "_".join(col) if col[0] != col[1] else col[0] for col in df.columns
                ]
                # sire_id列追加
                sire_id_list = []
                a_list = soup.find_all("a", href=re.compile(r"sire/"))
                for a in a_list:
                    sire_id = re.findall(r"sire/(\w+)/", a["href"])[0]
                    sire_id_list.append(sire_id)
                df.insert(0, "sire_id", sire_id_list)
                # 最初の列にkey列を挿入
                df.insert(0, "page_id", page_id)
                dfs[page_id] = df
            except IndexError as e:
                print(f"table not found at {page_id}")
                continue
    concat_df = pd.concat(dfs.values())
    concat_df.columns = concat_df.columns.str.replace(" ", "")
    save_dir.mkdir(parents=True, exist_ok=True)
    update_rawdf(
        concat_df,
        key="page_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def create_bms_leading(
    html_path_list: list[Path],
    save_dir: Path = RAWDF_DIR,
    save_filename: str = "bms_leading.csv",
) -> pd.DataFrame:
    """
    保存されているbms_leadingページのhtmlを読み込んで、騎手成績テーブルに加工する関数。
    """
    dfs = {}
    for html_path in tqdm(html_path_list):
        with open(html_path, "rb") as f:
            try:
                page_id = html_path.stem
                html = f.read()
                soup = BeautifulSoup(html, "lxml").find("table", class_="nk_tb_common")
                df = pd.read_html(html)[0]
                # マルチインデックスを解除
                df.columns = [
                    "_".join(col) if col[0] != col[1] else col[0] for col in df.columns
                ]
                # bms_id列追加
                bms_id_list = []
                a_list = soup.find_all("a", href=re.compile(r"sire/"))
                for a in a_list:
                    bms_id = re.findall(r"sire/(\w+)/", a["href"])[0]
                    bms_id_list.append(bms_id)
                df.insert(0, "bms_id", bms_id_list)
                # 最初の列にkey列を挿入
                df.insert(0, "page_id", page_id)
                dfs[page_id] = df
            except IndexError as e:
                print(f"table not found at {page_id}")
                continue
    concat_df = pd.concat(dfs.values())
    concat_df.columns = concat_df.columns.str.replace(" ", "")
    save_dir.mkdir(parents=True, exist_ok=True)
    update_rawdf(
        concat_df,
        key="page_id",
        save_filename=save_filename,
        save_dir=save_dir,
    )
    return concat_df


def update_rawdf(
    new_df: pd.DataFrame,
    key: str,
    save_filename: str,
    save_dir: Path = RAWDF_DIR,
) -> None:
    """
    既存のrawdfに新しいデータを追加して保存する関数。
    """
    save_dir.mkdir(parents=True, exist_ok=True)
    if (save_dir / save_filename).exists():
        old_df = pd.read_csv(save_dir / save_filename, sep="\t", dtype={f"{key}": str})
        # 念の為、key列をstr型に変換
        new_df[key] = new_df[key].astype(str)
        df = pd.concat([old_df[~old_df[key].isin(new_df[key])], new_df])
        df.to_csv(save_dir / save_filename, sep="\t", index=False)
    else:
        # ファイルが存在しない場合は単にそのまま保存
        new_df.to_csv(save_dir / save_filename, sep="\t", index=False)

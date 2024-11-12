from pathlib import Path

import pandas as pd

COMMON_DATA_DIR = Path("..", "..", "common", "data")
INPUT_DIR = COMMON_DATA_DIR / "rawdf"
MAPPING_DIR = COMMON_DATA_DIR / "mapping"
OUTPUT_DIR = Path("..", "data", "01_preprocessed")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

sex_mapping = {"牡": 0, "牝": 1, "セ": 2}
race_type_mapping = {"ダ": 0, "芝": 1, "障": 3}
weather_mapping = {"晴": 0, "曇": 1, "小雨": 2, "雨": 3}
ground_state_mapping = {"良": 0, "稍": 1, "稍重": 1, "重": 2, "不":3, "不良":3}
race_class_mapping = {
    "新馬": 0,
    "未勝利": 1,
    "1勝クラス": 2,
    "2勝クラス": 3,
    "3勝クラス": 4,
    "オープン": 5,
    "G3": 6,
    "G2": 7,
    "G1": 8,
    "OP": 5,
    "特別": 5,
    "500万以下": 2,
    "1000万以下": 3,
    "1600万以下": 4,
    }

def process_results(
    input_dir: Path = INPUT_DIR,
    output_dir: Path = OUTPUT_DIR,
    save_filename: str = "results.csv",
    sex_mapping: dict = sex_mapping
) -> pd.DataFrame:
    """
    レース結果テーブルのrawデータファイルをinput_dirから読み込んで、加工し、
    output_dirに保存する関数。
    """

    df = pd.read_csv(input_dir / save_filename, sep="\t")
    df["rank"] = pd.to_numeric(df["着順"], errors="coerce")
    df.dropna(subset=["rank"], inplace=True)
    df["rank"] = df["rank"].astype(int)
    
    df["sex"] = df["性齢"].str[0].map(sex_mapping)
    df["age"] = df["性齢"].str[1:].astype(int)
    df["weight"] = df["馬体重(増減)"].str.extract(r"(\d+)").astype(int)
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce")
    df["weight_diff"] = df["馬体重(増減)"].str.extract(r"\((.+)\)")
    df["weight_diff"] = df["weight_diff"].fillna(0).astype(int)
    df["weight_diff"] = pd.to_numeric(df["weight_diff"], errors="coerce")
    df["tansho_odds"] = df["単勝オッズ"].astype(float)
    df["popularity"] = df["人気"].astype(int)
    df["impost"] = df["斤量"].astype(float)
    df["wakuban"] = df["枠"].astype(int)
    df["umaban"] = df["馬番"].astype(int)

    # データが着順に並んでいることによるリーク防止のため、各レースを馬番順にソートする
    df = df.sort_values(["race_id", "umaban"])
    # 使用する列を選択
    df = df[
        [
            "race_id",
            "horse_id",
            "jockey_id",
            "trainer_id",
            "rank",
            "sex",
            "age",
            "weight",
            "weight_diff",
            "tansho_odds",
            "popularity",
            "impost",
            "wakuban",
            "umaban"
        ]
    ]

    df.to_csv(output_dir / save_filename, sep="\t")
    return df

def process_horse_results(
    input_dir: Path = INPUT_DIR,
    output_dir: Path = OUTPUT_DIR,
    save_filename: str = "horse_results.csv",
    race_type_mapping: dict = race_type_mapping,
    weather_mapping: dict = weather_mapping,
    ground_state_mapping: dict = ground_state_mapping,
    race_class_mapping: dict = race_class_mapping

) -> pd.DataFrame:
    """
    馬の過去成績テーブルのrawデータファイルをinput_dirから読み込んで、加工し、
    output_dirに保存する関数。
    """

    df = pd.read_csv(input_dir / save_filename, sep="\t")
    df["rank"] = pd.to_numeric(df["着順"], errors="coerce")
    df.dropna(subset=["rank"], inplace=True)
    df["date"] = pd.to_datetime(df["日付"])
    df["weather"] = df["天気"].map(weather_mapping)
    df["race_type"] = df["距離"].str[0].map(race_type_mapping)
    df["course_len"] = df["距離"].str.extract(r"(\d+)").astype(int)
    df["ground_state"] = df["馬場"].map(ground_state_mapping)
    df["rank_diff"] = df["着差"].map(lambda x: 0 if x < 0 else x)
    df["prize"] = df["賞金"].fillna(0)
    regex_race_class = "|".join(race_class_mapping.keys())
    df["race_class"] = df["レース名"].str.extract(rf"({regex_race_class})")[0].map(race_class_mapping)
    df.rename(columns={"頭数": "n_horses"}, inplace=True)

    df = df[
        [
            "horse_id",
            "date",
            "rank",
            "prize",
            "rank_diff",
            "weather",
            "race_type",
            "course_len",
            "ground_state",
            "race_class",
            "n_horses"
        ]
    ]

    df.to_csv(output_dir / save_filename, sep="\t")
    return df




from pathlib import Path

import pandas as pd

COMMON_DATA_DIR = Path("..", "..", "common", "data")
RAWDF_DIR = COMMON_DATA_DIR / "rawdf"
OUTPUT_DIR = Path("..", "data", "00_population")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


def create(
    from_: str,
    to_: str,
    input_dir: Path = RAWDF_DIR,
    race_info_filename: str = "race_info.csv",
    results_filename: str = "results.csv",
    output_dir: Path = OUTPUT_DIR,
    output_filename: str = "population.csv",
) -> pd.DataFrame:
    """
    from_に開始日、to_に終了日を指定（yyyy-mm-dd形式）して、その期間に絞って
    学習母集団である（race_id, date, horse_id）の組み合わせを作成する。
    """
    race_info = pd.read_csv(input_dir / race_info_filename, sep="\t")
    race_info["date"] = pd.to_datetime(
        race_info["info2"].map(lambda x: eval(x)[0]), format="%Y年%m月%d日"
    )
    results = pd.read_csv(input_dir / results_filename, sep="\t")
    population = (
        race_info.query("@from_ <= date <= @to_")[["race_id", "date"]]
        .merge(results[["race_id", "horse_id"]], on="race_id")
        .sort_values(["date", "race_id"])
    )
    population.to_csv(output_dir / output_filename, sep="\t", index=False)
    return population

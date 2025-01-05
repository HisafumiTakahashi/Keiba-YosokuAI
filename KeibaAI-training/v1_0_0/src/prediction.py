import pickle
from pathlib import Path
import lightgbm as lgb
import pandas as pd
import yaml

DATA_DIR = Path("data")
MODEL_DIR = DATA_DIR / "03_train"
OUTPUT_DIR = Path("predict_result")


def predict(
    features: pd.DataFrame,
    model_dir: Path = MODEL_DIR,
    model_filename: Path = "model.pkl",
    config_filepath: Path = "config.yaml",
    output_dir: Path = OUTPUT_DIR,
    output_filename = "predict_result.csv"
):
    with open(config_filepath, "r") as f:
        feature_cols = yaml.safe_load(f)["features"]
    # with open(model_dir / model_filename, "rb") as f:
    #     model = pickle.load(f)
    model = lgb.Booster(model_file=Path("model", "modelbetween0101-1131.txt"))
    prediction_df = features[["race_id", "umaban", "tansho_odds", "popularity"]].copy()
    prediction_df["pred"] = model.predict(features[feature_cols])

    prediction_df.to_csv(output_dir / output_filename, sep="\t", index=False)

    return prediction_df.sort_values("pred", ascending=False)

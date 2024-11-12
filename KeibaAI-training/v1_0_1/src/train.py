import pickle
from pathlib import Path

import lightgbm as lgb
import matplotlib.pyplot as plt
import pandas as pd
import yaml
from sklearn.metrics import log_loss

DATA_DIR = Path("..", "data")
INPUT_DIR = DATA_DIR / "02_features"
OUTPUT_DIR = DATA_DIR / "03_train"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class Trainer:
    def __init__(
        self,
        input_dir: Path = INPUT_DIR,
        features_filename: str = "features.csv",
        config_filepath: Path = "config.yaml",
        output_dir: Path = OUTPUT_DIR,
    ):
        self.features = pd.read_csv(input_dir / features_filename, sep="\t")
        with open(config_filepath, "r") as f:
            config = yaml.safe_load(f)
            self.feature_cols = config["features"]
            self.params = config["params"]
        self.output_dir = output_dir

    def create_dataset(self, valid_start_date: str, test_start_date: str):
        """
        test_start_dateをYYYY-MM-DD形式で指定すると、
        その日付以降のデータをテストデータに、
        それより前のデータを学習データに分割する関数。
        """
        # 目的変数
        self.features["target"] = (self.features["rank"] == 1).astype(int)
        # 学習データとテストデータに分割
        self.train_df = self.features.query("date < @valid_start_date")
        self.valid_df = self.features.query(
            "date >= @valid_start_date and date < @test_start_date"
        )
        self.test_df = self.features.query("date >= @test_start_date")

    def train(
        self,
        train_df: pd.DataFrame,
        valid_df: pd.DataFrame,
        test_df: pd.DataFrame,
        importance_filename: str,
        model_filename: str,
    ) -> pd.DataFrame:
        # データセットの作成
        lgb_train = lgb.Dataset(train_df[self.feature_cols], train_df["target"])
        lgb_valid = lgb.Dataset(
            valid_df[self.feature_cols], valid_df["target"], reference=lgb_train
        )
        # 学習の実行
        model = lgb.train(
            params=self.params,
            train_set=lgb_train,
            num_boost_round=10000,
            valid_sets=[lgb_valid],
            callbacks=[
                lgb.log_evaluation(100),
                lgb.early_stopping(stopping_rounds=100),
            ],
        )
        self.best_params = model.params
        with open(self.output_dir / model_filename, "wb") as f:
            pickle.dump(model, f)
        # 特徴量重要度の可視化
        lgb.plot_importance(
            model, importance_type="gain", figsize=(30, 15), max_num_features=50
        )
        plt.savefig(self.output_dir / f"{importance_filename}.png")
        plt.close()
        importance_df = pd.DataFrame(
            {
                "feature": model.feature_name(),
                "importance": model.feature_importance(importance_type="gain"),
            }
        ).sort_values("importance", ascending=False)
        importance_df.to_csv(
            self.output_dir / f"{importance_filename}.csv",
            index=False,
            sep="\t",
        )
        # テストデータに対してスコアリング
        evaluation_df = test_df[
            [
                "race_id",
                "horse_id",
                "target",
                "rank",
                "tansho_odds",
                "popularity",
                "umaban",
            ]
        ].copy()
        evaluation_df["pred"] = model.predict(
            test_df[self.feature_cols], num_iteration=model.best_iteration
        )
        logloss = log_loss(evaluation_df["target"], evaluation_df["pred"])
        print("-" * 20 + " result " + "-" * 20)
        print(f"test_df's binary_logloss: {logloss}")
        return evaluation_df

    def run(
        self,
        valid_start_date: str,
        test_start_date: str,
        importance_filename: str = "importance",
        model_filename: str = "model.pkl",
        evaluation_filename: str = "evaluation.csv",
    ):
        """
        学習処理を実行する。
        test_start_dateをYYYY-MM-DD形式で指定すると、
        その日付以降のデータをテストデータに、
        それより前のデータを学習データに分割する
        """
        self.create_dataset(valid_start_date, test_start_date)
        evaluation_df = self.train(
            self.train_df,
            self.valid_df,
            self.test_df,
            importance_filename,
            model_filename,
        )
        evaluation_df.to_csv(
            self.output_dir / evaluation_filename, sep="\t", index=False
        )
        return evaluation_df

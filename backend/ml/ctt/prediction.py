"""
This script does not contain any modular level code.
This is just for to give a reference that how the prediction pipeline works.
"""

if __name__ == "__main__":
    from pathlib import Path

    import dill
    import polars as pl

    raw_data = pl.read_json("../data/ctt/channels_data.json").join(
        pl.read_json("../data/ctt/titles_data.json"), on="channelId"
    )

    with Path("../data/ctt_model.dill").open("rb") as f:
        model = dill.load(f)

    pred = model.predict(
        [
            "India russia pakistan china US",
            "campusx teaches machine learning krish naik",
            "mobile apple samsung",
        ]
    )
    print(pred)

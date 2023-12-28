"""
Import training pipeline here and run it with `python3 run_pipeline.py` command. Also, you can
provide the parameters to the cli command of pipeline.
"""

from backend.ml.ctt import pipeline_for_ctt_model

if __name__ == "__main__":
    pipeline_for_ctt_model()

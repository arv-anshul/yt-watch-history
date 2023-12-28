# ML Model Migration

> [!IMPORTANT]
>
> Fixing issue [#9](https://github.com/arv-anshul/yt-watch-history/issues/9) of [arv-anshul/yt-watch-history](https://github.com/arv-anshul/yt-watch-history) repository.

## Plan of Attack

### For ContentType Prediction Model

1. **Fetch Data From Database for Model Training**

   - Fetch video details data from database and store it into local then train on it with different params.
   - Fetch ContentTypeTaggedChannel data from database to create the training data.

2. **Design Model Training Structure**

   - Used `click` package to get params from terminal.
   - Used `mlflow` library for model versioning and model monitoring.
   - Created `Pipeline` to directly encode and train videos titles data.
   - ~~Used `LabelEncoder` to encode the target labels **contentType**s.~~
     - Instead of using `LabelEncoder` encode the class labels with a pre-defined encoding technique which saves very much complexity of pipeline structure.
     - **Encoding Technique for contentType:** Assign one counting number to each contentType after **sorting them by ascending order**.
     - Do this in **preprocessing step**.
   - If the training data is not provided, we are fetching it from database. So, in that case keep the API instance running.
   - If you get your best then re-run the pipeline with `--save-model` flag to save the model at specified path or goto `/ml/ctt/store-logged-model` endpoint of the API and **provide mlflow `run_id` to copy the same model at path**.

> [!TIP]
>
> Import training pipeline at `run_pipeline.py` file and run it with `python3 run_pipeline.py` command. Also, you can provide the parameters to the cli command of pipeline.

3. **Prediction with Trained Model**

   - Created some API endpoint to make prediction with the trained models.
   - You can make prediction using `list[dict]` and alos **using JSON file** itself in one go.

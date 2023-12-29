# CttTitleModel Overview

[![Python](https://img.shields.io/badge/Code%20File-3776AB?logo=python&logoColor=fff)](https://github.com/arv-anshul/yt-watch-history/blob/main/backend/ml/ctt.py)

### Purpose and Features:

This ML model is focused on classifying YouTube video titles into predefined content categories. Some key features and functionalities include:

1. **Data Collection:** The model fetches data from a database containing information about YouTube channels (`ctt_channels_data`) and video titles (`titles_data`). It ensures the presence of required data and fetches it if missing from the specified paths or database.

- `data/ctt_channels_data.json` representation in JSON format:

  ```json
  [
    {
      "channelId": "string",
      "contentType": "string"
    }
  ]
  ```

- `data/titles_data.json` representation in JSON format:

  ```json
  [
    {
      "channelId": "string",
      "title": "string"
    }
  ]
  ```

These JOSN files are imported as `polars.DataFrame` object using [polars](https://docs.pola.rs/) library.

2. **Data Processing and Validation:** The fetched data undergoes processing,

   - Validation checks are performed to ensure the necessary columns (`channelId`, `title` and `contentType`) are present in the datasets.
   - Both data merge together on `channelId` column and then the merged dataset is ready to preprocess further.

3. **Text Preprocessing:** Before training the model, the video titles data undergoes preprocessing steps such as **removing punctuation, digits, short words, and emojis**.

4. **Model Training:** The ML model is trained using a pipeline approach, where a **TF-IDF vectorizer is combined with a Multinomial Naive Bayes classifier**.

   The vectorizer converts text data into numerical form, capturing the significance of words in the titles, while the classifier predicts the content type based on these features.

5. **Model Evaluation:** The trained model's performance is evaluated using various metrics like accuracy, precision, recall, and F1-score. Additionally, a confusion matrix is generated to understand classification performance across different content types.

6. **Logging and Saving:** The model's parameters, evaluation metrics, and the trained model itself are logged using MLflow, a platform for managing the ML lifecycle. It provides the ability to track experiments, reproduce results, and deploy models.

7. **Model Persistence:** The model can be saved locally using two different approaches - one via MLflow's model logging (`mlflow.sklearn.log_model`) and the other by directly storing the model object (`io.dump_object`) using the `dill` library.

### Key Components:

- **Data Fetching:** Fetches data from a database or specified paths if not available.
- **Data Processing:** Joins and validates the data, ensuring the necessary columns are present.
- **Text Preprocessing:** Cleans and standardizes text data for model input.
- **Model Training:** Creates a pipeline with TF-IDF vectorization and Multinomial Naive Bayes classification.
- **Model Evaluation:** Calculates various metrics and generates a confusion matrix for performance analysis.
- **Logging and Saving:** Logs parameters, metrics, and model artifacts using MLflow.
- **Model Persistence:** Provides options to save the trained model for future use.

### Command-Line Interface (CLI):

The script also contains a CLI (`pipeline_for_ctt_model`) that allows customization of model training parameters via command-line options. These options include paths to data files, model hyperparameters, and a flag to save the model.

### Conclusion:

In summary, the `CttTitles ML Model` encapsulates a pipeline for training, evaluating, and saving a machine learning model capable of categorizing YouTube video titles into predefined content types. It uses text processing techniques, ML algorithms, and MLflow for efficient model development, evaluation, and deployment.

### Acknowledgements

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)
![Polars](https://img.shields.io/badge/Polars-CD792C?logo=polars&logoColor=fff)
![MLflow](https://img.shields.io/badge/MLflow-0194E2?logo=mlflow&logoColor=fff)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=fff)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=fff)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=fff)
![OpenAI](https://img.shields.io/badge/ChatGPT-412991?logo=openai&logoColor=fff)

- **ChatGPT:** For documentation generation.
  > Also, I further did some improvisation in the ChatGPT's output.

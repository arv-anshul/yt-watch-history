# Pipeline of ML Model

Discussing the ML model pipeline from Data Ingestion to Model Training. We are not going to discuss the model deployment because I have figure it out yet that how to deploy a ML model and where.

Although, I have already built a ML pipeline and also making prediction with it. But I don't feel comfortable with it because I feel that it is lacking the scalability, reliability, monitoring options. I have implemented the MLflow but I don't know how to use it in advance way (means more than just logging metrics and parameters).

### First, discuss what I have built?

I have a model which takes **YouTube video title as input feature and its corresponding contentType as target feature while training** to tag all the videos with its contentType.
I make prediction with this model, when user uploads his watching history on my app. For prediction, I have created an API endpoint as `/ml/ctt/predict`.

## How my model trains?

- I define constants for **training data path, model path**, means I am storing the model and the training data at a specific place which is pre-defined.
- I fetches data from database for training, do validation and preprocessing on it too.
- Then train the model with all the stuffs, if I want I can log the model using mlflow. After training model stores at the specified path.

### Some improvement I can do, but don't know how?

- I can split the `DataIngestion`, `DataValidation`, `ModelTraining` and `ModelEvaluation` parts.
- I can implement the that strategy pattern which [@AyushSingh](https://github.com/ayush714/customer-satisfaction-mlops) has taught in his lecture, with some changes.

### THOUGHT: How a typical model should train and being monitored at same time using MLFLow?

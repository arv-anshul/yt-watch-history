# YouTube Watch History Analysis

This project analyzes a user's YouTube watch history data downloaded from Google Takeout. It provides insights into watch patterns, content preferences, and overall YouTube consumption.

### Getting Your YouTube History Data

1. Go to the Google Takeout website: [Google Takeout](https://takeout.google.com/)
2. Sign in with your Google account.
3. Select "YouTube History" under "Choose data to export".
4. Choose **JOSN** file type and delivery options.
5. Click "Create export".
6. Wait for the export process to complete and download the file.

##### Or refer to this blog at [dev.to](https://dev.to/ubershmekel/what-did-i-watch-most-on-youtube-1ol2).

### Benefits

- Gain valuable insights into your YouTube viewing habits.
- Discover your content preferences and identify areas of interest.
- Track your progress towards achieving your YouTube goals.
- Make informed decisions about your YouTube consumption.

### Project's Notebooks

If you want to see my 📓 notebooks where I have done some interesting analysis on the datasets which I have used in this project then you can se them in my [**@arv-anshul/notebooks**](https://github.com/arv-anshul/notebooks/tree/main/yt-watch-history) github repository.

### Tech Stack

![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=fff)
![MLflow](https://img.shields.io/badge/MLflow-0194E2?logo=mlflow&logoColor=fff)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=fff)
![NLTK](https://img.shields.io/badge/NLTK-3776AB?logo=python&logoColor=fff)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?logo=plotly&logoColor=fff)
![Polars](https://img.shields.io/badge/Polars-CD792C?logo=polars&logoColor=fff)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=fff)
![Ruff](https://img.shields.io/badge/Ruff-FCC21B?logo=ruff&logoColor=000)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=fff)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=fff)
![YouTube Badge](https://img.shields.io/badge/YouTube-F00?logo=youtube&logoColor=fff)

## Project Setup Guide

This guide helps you set up and run this project using Docker Compose. The project consists of a frontend and backend service.

### Prerequisites

- [🍀 MongoDB Database URL](https://mongodb.com)
- [💥 Youtube Data v3 API Key](https://developers.google.com/youtube/v3/docs/)
- [🐳 Docker](https://www.docker.com/get-started)
- [🐳 Docker Compose](https://docs.docker.com/compose/install/)

### Steps to Set Up

1. Clone the Repository:

   ```bash
   git clone https://github.com/arv-anshul/yt-watch-history
   ```

2. Configuration:

   - Open the `docker-compose.yml` file in the project root.

   - Set the following environment variables in the `frontend` service:

     - `YT_API_KEY`: Replace `null` with your YouTube API key.
     - `API_HOST`: Should match the name of the backend service **(`backend` in this case)**.
     - `API_PORT`: Port number for the backend service **(default is `8001`)**.
     - `LOG_LEVEL`: Logging level **(default is `INFO`)**.

   - Set the following environment variables in the `backend` service:

     - `MONGODB_URL`: Replace `null` with your MongoDB URL.
     - `API_PORT`: Port number for the backend service **(default is `8001`)**.
     - `API_HOST`: Set to `"0.0.0.0"`.
     - `LOG_LEVEL`: Logging level **(default is `INFO`)**.

3. Build and Run:

   ```bash
   docker-compose up --build
   ```

4. Access the application:

   - **Frontend:** Open a browser and go to `http://localhost:8501`.
   - **Backend:** Accessed internally via the configured API endpoints. Or access locally at `http://0.0.0.0:8001`.

> [!NOTE]
>
> - Frontend service runs on port `8501` locally.
> - Backend service runs on port `8001` locally.
> - Make sure no other services are running on these ports.
> - `/frontend` and `/backend` directories are mounted as volumes for the respective services.
> - `/frontend/data` and `/backend/ml_models` directories are mounted for persistent data storage.

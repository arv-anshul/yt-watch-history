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

### Tech Stack

|               Tech | Stack                                                                                                                                                                                                                                                          |
| -----------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|                API | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=fff) ![YouTube Badge](https://img.shields.io/badge/YouTube-F00?logo=youtube&logoColor=fff)                                                                                       |
|           Database | ![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=fff)                                                                                                                                                                             |
|      Web Framework | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=fff)                                                                                                                                                                       |
|    Data Validation | ![Pydantic](https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=fff)                                                                                                                                                                          |
|   Machine Learning | ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=fff) ![NLTK](https://img.shields.io/badge/NLTK-3776AB?logo=python&logoColor=fff)                                                                                  |
|  Data Manipulation | ![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=fff) ![Polars](https://img.shields.io/badge/Polars-CD792C?logo=polars&logoColor=fff)                                                                                                |
| Data Visualization | ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?logo=plotly&logoColor=fff) ![Matplotlib](https://img.shields.io/badge/Matplotlib-3776AB?logo=matplotlib&logoColor=fff) ![Seaborn](https://img.shields.io/badge/Seaborn-3776AB?logo=seaborn&logoColor=fff) |

### Project Initialization

1. Clone the project repo using `git` command:

```sh
git clone https://github.com/arv-anshul/yt-watch-history
```

2. In a virtual environment, install the required dependencies using `pip` command:

```sh
pip install -r requirements.txt
```

3. Run the streamlit app:

```sh
# Using streamlit command (Recommended)
streamlit run README.py

# Using make command (Easy)
make st
```

4. Access webpage using `localhost` url:

```sh
# This URL displays in your terminal
http://localhost:8501
```

5. Now, you can see basic insights of your **Watch History** but you can also see **Advance Insights** of your history. For that, you have to run the api.

### Initialize Advance Insights Process

#### Prerequisite

1. [**MongoDB Database URL**](https://mongodb.com)
2. [**Youtube Data v3 API Key**](https://developers.google.com/youtube/v3/docs/)

#### Now, when you have all the prerequisite.

1. Rename `example.env` file to `.env` and fill the `MONGODB_URL` and `YT_API_KEY` parameters.

2. Run the api using terminal _(Use anyone command)_:

```sh
# Using python command
python -m api.app

# Using uvicorn command
uvicorn api.app:app

# Using make command (Easy)
make api
```

3. You can access the api in your local system at `localhost` url:

```sh
https://localhost:8000/
```

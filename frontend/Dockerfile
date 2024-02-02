FROM python:3.11-slim

WORKDIR /app/frontend

# Install dependency for `wordcloud` module
RUN apt-get update && apt-get install -y gcc

RUN pip install -U pip
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . .

CMD [ "streamlit", "run", "README.py" ]

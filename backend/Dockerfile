FROM python:3.11-slim

WORKDIR /backend

RUN pip install -U pip
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "app.py" ]

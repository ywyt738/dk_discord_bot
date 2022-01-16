FROM python:3.10.1-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir db
COPY . .

VOLUME [ "dk.db" ]

CMD [ "python", "./bot.py" ]
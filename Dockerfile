FROM python:3.10.1-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir db
COPY . .

CMD [ "python", "./bot.py" ]
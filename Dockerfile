FROM python:3.11.1-slim

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir .

CMD [ "python", "./bot.py" ]
FROM python:3.11-slim

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY db/ db/
COPY settings/ settings/
COPY tgbot ./telegram_bot
COPY .env .env
COPY main.py main.py

CMD [ "python", "-u", "main.py" ]

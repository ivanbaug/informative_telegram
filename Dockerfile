FROM python:3.9

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./telegram_bot ./telegram_bot

CMD [ "python", "-u", "./telegram_bot/main.py" ]

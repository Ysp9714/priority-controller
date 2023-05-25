FROM python:3.9

COPY ./src /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ./app.sh
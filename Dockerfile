FROM python:3.8-buster

WORKDIR /app
RUN apt-get update; apt-get install -y ffmpeg git

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

ARG FLASK_ENV="production"
ENV FLASK_ENV="${FLASK_ENV}" \
    PYTHONUNBUFFERED="true"

COPY . .

CMD ["gunicorn", "-c", "python:config.gunicorn", "encoder_ui.app:create_app()"]
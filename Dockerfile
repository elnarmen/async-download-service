FROM docker.io/python:3.10

WORKDIR /async-download-service

RUN apt-get update && apt-get install -y zip

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt

RUN pip3 install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

ENV GIT_PYTHON_REFRESH=quiet

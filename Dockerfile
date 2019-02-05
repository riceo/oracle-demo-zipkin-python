FROM python:2.7-alpine

RUN mkdir /src && apk add --update alpine-sdk
WORKDIR /src

COPY ./* ./
RUN pip install -r requirements.pip

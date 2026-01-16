FROM python:3.9-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV CRYPTOGRAPHY_DONT_BUILD_RUST 1
ENV LIVE_RELOAD_SUPPORT='true' \
    AUTO_UPDATE='true' \
    UPDATE_INTERVAL=15

RUN apk update \
    && apk add --no-cache bash

ADD ./requirements.txt /tmp/

WORKDIR /tmp
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ADD . /code/

ADD entrypoint.sh /
RUN chmod +x /entrypoint.sh

WORKDIR /code/

EXPOSE 8000
EXPOSE 9000

CMD /./entrypoint.sh

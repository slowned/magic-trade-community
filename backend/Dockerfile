FROM python:3.9-alpine3.18

ARG ENVIRONMENT
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt

WORKDIR /app
EXPOSE 8000

RUN apk add pkgconfig


RUN set -x && \
    deps=" \
        build-base \
        gcc \
        musl-dev \
        linux-headers \
        python3-dev \
        libffi-dev \
        pkgconfig \
        postgresql-dev \
        jpeg-dev \
        openjpeg-dev \
        zlib-dev \
        freetype-dev \
        lcms2-dev \
        libwebp-dev \
        tiff-dev \
        libpng-dev \
        shadow \
    " && \
    python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache --virtual .tmp-deps $deps && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    apk del .tmp-deps && \
    adduser --disabled-password --no-create-home app

RUN chown -R app /py

ENV PATH="/scripts:/py/bin:$PATH"

COPY . .

USER app

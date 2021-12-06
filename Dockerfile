FROM tensorflow/tensorflow:1.14.0-py3

USER root

ENV SHELL=/bin/bash

WORKDIR /tf

COPY requirements.txt /tf/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tf/requirements.txt

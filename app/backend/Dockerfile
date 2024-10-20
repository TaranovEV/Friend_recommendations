FROM python:3.10-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt update -y && \
    apt install -y python3-dev \
    openjdk-11-jdk \
    gcc \
    musl-dev && \
    rm -rf /var/lib/apt/lists/*
#    openjdk-11-jdk-headless curl &&  \
#    rm -rf /var/lib/apt/lists/*

#ENV SPARK_VERSION=3.2.0
#RUN curl -L -o /tmp/spark.tgz "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop2.7.tgz" \
#    && tar -xzf /tmp/spark.tgz -C /opt/ \
#    && rm /tmp/spark.tgz
#ENV SPARK_HOME=/opt/spark-${SPARK_VERSION}-bin-hadoop2.7
#ENV PATH=$SPARK_HOME/bin:$PATH

ADD /app/backend/pyproject.toml /app

RUN pip install --upgrade pip
RUN pip install poetry

RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi

COPY ../.. /app/
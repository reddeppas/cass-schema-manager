FROM python:3-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    && pip3 install cassandra-driver 

ADD . /app
WORKDIR /app

CMD ["python", "/app/schema_manage.py"]

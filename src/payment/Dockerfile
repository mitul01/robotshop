FROM python:3.9

EXPOSE 8080
USER root

ENV INSTANA_SERVICE_NAME=payment

ENV JAEGER_HOST_NAME = "localhost"
ENV JAEGER_HOST_PORT = 6831

WORKDIR /app

COPY requirements.txt /app/

RUN pip install -r requirements.txt
RUN pip install opentelemetry-instrumentation-flask
RUN pip install opentelemetry-instrumentation-requests
RUN pip install opentelemetry-sdk install opentelemetry-api
RUN pip install opentelemetry-instrumentation opentelemetry-exporter-jaeger
COPY *.py /app/
COPY payment.ini /app/

CMD ["python3", "payment2.py"]
# CMD ["uwsgi", "--ini", "payment.ini"]


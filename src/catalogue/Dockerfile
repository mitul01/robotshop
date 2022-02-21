FROM node:14

ENV INSTANA_AUTO_PROFILE true

EXPOSE 8080

WORKDIR /opt/server

COPY package.json /opt/server/

RUN npm install
RUN npm install @opentelemetry/api
RUN npm install @opentelemetry/sdk-node
RUN npm install @opentelemetry/auto-instrumentations-node 
RUN npm install @opentelemetry/exporter-collector
RUN npm install @opentelemetry/exporter-trace-otlp-http 
RUN npm install @opentelemetry/exporter-jaeger
RUN npm install @opentelemetry/resources
RUN npm install @opentelemetry/instrumentation-express
RUN npm install @opentelemetry/instrumentation-http
RUN npm install @opentelemetry/propagator-ot-trace
RUN npm install @opentelemetry/sdk-trace-node
RUN npm install @opentelemetry/instrumentation 
RUN npm install @opentelemetry/tracing

COPY tracer.js /opt/server/
COPY server.js /opt/server/

CMD ["node", "server.js"]


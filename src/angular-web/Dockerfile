#stage 1
FROM node:latest as node
WORKDIR /app
COPY . .
RUN npm install
RUN npm run build --prod

#stage 2
FROM nginx:1.20.1
EXPOSE 8080
ENV CATALOGUE_HOST=catalogue \
    USER_HOST=user \
    CART_HOST=cart \
    SHIPPING_HOST=shipping \
    PAYMENT_HOST=payment \
    RATINGS_HOST=ratings \
    INSTANA_SERVICE_NAME=nginx-web

COPY entrypoint.sh /root/
ENTRYPOINT ["/root/entrypoint.sh"]
COPY default.conf.template /etc/nginx/conf.d/default.conf.template
COPY --from=node /app/dist/robotshop-web /usr/share/nginx/html
COPY --from=node /app/empty.html /usr/share/nginx/html
COPY --from=node /app/eum-tmpl.html /usr/share/nginx/html

import random

#import instana
import os
import sys
import time
import logging
import uuid
import json
import requests
import traceback
from flask import Flask
from flask import Response
from flask import request
from flask import jsonify
from rabbitmq import Publisher
# Prometheus
import prometheus_client
from prometheus_client import Counter, Histogram
# Wavefront 
from wavefront_sdk.client_factory import WavefrontClientFactory
from wavefront_sdk.entities.histogram import histogram_granularity


def send_metrics(wavefront_client):
    """Send a metric."""
    wavefront_client.send_metric(
        'python.proxy.payment.amount',
        4242.0, None, 'payment1', None)
    wavefront_client.send_metric(
        'python.proxy.cart.count',
        4.0, None, 'payment1', None)


def send_delta_counter(wavefront_client):
    """Send a delta counter."""
    wavefront_client.send_delta_counter(
        'python.delta.proxy.counter',
        1.0, 'python-delta', None)


def send_histogram(wavefront_client):
    """Send a histogram."""
    wavefront_client.send_distribution(
        'python.proxy.request.latency',
        [(30, 20), (5.1, 10)], {histogram_granularity.DAY,
                                histogram_granularity.HOUR,
                                histogram_granularity.MINUTE},
        None, 'appServer1', {'region': 'us-west'})


def send_tracing_span(wavefront_client):
    """Send a tracing span."""
    wavefront_client.send_span(
        'getAllUsersFromPythonProxy', 1533529977, 343500, 'python-span',
        uuid.UUID('7b3bf470-9456-11e8-9eb6-529269fb1459'),
        uuid.UUID('0313bafe-9457-11e8-9eb6-529269fb1459'),
        [uuid.UUID('2f64e538-9457-11e8-9eb6-529269fb1459')], None,
        [('application', 'robot-shop-1'),("service", "payment"),
         ('http.method', 'GET')], None)


def send_event(wavefront_client):
    """Send an event."""
    wavefront_client.send_event(
        'event_via_proxy',
        1590650592,
        1590650692,
        "python-event",
        ["env:", "test"],
        {"severity": "info",
         "type": "backup",
         "details": "broker backup"})


app = Flask(__name__)
app.logger.setLevel(logging.INFO)

CART = os.getenv('CART_HOST', 'cart')
USER = os.getenv('USER_HOST', 'user')
PAYMENT_GATEWAY = os.getenv('PAYMENT_GATEWAY', 'https://paypal.com/')

# Prometheus
PromMetrics = {}
PromMetrics['SOLD_COUNTER'] = Counter('sold_count', 'Running count of items sold')
PromMetrics['AUS'] = Histogram('units_sold', 'Avergae Unit Sale', buckets=(1, 2, 5, 10, 100))
PromMetrics['AVS'] = Histogram('cart_value', 'Avergae Value Sale', buckets=(100, 200, 500, 1000, 2000, 5000, 10000))


@app.errorhandler(Exception)
def exception_handler(err):
    app.logger.error(str(err))
    return str(err), 500

@app.route('/health', methods=['GET'])
def health():
    return 'OK'

# Prometheus
@app.route('/metrics', methods=['GET'])
def metrics():
    res = []
    for m in PromMetrics.values():
        res.append(prometheus_client.generate_latest(m))

    return Response(res, mimetype='text/plain')


@app.route('/pay/<id>', methods=['POST'])
def pay(id):
    app.logger.info('payment for {}'.format(id))
    cart = request.get_json()
    app.logger.info(cart)

    anonymous_user = True

    # check user exists
    try:
        req = requests.get('http://{user}:8080/check/{id}'.format(user=USER, id=id))
    except requests.exceptions.RequestException as err:
        app.logger.error(err)
        return str(err), 500
    if req.status_code == 200:
        anonymous_user = False

    # check that the cart is valid
    # this will blow up if the cart is not valid
    has_shipping = False
    for item in cart.get('items'):
        if item.get('sku') == 'SHIP':
            has_shipping = True

    if cart.get('total', 0) == 0 or has_shipping == False:
        app.logger.warn('cart not valid')
        return 'cart not valid', 400

    # dummy call to payment gateway, hope they dont object
    try:
        req = requests.get(PAYMENT_GATEWAY)
        app.logger.info('{} returned {}'.format(PAYMENT_GATEWAY, req.status_code))
    except requests.exceptions.RequestException as err:
        app.logger.error(err)
        return str(err), 500
    if req.status_code != 200:
        return 'payment error', req.status_code

    # Prometheus
    # items purchased
    item_count = countItems(cart.get('items', []))
    PromMetrics['SOLD_COUNTER'].inc(item_count)
    PromMetrics['AUS'].observe(item_count)
    PromMetrics['AVS'].observe(cart.get('total', 0))

    # Generate order id
    orderid = str(uuid.uuid4())
    queueOrder({ 'orderid': orderid, 'user': id, 'cart': cart })

    # add to order history
    if not anonymous_user:
        try:
            req = requests.post('http://{user}:8080/order/{id}'.format(user=USER, id=id),
                    data=json.dumps({'orderid': orderid, 'cart': cart}),
                    headers={'Content-Type': 'application/json'})
            app.logger.info('order history returned {}'.format(req.status_code))
        except requests.exceptions.RequestException as err:
            app.logger.error(err)
            return str(err), 500

    # delete cart
    try:
        req = requests.delete('http://{cart}:8080/cart/{id}'.format(cart=CART, id=id));
        app.logger.info('cart delete returned {}'.format(req.status_code))
    except requests.exceptions.RequestException as err:
        app.logger.error(err)
        return str(err), 500
    if req.status_code != 200:
        return 'order history update error', req.status_code

    return jsonify({ 'orderid': orderid })


def queueOrder(order):
    app.logger.info('queue order')

    # For screenshot demo requirements optionally add in a bit of delay
    delay = int(os.getenv('PAYMENT_DELAY_MS', 0))
    time.sleep(delay / 1000)

    headers = {}
    publisher.publish(order, headers)


def countItems(items):
    count = 0
    for item in items:
        if item.get('sku') != 'SHIP':
            count += item.get('qty')

    return count


# RabbitMQ
publisher = Publisher(app.logger)

if __name__ == "__main__":
    client_factory = WavefrontClientFactory()
    #client_factory.add_client("proxy://mtandon-z01:2878")
    #client_factory.add_client("http://mtandon-z01:30000")
    client_factory.add_client("proxy://wavefront-proxy.wavefront:2878")
    client_factory.add_client("http://wavefront-proxy.wavefront:30000")
    wavefront_client = client_factory.get_client()


    send_metrics(wavefront_client)
    send_histogram(wavefront_client)
    send_tracing_span(wavefront_client)
    send_delta_counter(wavefront_client)
    send_event(wavefront_client)
    time.sleep(15)
    
    wavefront_client.close()

    # logging
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    app.logger.info('Payment gateway {}'.format(PAYMENT_GATEWAY))
    port = int(os.getenv("SHOP_PAYMENT_PORT", "8080"))
    app.logger.info('Starting on port {}'.format(port))
    app.run(host='0.0.0.0', port=port)

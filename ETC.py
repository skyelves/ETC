#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name = "Fearow"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = True

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index = 0
prod_exchange_hostname = "production"

port = 25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + \
    team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)


def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")


def read_from_exchange(exchange):
    msg_list = []
    for i in range(20):
        msg = json.loads(exchange.readline())
        if msg is not None:
            msg_list.append(msg)
        else:
            break
    return msg_list


# ~~~~~============== MAIN LOOP ==============~~~~~

order_id = 0
msg = None

stocks = ['BOND', 'BABA', 'AABA', 'BIDU', 'NTES', 'SINA', 'CCUS']
items = ['sell', 'buy', 'trade']

repository = {}
stock_history = {}
avel_price = {}
order_list = {}

def establish_res():
    for stock in stocks:
        stock_history[stock] = {}
        for item in items:
            stock_history[stock][item] = []
        repository[stock] = 0
        avel_price[stock] = 0
    repository['order'] = set()

def process_msg(msg):
    if msg['type'] == "ack":
        repository['order'].add(msg['order_id'])
        order_list[msg['order_id']] = msg
    elif msg['type'] == "reject":
        pass
    elif msg['type'] == "fill":
        if msg['dir'] == "BUY":
            repository[msg['symbol']] += msg['size']
        else:
            repository[msg['symbol']] -= msg['size']
    elif msg['type'] == "out":
        repository['order'].remove(msg['order_id'])
    elif msg['type'] == "cancel":
        repository['order'].remove(msg['order_id'])
    elif msg['type'] == "book":
        if (len(msg['buy']) >0) :
            stock_history[msg['symbol']]['buy'].append(msg['buy'][0])
        if (len(msg['sell']) > 0):
            stock_history[msg['symbol']]['sell'].append(msg['sell'][0])
    elif msg['type'] == 'trade':
        stock_history[msg['symbol']]['trade'].append([msg['price'], msg['size']])
    elif msg['type'] == "hello": 
        symbols = msg['symbols']
        for symbol in symbols:
            repository[symbol['symbol']] = symbol['position']

def get_order_id():
    global order_id
    order_id += 1
    if order_id > 100000000:
        order_id = 0
    return order_id

def handle_bond(exchange):
    global msg

    write_to_exchange(
        exchange,
        {
            "type":   "add",
            "order_id": get_order_id(),
            "symbol": "BOND",
            "dir":    "BUY",
            "price":  999,
            "size":   min(100, 100-repository['BOND'])
        })

    write_to_exchange(
        exchange,
        {
            "type":   "add",
            "order_id": get_order_id(),
            "symbol": "BOND",
            "dir":    "SELL",
            "price":  1001,
            "size":   min(100, 100+repository['BOND'])
        })

    print(repository)
    #print(stock_history)


def mymin(a, b, c, d, e):
    tempmin = a
    if tempmin > min(b,c):
        tempmin = min(b,c)
    if tempmin > min(d,e):
        tempmin = min(d,e)
    return tempmin



def handle_other(exchange):
    if (len(stock_history["AABA"]["sell"]) == 0
            or len(stock_history["AABA"]["buy"]) == 0 or len(stock_history["BABA"]["sell"]) == 0
            or len(stock_history["BABA"]["buy"]) == 0 or len(stock_history["CCUS"]["sell"]) == 0
            or len(stock_history["CCUS"]["buy"]) == 0 or len(stock_history["BIDU"]["sell"]) == 0
            or len(stock_history["BIDU"]["buy"]) == 0 or len(stock_history["NTES"]["sell"]) == 0
            or len(stock_history["NTES"]["buy"]) == 0 or len(stock_history["SINA"]["sell"]) == 0
            or len(stock_history["SINA"]["buy"]) == 0):
        return
    ccus = (stock_history["CCUS"]["sell"][-1][0] + stock_history["CCUS"]["buy"][-1][0]) / 2
    bond = 1000
    bidu = (stock_history["BIDU"]["sell"][-1][0] + stock_history["BIDU"]["buy"][-1][0]) / 2
    ntes = (stock_history["NTES"]["sell"][-1][0] + stock_history["NTES"]["buy"][-1][0]) / 2
    sina = (stock_history["SINA"]["sell"][-1][0] + stock_history["SINA"]["buy"][-1][0]) / 2
    if 10*ccus + 20 < 3*bond + 2*bidu + 3*ntes + 2*sina:
        if repository['BOND'] < -85 or repository['CCUS'] > 50 or repository['BIDU'] < -90 \
                or repository['NTES'] < -85 or repository['SINA'] < -90:
            write_to_exchange(exchange, {
                "type"    : "convert",
                "order_id": get_order_id(),
                "symbol"  : "CCUS",
                "dir"     : "SELL",
                "size"    : min(abs(repository['BOND']), abs(repository['CCUS']),ans(repository['BIDU']),
                                abs(repository['NTES']), abs(repository['SINA']))})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "CCUS",
            "dir": "BUY",
            "price": int(ccus - 0.5),
            "size": 50})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BOND",
            "dir": "SELL",
            "price": int( bond + 1),
            "size": 15})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BIDU",
            "dir": "SELL",
            "price": int(bidu + 1),
            "size": 10})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "NTES",
            "dir": "SELL",
            "price": int(ntes + 1),
            "size": 15})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "SINA",
            "dir": "SELL",
            "price": int(sina + 1),
            "size": 10})
    elif 10*ccus + 20 > 3*bond + 2*bidu + 3*ntes + 2*sina:
        if repository['BOND'] > 85 or repository['CCUS'] < -50 or repository['BIDU'] > 90 \
                or repository['NTES'] > 85 or repository['SINA'] > 90:
            write_to_exchange(exchange, {
                "type"    : "convert",
                "order_id": get_order_id(),
                "symbol"  : "CCUS",
                "dir"     : "BUY",
                "size"    : min(abs(repository['BOND']), abs(repository['CCUS']), abs(repository['BIDU']),
                                abs(repository['NTES']), abs(repository['SINA']))})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "CCUS",
            "dir": "SELL",
            "price": int(ccus + 1),
            "size": 50})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BOND",
            "dir": "BUY",
            "price": int( bond - 0.5),
            "size": 15})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BIDU",
            "dir": "BUY",
            "price": int(bidu - 0.5),
            "size": 10})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "NTES",
            "dir": "BUY",
            "price": int(ntes - 0.5),
            "size": 15})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "SINA",
            "dir": "BUY",
            "price": int(sina - 0.5),
            "size": 10})
    return


def handle_baba_aaba_pair(exchange):
    if (len(stock_history["AABA"]["sell"]) == 0 or len(stock_history["AABA"]["buy"]) == 0 or len(stock_history["BABA"]["sell"]) == 0 or len(stock_history["BABA"]["buy"]) == 0):
        return
    aaba = (stock_history["AABA"]["sell"][-1][0] + stock_history["AABA"]["buy"][-1][0]) / 2
    baba = (stock_history["BABA"]["sell"][-1][0] + stock_history["BABA"]["buy"][-1][0]) / 2
    #avg = (repository['AABA'] + repository['BABA']) // 2
    #change = repository['AABA'] - avg

    if aaba < baba:
        if repository['BABA'] < -8 or repository['AABA'] > 8:
            write_to_exchange(exchange, {
                "type"    : "convert",
                "order_id": get_order_id(),
                "symbol"  : "BABA",
                "dir"     : "BUY",
                "size"    : min(abs(repository['AABA']), abs(repository['BABA']))})
        write_to_exchange(exchange, {
            "type"    : "add",
            "order_id": get_order_id(),
            "symbol"  : "AABA",
            "dir"     : "BUY",
            "price"   : int(aaba - 0.5),
            "size"    : 2})
        write_to_exchange(exchange, {
            "type"    : "add",
            "order_id": get_order_id(),
            "symbol"  : "BABA",
            "dir"     : "SELL",
            "price"   : int(baba + 1.5),
            "size"    : 2})
    elif aaba > baba:
        if repository['BABA'] > 8 or repository['AABA'] < -8:
            write_to_exchange(exchange, {
                "type"    : "convert",
                "order_id": get_order_id(),
                "symbol"  : "AABA",
                "dir"     : "BUY",
                "size"    : min(abs(repository['AABA']), abs(repository['BABA']))})
        write_to_exchange(exchange, {
            "type"    : "add",
            "order_id": get_order_id(),
            "symbol"  : "BABA",
            "dir"     : "BUY",
            "price"   : int(baba - 0.5),
            "size"    : 2})
        write_to_exchange(exchange, {
            "type"    : "add",
            "order_id": get_order_id(),
            "symbol"  : "AABA",
            "dir"     : "SELL",
            "price"   : int(aaba + 1.5),
            "size"    : 2})

def BBO(exchange):
    if (len(stock_history["AABA"]["sell"]) == 0 or len(stock_history["AABA"]["buy"]) == 0
            or len(stock_history["BABA"]["sell"]) == 0 or len(stock_history["BABA"]["buy"]) == 0
            or len(stock_history["BOND"]["sell"]) == 0 or len(stock_history["BOND"]["buy"]) == 0
            or len(stock_history["BIDU"]["sell"]) == 0 or len(stock_history["BIDU"]["buy"]) == 0
            or len(stock_history["NTES"]["sell"]) == 0 or len(stock_history["NTES"]["buy"]) == 0
            or len(stock_history["SINA"]["sell"]) == 0 or len(stock_history["SINA"]["buy"]) == 0
            or len(stock_history["CCUS"]["sell"]) == 0 or len(stock_history["CCUS"]["buy"]) == 0
    ):
        return
    if (stock_history["AABA"]["buy"][-1][0] + 5 < stock_history["AABA"]["sell"][-1][0]):
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "AABA",
            "dir": "BUY",
            "price": stock_history["AABA"]["buy"][-1][0]+1,
            "size": 2})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "AABA",
            "dir": "SELL",
            "price": stock_history["AABA"]["sell"][-1][0] - 1,
            "size": 2})
    if (stock_history["BABA"]["buy"][-1][0] > stock_history["BABA"]["sell"][-1][0] + 5):
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BABA",
            "dir": "BUY",
            "price": stock_history["BABA"]["buy"][-1][0] + 1,
            "size": 2})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BABA",
            "dir": "SELL",
            "price": stock_history["BABA"]["sell"][-1][0] - 1,
            "size": 2})
    if (stock_history["BOND"]["buy"][-1][0] + 5 < stock_history["BOND"]["sell"][-1][0]):
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BOND",
            "dir": "BUY",
            "price": stock_history["BOND"]["buy"][-1][0]+1,
            "size": 5})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BOND",
            "dir": "SELL",
            "price": stock_history["BOND"]["sell"][-1][0] - 1,
            "size": 5})
    if (stock_history["BIDU"]["buy"][-1][0] + 5 < stock_history["BIDU"]["sell"][-1][0]):
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BIDU",
            "dir": "BUY",
            "price": stock_history["BIDU"]["buy"][-1][0]+1,
            "size": 5})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "BIDU",
            "dir": "SELL",
            "price": stock_history["BIDU"]["sell"][-1][0] - 1,
            "size": 5})
    if (stock_history["NTES"]["buy"][-1][0] + 5 < stock_history["NTES"]["sell"][-1][0]):
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "NTES",
            "dir": "BUY",
            "price": stock_history["NTES"]["buy"][-1][0]+1,
            "size": 5})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "NTES",
            "dir": "SELL",
            "price": stock_history["NTES"]["sell"][-1][0] - 1,
            "size": 5})
    if (stock_history["SINA"]["buy"][-1][0] + 5 < stock_history["SINA"]["sell"][-1][0]):
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "SINA",
            "dir": "BUY",
            "price": stock_history["SINA"]["buy"][-1][0]+1,
            "size": 5})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "SINA",
            "dir": "SELL",
            "price": stock_history["SINA"]["sell"][-1][0] - 1,
            "size": 5})
    if (stock_history["CCUS"]["buy"][-1][0] + 5 < stock_history["CCUS"]["sell"][-1][0]):
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "CCUS",
            "dir": "BUY",
            "price": stock_history["CCUS"]["buy"][-1][0]+1,
            "size": 5})
        write_to_exchange(exchange, {
            "type": "add",
            "order_id": get_order_id(),
            "symbol": "CCUS",
            "dir": "SELL",
            "price": stock_history["CCUS"]["sell"][-1][0] - 1,
            "size": 5})

def main():
    global msg
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!

    establish_res()

    while True:
        msg_list = read_from_exchange(exchange)
        for msg in msg_list:
            process_msg(msg)
        #if "error" not in msg:
            #print("from exchange: ", msg)
        handle_bond(exchange)
        handle_baba_aaba_pair(exchange)
        BBO(exchange)
        #handle_other(exchange)

if __name__ == "__main__":
    main()
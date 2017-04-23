#!/usr/bin/env python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

""" Receive values from an "Elektronischer Haushaltszähler" (EHZ) using
    its infrared port attached to /dev/ttyUSB0 and provide a little
    webserver with a /metrics URL suitable to be scraped with Prometheus.

    Copyright (C) 2017, Michael "Svedrin" Ziegler <diese-addy@funzt-halt.net>.
"""

from time  import sleep
from Queue import Queue, Empty
from flask import Flask, Response
from uuid import uuid4

import serial
import sml
import threading
import json


dataqueue = Queue()
app  = Flask(__name__)
state = {"rx": None, "tx": None, "w": None}


def callback(values):
    rx = values[0][1] / 10000.
    tx = values[1][1] / 10000.
    w  = values[6][1] / 10.
    dataqueue.put({"rx": rx, "tx": tx, "w": w})


@app.route("/")
def hai():
    return Response("""<a href="/metrics">metrics</a>""")

@app.route("/metrics")
def metrics():
    while True:
        try:
            state.update( dataqueue.get_nowait() )
        except Empty:
            break

    if state["rx"] is None:
        return Response('\n', mimetype="text/plain")

    data = {
        "port":    "/dev/ttyUSB0",
        "rx":      state["rx"],
        "tx":      state["tx"],
        "rxwatts": max( state["w"], 0),
        "txwatts": max(-state["w"], 0),
    }

    return Response('\n'.join([
        '# HELP powergrid_rx Total energy consumed',
        '# TYPE powergrid_rx counter',
        'powergrid_rx{port="%(port)s"} %(rx).3f',

        '# HELP powergrid_tx Total energy fed into the grid',
        '# TYPE powergrid_tx counter',
        'powergrid_tx{port="%(port)s"} %(tx).3f',

        '# HELP powergrid_rxwatts Current power consumption',
        '# TYPE powergrid_rxwatts gauge',
        'powergrid_rxwatts{port="%(port)s"} %(rxwatts).3f',

        '# HELP powergrid_txwatts Current power feed-in',
        '# TYPE powergrid_txwatts gauge',
        'powergrid_txwatts{port="%(port)s"} %(txwatts).3f',

        '']) % data, mimetype="text/plain")


def main():
    ser = serial.Serial("/dev/ttyUSB0")
    ser.setRTS(True)

    listener = threading.Thread(name="smllistener",
            target = sml.sml_transport_listen,
            args   = (ser.fileno(), callback))
    listener.daemon = True
    listener.start()

    app.secret_key = str(uuid4())
    app.debug = False

    runner = threading.Thread(name="appruner",
            target=app.run,
            kwargs = dict(host="::", port=9100))
    runner.daemon = True
    runner.start()

    while True:
        sleep(99999)


if __name__ == '__main__':
    main()


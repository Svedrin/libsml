
import serial
import sml
import threading

from time import sleep


def callback(values):
    rx = values[0][1] / 10000.
    tx = values[1][1] / 10000.
    w  = values[6][1] / 10.
    print "rx:%f, tx:%f, watts:%f" % (rx, tx, w)


def main():
    ser = serial.Serial("/dev/ttyUSB0")
    ser.setRTS(True)

    listener = threading.Thread(name="smllistener",
            target = sml.sml_transport_listen,
            args   = (ser.fileno(), callback))
    listener.daemon = True
    listener.start()

    while True:
        sleep(2)


if __name__ == '__main__':
    main()


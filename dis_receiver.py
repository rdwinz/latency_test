#!python

__author__ = "mcgredo"
__date__ = "$Jun 25, 2015 12:10:26 PM$"

import socket
import time
import sys
import array
import math
import threading

from opendis.dis7 import *
from opendis.RangeCoordinates import *
from opendis.PduFactory import createPdu

UDP_PORT = 3001
CLOCK_SPEED = 50
PACKETS_RECEIVED = 20

class dis_receiver:

    def __init__(self):
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udpSocket.bind(("", UDP_PORT))

        print("Listening for DIS on UDP socket {}".format(UDP_PORT))

        self.clocktime = time.time()

        self.drx = 0
        self.dry = 0
        self.drxvel = 0
        self.dryvel = 0

        self.file = None
        self.start = False



    def recv(self):
        for i in range(PACKETS_RECEIVED):
            data = self.udpSocket.recv(1024) # buffer size in bytes
            self.start = True
            pdu = createPdu(data)
            pduTypeName = pdu.__class__.__name__

            # deltatime =  time.time() - self.clocktime
            # self.time = time.time()

            #Update the internal dead reckoned x and y positions based off of dead reckoning velocities
            # self.drx += self.drxvel * deltatime
            # self.dry += self.dryvel * deltatime

            x_err = self.drx - pdu.entityLocation.x
            y_err = self.dry - pdu.entityLocation.y

            self.drx = pdu.entityLocation.x
            self.dry = pdu.entityLocation.y

            self.drxvel = pdu.entityLinearVelocity.x
            self.dryvel = pdu.entityLinearVelocity.y

            if pdu.pduType == 1: # PduTypeDecoders.EntityStatePdu:
                print('Received:\n' +
                    f' x position: {pdu.entityLocation.x}\n' +
                    f' x error: {x_err}\n'
                    f' y position: {pdu.entityLocation.y}\n' +
                    f' y error: {y_err}\n' +
                    f' total error: {math.sqrt(x_err**2 + y_err**2)}' +
                    "") 
            else:
                print("Received {}, {} bytes".format(pduTypeName, len(data)), flush=True)

    def update(self):
        self.file = open("receiver_output.txt", "w")
        while not self.start:
            time.sleep(1.0/CLOCK_SPEED)
        while not self.file.closed:
            #Update the internal dead reckoned x and y positions based off of dead reckoning
            self.drx += self.drxvel * 1/CLOCK_SPEED
            self.dry += self.dryvel * 1/CLOCK_SPEED
            self.file.write(f"{time.time()},{self.drx},{self.dry}\n")
            time.sleep(1.0/CLOCK_SPEED)

if __name__ == '__main__':
    r = dis_receiver()
    t1 = threading.Thread(target=r.recv)
    t2 = threading.Thread(target=r.update)
    t1.start()
    t2.start()
    t1.join()
    r.file.close()

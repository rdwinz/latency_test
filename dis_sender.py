#!python

__author__ = "DMcG"
__date__ = "$Jun 23, 2015 10:27:29 AM$"

import socket
import time
import math

from io import BytesIO

from opendis.DataOutputStream import DataOutputStream
from opendis.dis7 import EntityStatePdu
from opendis.dis7 import DeadReckoningParameters
from opendis.RangeCoordinates import *

UDP_PORT = 3001
DESTINATION_ADDRESS = "10.0.0.2"
CLOCK_SPEED = 50
THRESHOLD_VALUE = .1
PACKETS_SEND = 20

class dis_sender:
    def __init__(self): 
        #Initialize UDP sockets  
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        #Set itital x and y values
        self.x = 0
        self.y = 0

        #Set initial x and y velocities
        self.xvel = 1
        self.yvel = cos(self.x)

        #Set initial internal dead reckoning position and velocities
        self.drx = self.x
        self.dry = self.y
        self.drxvel = self.xvel
        self.dryvel = self.yvel

        self.clocktime = 0

    def update(self, f1, f2):
        #Update the actual x and y positions
        self.x += 1/CLOCK_SPEED
        self.y = sin(self.x)

        #Update the actual x and y velocities
        self.xvel = 1
        self.yvel = cos(self.x)

        #Update the internal dead reckoned x and y positions based off of dead reckoning
        self.drx += self.drxvel * 1/CLOCK_SPEED
        self.dry += self.dryvel * 1/CLOCK_SPEED

        curr_time = time.time()
        f1.write(f"{curr_time},{self.x},{self.y}\n")
        f2.write(f"{curr_time},{self.drx},{self.dry}\n")

        self.clocktime += 1

    def send(self):
        #Update internal dead reckoning state:
        self.drx = self.x
        self.dry = self.y
        self.drxvel = 1
        self.dryvel = cos(self.x)
    
        #Create PDU to send
        pdu = EntityStatePdu()

        #Input current location into PDU
        pdu.entityLocation.x = self.x
        pdu.entityLocation.y = self.y

        pdu.entityLinearVelocity.x = self.drxvel
        pdu.entityLinearVelocity.y = self.dryvel

        #Specify dead reckoning parameters
        dr = DeadReckoningParameters()
        dr.deadReckoningAlgorithm = 2
        pdu.deadReckoningParameters = dr

        #Serialize data and prepare output stream
        memoryStream = BytesIO()
        outputStream = DataOutputStream(memoryStream)
        pdu.serialize(outputStream)
        data = memoryStream.getvalue()

        #Send packet over UDP
        self.udpSocket.sendto(data, (DESTINATION_ADDRESS, UDP_PORT))
        print("Sent {}. {} bytes".format(pdu.__class__.__name__, len(data)))

    def threshold(self):
        return math.sqrt((self.x - self.drx)**2 + (self.y - self.dry)**2) > THRESHOLD_VALUE


if __name__ == '__main__':
    f1 = open("sender_output.txt","w")
    f2 = open("sender_dr_output.txt", "w")
    s = dis_sender()
    s.send()
    time.sleep(1.0/CLOCK_SPEED)
    i = 1
    while i < PACKETS_SEND:
        if s.threshold():
            s.send()
            i += 1
        time.sleep(1.0/CLOCK_SPEED)
        s.update(f1, f2)
    f1.close()
    f2.close()



        

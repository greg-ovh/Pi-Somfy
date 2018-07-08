#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import json
import pigpio
import random


class Remote:

    STOP_BTN = 0x1
    UP_BTN = 0x2
    DOWN_BTN = 0x4
    SETUP_BTN = 0x8

    DEBUG = True

    def __init__(self, name):

        self.__name = name
        self.__id = random.randint(0, 2**(3*8)-1)  # 2 power 3 bytes times 8 bit minus 1
        self.__roll = 1

        if not os.path.isdir('remotes'):
            os.mkdir('remotes')

        if os.path.isfile('remotes/'+self.__name+'.json'):
            file = open('remotes/'+self.__name+'.json', 'r')
            try:
                remotecfg = json.loads(file.read())
                self.__id = int(remotecfg['id'], 16)
                self.__roll = remotecfg['roll']
            except Exception as e:
                print(repr(e))
            file.close()

    @staticmethod
    def display_frame(title, frame):
        print(title)
        for byte in frame:
            print "0x%0.2X" % byte,
        print("")

    def send_signal(self, button, repetition=2, TXGPIO=4):
        frame = bytearray(7)

        if Remote.DEBUG:
                print(hex(self.__id))
                print(self.__roll)

        with open('remotes/'+self.__name+'.json', 'w') as file:
            file.writelines(
                json.dumps({
                    'name': self.__name,
                    'id': hex(self.__id),
                    'roll': self.__roll+1
                })
            )

        pi = pigpio.pi() # connect to Pi

        if not pi.connected:
            exit()

        pi.wave_add_new()
        pi.set_mode(TXGPIO, pigpio.OUTPUT)

        if Remote.DEBUG:
                print("Remote  :      " + "0x%0.2X" % self.__id)
                print("Button  :      " + "0x%0.2X" % button)
                print("Rolling code : " + str(self.__roll)+"\n")

        frame[0] = 0xA7 #  Encryption key. Doesn't matter much
        frame[1] = button << 4 #  checksum (4 bit shift)
        frame[2] = self.__roll >> 8 #  Rolling code (big endian)
        frame[3] = (self.__roll & 0xFF) #  Rolling code
        frame[4] = self.__id >> 16 #  Remote address
        frame[5] = ((self.__id >>  8) & 0xFF) #  Remote address
        frame[6] = (self.__id & 0xFF) #  Remote address

        if Remote.DEBUG:
                Remote.display_frame("Frame  :    ", frame)

        checksum = 0
        for i in range(0, 7):
            checksum = checksum ^ frame[i] ^ (frame[i] >> 4)
        checksum &= 0b1111 #  We keep the last 4 bits only
        frame[1] |= checksum

        if Remote.DEBUG:
                Remote.display_frame("Frame with checksum :    ", frame)

        for i in range(1, 7):
            frame[i] ^= frame[i-1];

        if Remote.DEBUG:
                Remote.display_frame("Frame obfuscated : ", frame)

        wf=[]
        wf.append(pigpio.pulse(1<<TXGPIO, 0, 9415)) # wake up pulse
        wf.append(pigpio.pulse(0, 1<<TXGPIO, 89565)) # silence
        for i in range(2): # hardware synchronization
            wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
            wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
        wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550)) # software synchronization
        wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

        for i in range (0, 56): # manchester enconding of payload data
            if ((frame[i/8] >> (7 - (i%8))) & 1):
                wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
                wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
            else:
                wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
                wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

        wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415)) # interframe gap

        for j in range(1, repetition): # repeating frames
            for i in range(7): # hardware synchronization
                wf.append(pigpio.pulse(1<<TXGPIO, 0, 2560))
                wf.append(pigpio.pulse(0, 1<<TXGPIO, 2560))
            wf.append(pigpio.pulse(1<<TXGPIO, 0, 4550)) # software synchronization
            wf.append(pigpio.pulse(0, 1<<TXGPIO,  640))

        for i in range (0, 56): # manchester enconding of payload data
            if ((frame[i/8] >> (7 - (i%8))) & 1):
                wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))
                wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
            else:
                wf.append(pigpio.pulse(1<<TXGPIO, 0, 640))
                wf.append(pigpio.pulse(0, 1<<TXGPIO, 640))

            wf.append(pigpio.pulse(0, 1<<TXGPIO, 30415)) # interframe gap

        pi.wave_add_generic(wf)
        wid = pi.wave_create()
        pi.wave_send_once(wid)
        while pi.wave_tx_busy():
            pass
        pi.wave_delete(wid)
        pi.stop()

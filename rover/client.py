#!/usr/bin/env python3

import asyncio
import websockets

import pwmio
import busio
import board

import time
import os

import adafruit_sgp30

import threading

import cv2

from collections import namedtuple

pwm_dev = namedtuple('pwm_dev', 'dev mid_val range_val')

i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
print('i2c initialized')

try:
    sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
    print('sgp30 initialized')
except:
    print('sgp30 not detected')
    sgp30 = None


def drive_rover(drive, servo, fwd, turn):
    drive.dev.duty_cycle = drive.mid_val + (drive.range_val * fwd)
    servo.dev.duty_cycle = servo.mid_val + (servo.range_val * turn)

def hd_init():
    drive = pwm_dev(pwmio.PWMOut(board.D12), 0xB700, 0x4600)
    servo = pwm_dev(pwmio.PWMOut(board.D13), 0xBA00, 0x3400)

    return (drive, servo)

def dead_band(fwd, turn, fwd_dead, turn_dead):
    if abs(fwd) <= fwd_dead:
        fwd = 0
    if abs(turn) <= turn_dead:
        turn = 0

    return (fwd, turn)

#global eCO2
#global tvoc
eCO2 = 0.0
tvoc = 0.0

high_res = False

async def send_vox(websocket):
    global eCO2
    global tvoc
    while True:
        await websocket.send('{eCO2}:{TVOC}'.format(eCO2=eCO2, TVOC=tvoc))
        print('sending ' + '{eCO2}:{TVOC}'.format(eCO2=eCO2, TVOC=tvoc), flush=True)
        await asyncio.sleep(100/1000)

async def rover_main(websocket, drive, servo):
    global eCO2
    global tvoc

    global high_res

    #cam = cv2.VideoCapture(0)

    print('connected to server')
    while True:
        # await websocket.send("hello")
        #response = '0:0:0'
        response = await websocket.recv()
        #try:
        #    response = await asyncio.wait_for(websocket.recv(), timeout=1.5)
        #except asyncio.TimeoutError:
        #    print('timed out', flush=True)
        print(response, flush=True)
        axes = [float(s) for s in response.split(':')[:2]]
        fwd = -axes[0] *0.5
        turn = axes[1]
        fwd, turn = dead_band(fwd, turn , 0.1, 0.1)
        #print(str(fwd) + ' ' + str(turn))
        drive_rover(drive, servo, fwd, turn)

        #ret, frame = cam.read()
        #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #gray = cv2.resize(gray, (960, 540))

        #ret, buf = cv2.imencode('.jpg', gray)
        #print(frame)

        buttons = [bool(int(s)) for s in response.split(':')[2:]]
        use_vox = buttons[0]
        high_res = buttons[1]
        if use_vox:
            #print('using vox')
            eCO2, tvoc = sgp30.iaq_measure()
            #print("eCO2 = %d ppm \t TVOC = %d ppb" % (eCO2, tvoc))
            #await websocket.send('{eCO2}:{TVOC}'.format(eCO2=eCO2, TVOC=tvoc))
        else:
            pass
            #await websocket.send('-1:-1')

        await asyncio.sleep(20/1000)

async def test():
    drive, servo = hd_init()

    #cam = cv2.VideoCapture(0)

    async for websocket in websockets.connect('ws://192.168.99.32:{port}'.format(port=os.environ.get('PORT', '8000')), max_queue=1024):
        #await test2(websocket, drive, servo)
        try:
            await asyncio.gather(rover_main(websocket, drive, servo), send_vox(websocket))
        except websockets.ConnectionClosed:
            continue

def throw():
    asyncio.run(test())

async def test_cam():
    global high_res

    cam = cv2.VideoCapture(0)

    async for websocket in websockets.connect('ws://192.168.99.32:{port}'.format(port=os.environ.get('WORT', '8001'))):
        try:
            while True:
                ret, frame = cam.read()

                gray = frame
                if not high_res:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.resize(gray, (160, 90))

                ret, buf = cv2.imencode('.jpg', gray)

                await websocket.send(bytearray(buf))

                await asyncio.sleep(200/1000)
        except websockets.ConnectionClosed:
            continue

def throw_cam():
    asyncio.run(test_cam())

th = threading.Thread(target=throw)
th.start()

th2 = threading.Thread(target=throw_cam)
th2.start()

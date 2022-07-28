#!/usr/bin/env python3

import asyncio
import pygame
import websockets
import time
import threading
from turbojpeg import TurboJPEG, TJPF_GRAY, TJSAMP_GRAY, TJFLAG_PROGRESSIVE, TJFLAG_FASTUPSAMPLE, TJFLAG_FASTDCT
import cv2
import numpy as np

# create handler for each connection
# gl
# ws_data = ''

pygame.init()
pygame.joystick.init()

js1 = pygame.joystick.Joystick(0)
js1.init()
print('joystick connected: ' + str(js1.get_name()))

async def get_joy():
    pygame.event.pump()
    x_axis = js1.get_axis(3) # right stick x
    y_axis = js1.get_axis(1) # left stick y

    vox_button = js1.get_button(0) # A

    ws_data = "{y_axis}:{x_axis}:{use_vox}".format(y_axis=y_axis, x_axis=x_axis, use_vox=vox_button)
    return ws_data


async def phandler(websocket):
    while True:
        data = await get_joy()
        await websocket.send(data)
        #resp = await websocket.recv()
        #print(resp)
        await asyncio.sleep(100/1000)

async def chandler(websocket):
    while True:
        resp = await websocket.recv()
        print(resp)
        await asyncio.sleep(100/1000)

async def handler(websocket):
    await asyncio.gather(
        chandler(websocket),
        phandler(websocket),
    )

async def cam_handler(websocket):
    jpeg = TurboJPEG()
    while True:
        print('cam')
        resp = await websocket.recv()
        jpg = np.asarray(bytearray(resp), dtype=np.uint8)
        img = jpeg.decode(jpg)
        print(img)
        cv2.imshow('', img)
        cv2.waitKey(1)



# start_server = websockets.serve(handler, "192.168.99.32", 8000)
async def start_server():
    async with websockets.serve(handler, '192.168.99.32', 8000):
        await asyncio.Future()

async def start_cam_server():
    async with websockets.serve(cam_handler, '192.168.99.32', 8001):
        await asyncio.Future()

async def idk():
    await asyncio.gather(start_server(), start_cam_server())

# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()
# asyncio.run(start_server())
asyncio.run(idk())

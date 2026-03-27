#!/usr/bin/python3

from hsl3_14587_kodi import LogicModule
from hsl3.dummy import Hsl3Framework, Hsl3Slots
import logging
import time
import sys

logging.getLogger().setLevel(logging.DEBUG)
fw = Hsl3Framework("config.json")
module = LogicModule(fw)


test_input = {"server_name": b'kodi.lan',
              "port": 9090,
              "open_file": b"/srv/video/tests/stereo-test.mp3",
              "startstop": 0,
              "pauseplay": 0,
              "set_volume": 56,
              "set_mute": 0,
              "nextprev": 0,
              "repeatall": 0,
              "shuffle": 0,
              }
inputs=Hsl3Slots(test_input)
store=Hsl3Slots({})
module.on_init(inputs, store)

if True:
    print("Testing opening")
    inputs=Hsl3Slots(test_input)
    inputs["open_file"].changed = True
    module.on_calc(inputs)

    time.sleep(2)

if True:
    print("Testing playing")
    inputs=Hsl3Slots(test_input)
    inputs["startstop"].value = 1
    inputs["startstop"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing next")
    inputs=Hsl3Slots(test_input)
    inputs["nextprev"].value = 1
    inputs["nextprev"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing prev")
    inputs=Hsl3Slots(test_input)
    inputs["nextprev"].value = 0
    inputs["nextprev"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing enabling shuffle")
    inputs=Hsl3Slots(test_input)
    inputs["shuffle"].value = True
    inputs["shuffle"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing disabling shuffle")
    inputs=Hsl3Slots(test_input)
    inputs["shuffle"].value = False
    inputs["shuffle"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing enabling repeat")
    inputs=Hsl3Slots(test_input)
    inputs["repeatall"].value = True
    inputs["repeatall"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing disabling repeat")
    inputs=Hsl3Slots(test_input)
    inputs["repeatall"].value = False
    inputs["repeatall"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing volume")
    inputs=Hsl3Slots(test_input)
    inputs["set_volume"].value = 55
    inputs["set_volume"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing volume")
    inputs=Hsl3Slots(test_input)
    inputs["set_volume"].value = 56
    inputs["set_volume"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing mute")
    inputs=Hsl3Slots(test_input)
    inputs["set_mute"].value = 1
    inputs["set_mute"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing unmute")
    inputs=Hsl3Slots(test_input)
    inputs["set_mute"].value = 0
    inputs["set_mute"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing pausing")
    inputs=Hsl3Slots(test_input)
    inputs["pauseplay"].value = 1
    inputs["pauseplay"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing resuming")
    inputs=Hsl3Slots(test_input)
    inputs["pauseplay"].value = 0
    inputs["pauseplay"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if True:
    print("Testing stopping")
    inputs=Hsl3Slots(test_input)
    inputs["startstop"].value = 0
    inputs["startstop"].changed = True
    module.on_calc(inputs)

    time.sleep(1)

if False:
    print("Testing setting input values again")
    inputs=Hsl3Slots(test_input)
    inputs["server_name"].changed = True
    module.on_calc(inputs)

time.sleep(10000)

#!/usr/bin/env python
# -*- coding: utf8 -*-

import time

from somfy import Remote


bedroom = Remote("bedroom")
bedroom.send_signal(Remote.SETUP_BTN)
time.sleep(5)
bedroom.send_signal(Remote.DOWN_BTN)

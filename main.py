#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
import time

from somfy import Remote


btn = {
"UP": Remote.UP_BTN,
"DOWN": Remote.DOWN_BTN,
"STOP": Remote.STOP_BTN,
"SETUP": Remote.SETUP_BTN
}

if len(sys.argv) == 3:
    rem = Remote(sys.argv[1])
    rem.send_signal(btn[sys.argv[2].upper()])

import time

TICK_RATE = 20  # server updates per second

def current_millis():
    return int(time.time() * 1000)

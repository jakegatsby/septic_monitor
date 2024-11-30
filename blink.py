from machine import Pin, Timer

LED = Pin("LED", machine.Pin.OUT)


def blink(timer):
    if LED.value() == 0:
        LED.on()
    else:
        LED.off()


timer = Timer()
timer.init(freq=5, mode=Timer.PERIODIC, callback=blink)

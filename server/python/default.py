import machine
from time import sleep
led1 = machine.Pin(17, machine.Pin.OUT)
led2 = machine.Pin(33, machine.Pin.OUT)
in1=machine.Pin(2, machine.Pin.IN)
while(1):
    led1.value(0)
    sleep(1)
    led2.value(1)
    sleep(1)
    led1.value(1)
    sleep(1)
    led2.value(0)
    sleep(1)
    print(in1.value())
    sleep(1)


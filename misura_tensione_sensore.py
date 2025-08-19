from machine import Pin, I2C
from ina219 import INA219
from time import sleep

i2c = I2C(scl=Pin(5), sda=Pin(4))  # D1, D2

ina = INA219(0.1, i2c)

# calcola calibrazione realistica
max_current = 1.0  # Ampere
current_lsb = max_current / 32768
calibration = int(0.04096 / (current_lsb * 0.1))

ina._current_lsb = current_lsb
ina._calibration_value = calibration

ina._configure()
ina._calibrate()

while True:
    print(f"Bus Voltage: {ina.voltage():.2f} V")
    print(f"Shunt Voltage: {ina.shunt_voltage():.2f} mV")
    print(f"Current: {ina.current():.2f} mA")
    print(f"Power: {ina.power():.2f} mW")
    print('-' * 20)
    sleep(1)



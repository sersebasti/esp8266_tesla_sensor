from time import sleep_us
from math import trunc

class INA219:
    REG_CONFIG = 0x00
    REG_SHUNT_VOLTAGE = 0x01
    REG_BUS_VOLTAGE = 0x02
    REG_POWER = 0x03
    REG_CURRENT = 0x04
    REG_CALIBRATION = 0x05

    SHUNT_LSB = 0.01         # mV per bit
    BUS_LSB = 0.004          # V per bit
    CALIBRATION_FACTOR = 0.04096

    def __init__(self, shunt_ohms, i2c, max_current=1.0, addr=0x40):
        self.i2c = i2c
        self.addr = addr
        self.shunt_ohms = shunt_ohms

        # calcola LSB e calibrazione
        self.current_lsb = max_current / 32768
        self.power_lsb = self.current_lsb * 20
        self.calibration = trunc(self.CALIBRATION_FACTOR / (self.current_lsb * shunt_ohms))

        self._configure()
        self._calibrate()

    def _write_reg(self, reg, value):
        msb = (value >> 8) & 0xFF
        lsb = value & 0xFF
        self.i2c.writeto_mem(self.addr, reg, bytes([msb, lsb]))

    def _read_reg(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2)
        val = (data[0] << 8) | data[1]
        if val > 32767:
            val -= 65536
        return val

    def _configure(self):
        # 32V bus, 320mV shunt, 12bit ADCs, continuous
        config = 0x019F
        self._write_reg(self.REG_CONFIG, config)

    def _calibrate(self):
        self._write_reg(self.REG_CALIBRATION, self.calibration)

    def voltage(self):
        val = self._read_reg(self.REG_BUS_VOLTAGE) >> 3
        return val * self.BUS_LSB

    def shunt_voltage(self):
        val = self._read_reg(self.REG_SHUNT_VOLTAGE)
        return val * self.SHUNT_LSB

    def current(self):
        val = self._read_reg(self.REG_CURRENT)
        return val * self.current_lsb * 1000  # mA

    def power(self):
        val = self._read_reg(self.REG_POWER)
        return val * self.power_lsb * 1000  # mW 
from machine import ADC
from time import sleep_us, sleep_ms
import math

adc = ADC(0)
VREF = 3.3
PARTITORE = 2  # fattore di correzione per il partitore

SAMPLES = 1000
INTERVAL_US = 200

# 🔷 Parametri calcolati durante la taratura
OFFSET_CALIBRATO = 2.675680     # [V]
SENSIBILITA_CALIBRATA = 0.074618  # [V/A]

def misura_vrms(offset):
    sum_sq = 0
    for _ in range(SAMPLES):
        raw = adc.read()
        volts = (raw / 1023) * VREF * PARTITORE
        deviation = volts - offset
        sum_sq += deviation ** 2
        sleep_us(INTERVAL_US)
    vrms = math.sqrt(sum_sq / SAMPLES)
    return vrms

print("\n🚀 Inizio misura continua...\n")

while True:
    vrms = misura_vrms(OFFSET_CALIBRATO)
    irms = max(vrms / SENSIBILITA_CALIBRATA, 0)
    print(f"📈 Corrente RMS: {irms:.3f} A | Offset: {OFFSET_CALIBRATO:.3f} V | Sensibilità: {SENSIBILITA_CALIBRATA:.6f} V/A")
    sleep_ms(1000)
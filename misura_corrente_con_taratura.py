from machine import ADC
from time import sleep_us, sleep_ms
import math

adc = ADC(0)
VREF = 3.3
PARTITORE = 2  # fattore di correzione per il partitore

SAMPLES = 1000
INTERVAL_US = 200

def misura_offset():
    sum_v = 0
    for _ in range(SAMPLES):
        raw = adc.read()
        volts = (raw / 1023) * VREF * PARTITORE
        sum_v += volts
        sleep_us(INTERVAL_US)
    offset = sum_v / SAMPLES
    print(f"📋 Offset reale: {offset:.3f} V")
    return offset

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

# 📋 Fase 1: misura OFFSET
print("👉 Lascia il cavo senza carico...")
sleep_ms(3000)
offset = misura_offset()

# 📋 Fase 2: misura baseline a vuoto
print("👉 Misuro rumore a vuoto...")
vrms_vuoto = misura_vrms(offset)
print(f"📋 Vrms a vuoto: {vrms_vuoto:.6f} V")

# 📋 Fase 3: misura con carico noto
input("👉 Collega un carico noto e premi invio...")
vrms_carico = misura_vrms(offset)
print(f"📋 Vrms con carico: {vrms_carico:.6f} V")

corrente_reale = float(input("✍️ Inserisci la corrente reale (A) misurata con la pinza: "))
sensibilita = (vrms_carico - vrms_vuoto) / corrente_reale

# 🔷 STAMPA PARAMETRI DEFINITIVI
print("\n✅ Parametri da usare nel codice finale:")
print(f"OFFSET_CALIBRATO = {offset:.6f}  # [V]")
print(f"SENSIBILITA_CALIBRATA = {sensibilita:.6f}  # [V/A]")

print("\n🚀 Inizio misura continua...\n")

# 📋 Fase 4: ciclo continuo
while True:
    vrms = misura_vrms(offset)
    irms = max((vrms - vrms_vuoto) / sensibilita, 0)
    print(f"📈 Corrente RMS: {irms:.3f} A | Offset: {offset:.3f} V | Sensibilità: {sensibilita:.6f} V/A")
    sleep_ms(1000)



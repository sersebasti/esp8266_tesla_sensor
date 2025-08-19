from machine import ADC
from time import sleep

adc = ADC(0)  # unico ADC disponibile

# se la tua scheda ha partitore integrato → fino a ~3.3 V
# se non ce l’ha → massimo 1.0 V sul pin

while True:
    raw = adc.read()  # 0–1023
    volts = raw / 1023  # normalizzato 0–1.0
    # se partitore: tensione massima 3.3 V
    volts_real = volts * 3.3  # cambia in 1.0 se scheda SENZA partitore

    print(f"ADC raw: {raw} → {volts_real:.2f} V")
    sleep(1)

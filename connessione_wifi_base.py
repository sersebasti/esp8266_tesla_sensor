import network
import time

ssid = "Vodafone-E34013225"
password = "Merca1!tello"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# disconnetti sempre prima
if wlan.isconnected():
    print("Disconnetto la vecchia connessione.")
    wlan.disconnect()
    time.sleep(1)

print("Connessione a:", ssid)
wlan.connect(ssid, password)

timeout = 15
while timeout > 0:
    if wlan.isconnected():
        break
    print(".", end="")
    time.sleep(1)
    timeout -= 1

if wlan.isconnected():
    print("\n✅ Connesso!")
    print("IP:", wlan.ifconfig()[0])
else:
    print("\n❌ Connessione fallita.")
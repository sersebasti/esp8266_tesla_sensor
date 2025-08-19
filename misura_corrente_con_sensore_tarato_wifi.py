import network
import time
import socket
import math
from machine import ADC, Pin
from time import sleep_us

# --- Config Wi-Fi ---
SSID = 'Vodafone-E34013225_EXT'
PASSWORD = 'Merca1!tello'

# --- Config ADC & Sensore Hall ---
adc = ADC(0)
VREF = 3.3
PARTITORE = 2  # se usi un partitore resistivo
SAMPLES = 1000
INTERVAL_US = 200

# Taratura sensore
OFFSET_CALIBRATO = 2.335    # [V]
SENSIBILITA_CALIBRATA = 0.065891  # [V/A]

# Token segreto per API
SECRET_TOKEN = "Merca10tello"


# --- Funzioni ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("🔌 Già connesso. Disconnetto...")
        wlan.disconnect()
        time.sleep(1)

    print(f"🌐 Connessione a: {ssid}")
    wlan.connect(ssid, password)

    timeout = 15
    while not wlan.isconnected() and timeout > 0:
        print(".", end="")
        time.sleep(1)
        timeout -= 1

    if wlan.isconnected():
        print("\n✅ Connesso!")
        print("IP:", wlan.ifconfig()[0])
    else:
        print("\n❌ Connessione fallita.")
        raise RuntimeError("Wi-Fi connection failed")


def misura_corrente_rms(offset):
    sum_sq = 0
    for _ in range(SAMPLES):
        raw = adc.read()
        volts = (raw / 1023) * VREF * PARTITORE
        deviation = volts - offset
        sum_sq += deviation ** 2
        sleep_us(INTERVAL_US)
    vrms = math.sqrt(sum_sq / SAMPLES)
    irms = max(vrms / SENSIBILITA_CALIBRATA, 0)
    return irms


def parse_request(request):
    try:
        first_line = request.decode().split("\r\n")[0]
        method, full_path, _ = first_line.split()
        if '?' in full_path:
            path, query = full_path.split('?', 1)
        else:
            path, query = '', ''
        return method, path, query
    except:
        return None, None, None


def parse_query(query):
    params = {}
    for part in query.split('&'):
        if '=' in part:
            k, v = part.split('=', 1)
            params[k] = v
    return params


def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('🌐 Listening on', addr)

    while True:
        cl, addr = s.accept()
        print('📥 Client connected from', addr)
        request = cl.recv(1024)
        print("Request:", request)

        method, path, query = parse_request(request)
        params = parse_query(query)

        # Default response
        response_code = '200 OK'
        content_type = 'application/json'
        response_body = '{"message": "default response"}'

        if path == '/status':
            token = params.get('token', '')
            if token != SECRET_TOKEN:
                response_code = '401 Unauthorized'
                response_body = '{"error": "Invalid token"}'
            else:
                irms = misura_corrente_rms(OFFSET_CALIBRATO)
                response_body = '{{"status": "ok", "message": "Authorized", "irms_A": {:.3f}}}'.format(irms)

        else:
            response_body = '{"error": "Not found"}'
            response_code = '404 Not Found'

        response = 'HTTP/1.1 {}\r\nContent-Type: {}\r\n\r\n{}'.format(
            response_code, content_type, response_body
        )
        cl.send(response)
        cl.close()


# --- MAIN ---
connect_wifi(SSID, PASSWORD)
start_server()

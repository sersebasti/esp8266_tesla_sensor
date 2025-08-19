import network
import time
import socket
import math
import ujson
import os
from machine import ADC
from time import sleep_us

# --- Config Wi-Fi ---
SSID = 'Vodafone-E34013225_EXT'
PASSWORD = 'Merca1!tello'

# --- ADC & Sensore ---
adc = ADC(0)
VREF = 3.3
PARTITORE = 2
SAMPLES = 1000
INTERVAL_US = 200

# --- File di configurazione ---
CONFIG_FILE = "config.json"
OFFSET_CALIBRATO = 2.335
SENSIBILITA_CALIBRATA = 0.065891

# --- File di log ---
LOG_FILE = "log.txt"
MAX_LOG_SIZE = 15 * 1024  # 15 KB

# --- Stato taratura temporaneo ---
offset_misurato = None
vrms_vuoto = None

# --- Funzioni di log ---
def log_event(msg):
    ts = time.localtime()
    line = "[{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}] {}\n".format(
        ts[0], ts[1], ts[2], ts[3], ts[4], ts[5], msg
    )
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
        # Controlla dimensione file
        if os.stat(LOG_FILE)[6] > MAX_LOG_SIZE:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-100:]  # tieni ultime 100 righe
            with open(LOG_FILE, "w") as f:
                f.writelines(lines)
    except Exception as e:
        print("Errore log:", e)

# --- Carica configurazione ---
def carica_config():
    global OFFSET_CALIBRATO, SENSIBILITA_CALIBRATA
    try:
        with open(CONFIG_FILE, "r") as f:
            cfg = ujson.load(f)
            OFFSET_CALIBRATO = cfg["offset"]
            SENSIBILITA_CALIBRATA = cfg["sensibilita"]
            print("✅ Configurazione caricata")
    except:
        print("⚠️ Nessun file di configurazione, uso valori di default")

# --- Salva configurazione ---
def salva_config(offset, sensibilita):
    try:
        with open(CONFIG_FILE, "w") as f:
            ujson.dump({"offset": offset, "sensibilita": sensibilita}, f)
        print("💾 Configurazione salvata")
        log_event(f"Salvata configurazione: offset={offset:.6f}, sensibilita={sensibilita:.6f}")
    except:
        print("❌ Errore nel salvataggio configurazione")

# --- Connessione Wi-Fi ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        wlan.disconnect()
        time.sleep(1)
    wlan.connect(ssid, password)
    timeout = 15
    while not wlan.isconnected() and timeout > 0:
        print(".", end="")
        time.sleep(1)
        timeout -= 1
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("\n✅ IP:", ip)
        log_event(f"Wi-Fi connesso: {ip}")
    else:
        raise RuntimeError("❌ Connessione Wi-Fi fallita")

def check_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        log_event("⚠️ Wi-Fi disconnesso, riconnessione...")
        connect_wifi(SSID, PASSWORD)

# --- Funzioni di misura ---
def misura_offset():
    sum_v = 0
    for _ in range(SAMPLES):
        raw = adc.read()
        volts = (raw / 1023) * VREF * PARTITORE
        sum_v += volts
        sleep_us(INTERVAL_US)
    return sum_v / SAMPLES

def misura_vrms(offset):
    sum_sq = 0
    for _ in range(SAMPLES):
        raw = adc.read()
        volts = (raw / 1023) * VREF * PARTITORE
        deviation = volts - offset
        sum_sq += deviation ** 2
        sleep_us(INTERVAL_US)
    return math.sqrt(sum_sq / SAMPLES)

def misura_corrente_rms(offset, sensibilita):
    vrms = misura_vrms(offset)
    return max(vrms / sensibilita, 0)

# --- Parser HTTP ---
def parse_request(request):
    try:
        first_line = request.decode().split("\r\n")[0]
        method, full_path, _ = first_line.split()
        if '?' in full_path:
            path, query = full_path.split('?', 1)
        else:
            path, query = full_path, ''
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

# --- Web server ---
def start_server():
    global OFFSET_CALIBRATO, SENSIBILITA_CALIBRATA
    global offset_misurato, vrms_vuoto

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.settimeout(2)  # timeout accettazione
    s.bind(addr)
    s.listen(1)
    print('🌐 Server attivo su http://{}/'.format(addr[0]))
    log_event("Server avviato")

    while True:
        check_wifi()
        try:
            cl, addr = s.accept()
            cl.settimeout(2)  # timeout ricezione
            request = cl.recv(1024)
            method, path, query = parse_request(request)
            params = parse_query(query)

            log_event(f"Richiesta da {addr}: {path} {query}")

            response_code = '200 OK'
            content_type = 'application/json'
            response_body = '{"message": "default response"}'

            if path == '/status':
                irms = misura_corrente_rms(OFFSET_CALIBRATO, SENSIBILITA_CALIBRATA)
                response_body = '{{"status": "ok", "name": "tesla_esp","irms_A": {:.3f}}}'.format(irms)

            elif path == '/tuning':
                amp = params.get('amp', None)

                if amp is None:
                    offset_misurato = misura_offset()
                    vrms_vuoto = misura_vrms(offset_misurato)
                    response_body = '{{"step": 1, "offset_V": {:.6f}, "vrms_vuoto_V": {:.6f}}}'.format(
                        offset_misurato, vrms_vuoto)
                else:
                    try:
                        corrente = float(amp)
                        vrms_carico = misura_vrms(offset_misurato)
                        sensibilita = (vrms_carico - vrms_vuoto) / corrente
                        OFFSET_CALIBRATO = offset_misurato
                        SENSIBILITA_CALIBRATA = sensibilita
                        salva_config(OFFSET_CALIBRATO, SENSIBILITA_CALIBRATA)
                        response_body = '{{"step": 2, "offset_V": {:.6f}, "sensibilita_V_per_A": {:.6f}}}'.format(
                            OFFSET_CALIBRATO, SENSIBILITA_CALIBRATA)
                    except:
                        response_code = '400 Bad Request'
                        response_body = '{"error": "Parametro amp non valido"}'
            else:
                response_code = '404 Not Found'
                response_body = '{"error": "Endpoint non trovato"}'

            response = 'HTTP/1.1 {}\r\nContent-Type: {}\r\n\r\n{}'.format(
                response_code, content_type, response_body)
            cl.send(response)
            cl.close()

        except OSError:
            pass
        except Exception as e:
            log_event(f"Errore server: {e}")

# --- MAIN ---
carica_config()
connect_wifi(SSID, PASSWORD)
start_server()

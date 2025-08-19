import network
import time
import socket
from machine import ADC

adc = ADC(0)  # oppure ADC() su firmware recenti
VREF = 3.3  

def leggi_adc():
    return adc.read()



# Config Wi-Fi
ssid = 'Vodafone-E34013225_EXT'
password = 'Merca1!tello'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if wlan.isconnected():
    print("Disconnetto la vecchia connessione.")
    wlan.disconnect()
    time.sleep(1)

print("Connecting to", ssid)
wlan.connect(ssid, password)

timeout = 15
while not wlan.isconnected() and timeout > 0:
    print(".", end="")
    time.sleep(1)
    timeout -= 1

if wlan.isconnected():
    print("\n✅ Connected!")
    print("IP address:", wlan.ifconfig()[0])
else:
    print("\n❌ Failed to connect.")
    raise RuntimeError("Wi-Fi connection failed")

# Token segreto
SECRET_TOKEN = "Merca10tello"

def parse_request(request):
    """Estrae metodo, path e querystring"""
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
    """Converte la querystring in dict"""
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
                adc_val = leggi_adc()
                volts = round((adc_val / 1023) * VREF, 3)
                response_body = '{{"status": "ok", "message": "Authorized", "adc_raw": {}, "volts": {}}}'.format(adc_val, volts)
        
        else:
            response_body = '{"error": "Not found"}'
            response_code = '404 Not Found'

        response = 'HTTP/1.1 {}\r\nContent-Type: {}\r\n\r\n{}'.format(
            response_code, content_type, response_body
        )
        cl.send(response)
        cl.close()

start_server()
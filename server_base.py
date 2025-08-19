import socket

def start_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)

    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        request = cl.recv(1024)
        print("Request:", request)

        # Risposta JSON
        response = 'HTTP/1.1 200 OK\r\n'
        response += 'Content-Type: application/json\r\n\r\n'
        response += '{"status":"ok", "message":"Hello from ESP8266!"}'

        cl.send(response)
        cl.close()

start_server()
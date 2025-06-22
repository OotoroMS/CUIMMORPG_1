import socket
import threading
import sys

END_MARK = '\n'

def recv_loop(sock):
    try:
        buf = b''
        while True:
            data = sock.recv(1024)
            if not data:
                print('\n[サーバとの接続が切断されました]')
                break
            buf += data
            while END_MARK.encode() in buf:
                line, buf = buf.split(END_MARK.encode(), 1)
                print(line.decode('utf-8'))
    except OSError:
        pass

def main(host='127.0.0.1', port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    thread = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    thread.start()
    try:
        while True:
            try:
                line = input()
            except EOFError:
                break
            sock.sendall((line + END_MARK).encode('utf-8'))
    finally:
        sock.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Simple RPG Client')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    main(args.host, args.port)

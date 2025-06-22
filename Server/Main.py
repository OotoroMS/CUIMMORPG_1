import socket
import threading
import json

MAX_PLAYERS = 16
MAX_PARTY_SIZE = 4
JOBS = ['\u6226\u58eb', '\u795e\u5b98', '\u9b54\u6cd5\u4f7f\u3044', '\u9b54\u6cd5\u6226\u58eb', '\u76d7\u8cca']

BASE_STATS = {
    '\u6226\u58eb':    {'HP': 30, 'MP': 5, '攻撃力': 8, '守備力': 8, '素早さ': 5, '魔法攻撃': 2, '魔法防御': 3, '運': 5},
    '\u795e\u5b98':    {'HP': 20, 'MP': 15, '攻撃力': 4, '守備力': 4, '素早さ': 4, '魔法攻撃': 6, '魔法防御': 6, '運': 5},
    '\u9b54\u6cd5\u4f7f\u3044': {'HP': 18, 'MP': 20, '攻撃力': 3, '守備力': 3, '素早さ': 5, '魔法攻撃': 8, '魔法防御': 5, '運': 5},
    '\u9b54\u6cd5\u6226\u58eb': {'HP': 25, 'MP': 10, '攻撃力': 6, '守備力': 6, '素早さ': 6, '魔法攻撃': 4, '魔法防御': 4, '運': 5},
    '\u76d7\u8cca':    {'HP': 22, 'MP': 8, '攻撃力': 5, '守備力': 4, '素早さ': 8, '魔法攻撃': 3, '魔法防御': 3, '運': 7},
}

players = {}
lock = threading.Lock()

class Player:
    def __init__(self, conn, addr, name, job):
        self.conn = conn
        self.addr = addr
        self.name = name
        self.job = job
        self.level = 1
        self.stats = BASE_STATS[job].copy()
        self.party = None

    def to_dict(self):
        return {
            'name': self.name,
            'job': self.job,
            'level': self.level,
            'stats': self.stats,
        }

def send(conn, msg):
    conn.sendall((msg + '\n').encode('utf-8'))

def recv(conn):
    data = b''
    while not data.endswith(b'\n'):
        chunk = conn.recv(1024)
        if not chunk:
            return None
        data += chunk
    return data.decode('utf-8').rstrip('\n')

def handle_town(player):
    conn = player.conn
    while True:
        menu = (
            '\n-- \u8857 --\n'
            '1) \u9053\u5177\u5c4b\n'
            '2) \u6b66\u5668\u9632\u5177\u5c4b\n'
            '3) \u30a2\u30af\u30bb\u30b5\u30ea\u30fc\u5c4b\n'
            '4) \u9b54\u6cd5\u5c4b\n'
            '5) \u9152\u5834(\u30de\u30c3\u30c1\u7528\u30ed\u30d3\u30fc)\n'
            '0) \u623b\u308b\n> '
        )
        send(conn, menu)
        choice = recv(conn)
        if choice is None or choice == '0':
            return
        else:
            send(conn, '\u73fe\u5728\u306f\u5229\u7528\u3067\u304d\u307e\u305b\u3093')

def handle_dungeon(player):
    conn = player.conn
    send(conn, '\n-- \u30c0\u30f3\u30b8\u30e7\u30f3 --')
    send(conn, '\u30c0\u30f3\u30b8\u30e7\u30f3\u3092\u63a2\u7d22\u3057\u3001\u5e30\u3063\u3066\u304d\u307e\u3057\u305f\u3002')

def show_status(player):
    conn = player.conn
    status = json.dumps(player.to_dict(), ensure_ascii=False, indent=2)
    send(conn, status)

def handle_client(conn, addr):
    try:
        send(conn, 'ようこそ！ 名前を入力してください:')
        name = recv(conn)
        if not name:
            conn.close()
            return
        job_menu = '\n'.join(f'{i}) {job}' for i, job in enumerate(JOBS)) + '\n職業を選んでください:'
        send(conn, job_menu)
        job_index = recv(conn)
        if job_index is None:
            conn.close()
            return
        try:
            job = JOBS[int(job_index)]
        except (ValueError, IndexError):
            send(conn, '不正な入力です')
            conn.close()
            return
        player = Player(conn, addr, name, job)
        with lock:
            if len(players) >= MAX_PLAYERS:
                send(conn, 'サーバが満員です')
                conn.close()
                return
            players[conn] = player
        send(conn, f'{name} としてログインしました。')
        while True:
            menu = (
                '\n-- メインメニュー --\n'
                '1) 街\n'
                '2) ダンジョン\n'
                '3) ステータス\n'
                '4) 終了\n> '
            )
            send(conn, menu)
            cmd = recv(conn)
            if cmd is None or cmd == '4':
                break
            elif cmd == '1':
                handle_town(player)
            elif cmd == '2':
                handle_dungeon(player)
            elif cmd == '3':
                show_status(player)
            else:
                send(conn, '不明なコマンドです')
    finally:
        with lock:
            players.pop(conn, None)
        conn.close()

def main(host='0.0.0.0', port=5000):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen()
    print(f'Server start on {host}:{port}')
    try:
        while True:
            conn, addr = srv.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    finally:
        srv.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Simple RPG Server')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    main(args.host, args.port)

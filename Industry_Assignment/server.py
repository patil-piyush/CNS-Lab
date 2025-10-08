import socket
import struct
import json
import os

HOST = '127.0.0.1'
PORT = 5555
MAX_BALANCE = 65535
PLAYER_FILE = 'players.json'

# Load or initialize players
if os.path.exists(PLAYER_FILE):
    with open(PLAYER_FILE, 'r') as f:
        players = json.load(f)
else:
    players = {}

SHOP_ITEMS = {
    "Health Potion": 200,
    "Sword": 500,
    "Shield": 300,
    "Legendary Armor": 1000
}

def save_players():
    with open(PLAYER_FILE, 'w') as f:
        json.dump(players, f)

def process_instruction(username, instr, amount):
    balance = players[username]
    if instr == b'CR':
        if balance + amount <= MAX_BALANCE:
            balance += amount
            players[username] = balance
            return b'BA', balance
        else:
            return b'ER', 0
    elif instr == b'DB':
        if balance >= amount:
            balance -= amount
            players[username] = balance
            return b'BA', balance
        else:
            return b'ER', 0
    else:
        return b'ER', 0

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Gaming Coin Wallet Server running on {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            try:
                while True:  # Main menu loop
                    # Send main menu
                    conn.sendall(b"MAIN_MENU")
                    main_choice = conn.recv(1024).decode().strip().upper()
                    if not main_choice or main_choice == 'X':
                        conn.sendall(b"EXIT")
                        print(f"Client {addr} exited.")
                        break

                    if main_choice not in ['E', 'N']:
                        conn.sendall(b"INVALID_MENU")
                        continue

                    # Username handling
                    while True:
                        prompt = b"USERNAME?" if main_choice == 'E' else b"NEW_USERNAME?"
                        conn.sendall(prompt)
                        username = conn.recv(1024).decode().strip()
                        if main_choice == 'E':
                            if username in players:
                                balance = players[username]
                                conn.sendall(f"Welcome back, {username}! Balance: {balance} coins\n".encode())
                                break
                            else:
                                conn.sendall(b"User not found. Try again.")
                        else:
                            if username not in players:
                                players[username] = 1000
                                save_players()
                                conn.sendall(f"Account created! Welcome, {username}! Balance: 1000 coins\n".encode())
                                break
                            else:
                                conn.sendall(b"Username exists. Try another.")

                    # Transaction loop
                    while True:
                        data = conn.recv(4)
                        if not data or len(data) != 4:
                            continue
                        instr, amount = struct.unpack('>2sH', data)
                        if instr == b'LO':  # Logout
                            print(f"{username} logged out.")
                            break
                        code, new_balance = process_instruction(username, instr, amount)
                        conn.sendall(struct.pack('>2sH', code, new_balance))
                        if code == b'BA':
                            print(f"{username}: Transaction successful. New Balance: {new_balance}")
                        else:
                            print(f"{username}: Transaction failed. Balance: {players[username]}")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                save_players()
                conn.close()
                print(f"Connection with {addr} closed.")

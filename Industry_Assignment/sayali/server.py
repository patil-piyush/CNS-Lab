"""
FASTag Server
- Listens on 127.0.0.1:5555
- Persistent balances in users.json (vehicle reg -> balance)
- Protocol:
  * Handshake (text): MAIN_MENU, USERNAME?/NEW_USERNAME?, welcome messages
  * Transactions (binary 4 bytes): struct.pack('>2sH', instr, amount)
    instr: b'CR' (recharge), b'DB' (deduct toll), b'LO' (logout)
    response: b'BA' (balance) or b'ER' (error) + 2-byte value
"""

import socket
import struct
import json
import os

HOST = '127.0.0.1'
PORT = 5555
USER_FILE = 'users.json'
MAX_BALANCE = 65535
INITIAL_BALANCE = 1000  # starting balance for new vehicles

# Preset toll categories (must match client)
TOLL_RATES = {
    "1": ("Car", 100),
    "2": ("Truck", 250),
    "3": ("Bus", 200),
    "4": ("Multi-axle", 400)
}

# Load or initialize users data
if os.path.exists(USER_FILE):
    with open(USER_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    """Persist users dict to JSON file."""
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

def process_instruction(vehicle_id, instr, amount):
    """Apply CR/DB for vehicle_id. Return (code_bytes, value_int)."""
    balance = users[vehicle_id]
    if instr == b'CR':  # Recharge
        if balance + amount <= MAX_BALANCE:
            balance += amount
            users[vehicle_id] = balance
            return b'BA', balance
        else:
            return b'ER', 0
    elif instr == b'DB':  # Toll deduction
        if balance >= amount:
            balance -= amount
            users[vehicle_id] = balance
            return b'BA', balance
        else:
            return b'ER', 0
    else:
        return b'ER', 0

def handle_client(conn, addr):
    """Handle a single client connection (sequential server)."""
    print(f"[+] Connected by {addr}")
    try:
        while True:
            # Prompt client to show main menu
            conn.sendall(b"MAIN_MENU")
            choice_bytes = conn.recv(1024)
            if not choice_bytes:
                # client disconnected
                print(f"[-] Client {addr} disconnected during main menu")
                break
            main_choice = choice_bytes.decode().strip().upper()
            if main_choice == 'X':
                conn.sendall(b"EXIT")
                print(f"[+] Client {addr} requested exit")
                break
            if main_choice not in ('E', 'N'):
                conn.sendall(b"INVALID_MENU")
                continue

            # Username / vehicle registration handshake
            while True:
                prompt = b"USERNAME?" if main_choice == 'E' else b"NEW_USERNAME?"
                conn.sendall(prompt)
                uname_bytes = conn.recv(1024)
                if not uname_bytes:
                    # client disconnected
                    print(f"[-] Client {addr} disconnected during username prompt")
                    return
                vehicle_id = uname_bytes.decode().strip()
                if main_choice == 'E':
                    if vehicle_id in users:
                        bal = users[vehicle_id]
                        conn.sendall(f"Welcome back, {vehicle_id}! Balance: {bal} coins (₹{bal})\n".encode())
                        break
                    else:
                        conn.sendall(b"User not found. Try again.")
                else:  # new registration
                    if vehicle_id in users:
                        conn.sendall(b"Username exists. Try another.")
                    else:
                        users[vehicle_id] = INITIAL_BALANCE
                        save_users()
                        bal = users[vehicle_id]
                        conn.sendall(f"Account created! Vehicle {vehicle_id} registered. Balance: {bal} coins (₹{bal})\n".encode())
                        break

            # Transaction loop (expect binary 4-byte messages)
            while True:
                data = conn.recv(4)
                if not data or len(data) != 4:
                    # ignore and wait for proper 4-byte packet
                    continue
                instr, amount = struct.unpack('>2sH', data)

                # Logout special signal
                if instr == b'LO':
                    print(f"[+] {vehicle_id} logged out")
                    break

                # Process CR / DB
                code, new_balance = process_instruction(vehicle_id, instr, amount)
                # send response
                conn.sendall(struct.pack('>2sH', code, new_balance))
                if code == b'BA':
                    print(f"[TX] {vehicle_id}: {instr.decode()} {amount} => New balance ₹{new_balance}")
                else:
                    print(f"[TX] {vehicle_id}: {instr.decode()} {amount} => FAILED (Balance ₹{users[vehicle_id]})")

    except Exception as ex:
        print(f"[!] Error with client {addr}: {ex}")
    finally:
        save_users()
        try:
            conn.close()
        except Exception:
            pass
        print(f"[-] Connection with {addr} closed")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"FASTag Server running on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FASTag Client
- Connects to local FASTag server
- Preset toll categories (Car/Truck/Bus/Multi-axle)
- Recharge (CR), Deduct toll (DB), Logout (LO)
"""

import socket
import struct

HOST = '127.0.0.1'
PORT = 5555

TOLL_RATES = {
    "1": ("Car", 100),
    "2": ("Truck", 250),
    "3": ("Bus", 200),
    "4": ("Multi-axle", 400)
}

INITIAL_BALANCE_DISPLAY = "₹"  # currency symbol for display

def main_menu():
    print("\n🚗 === FASTag MAIN MENU ===")
    print("E - Existing Vehicle (Login)")
    print("N - New Vehicle Registration")
    print("X - Exit")
    return input("Choose option: ").strip().upper()

def fastag_menu(vehicle_id, balance):
    print(f"\n🚦 Vehicle: {vehicle_id} | Balance: {balance} coins ({INITIAL_BALANCE_DISPLAY}{balance})")
    print("1. Recharge FASTag")
    print("2. Pass Toll (choose preset)")
    print("3. Logout")
    return input("Choose option: ").strip()

def show_toll_presets():
    print("\n💳 Toll Presets:")
    for k, (name, price) in TOLL_RATES.items():
        print(f"{k}. {name} - ₹{price}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"[+] Connected to FASTag server at {HOST}:{PORT}")

        while True:
            # Wait for server main-menu prompt
            _ = s.recv(1024).decode()  # expect MAIN_MENU token
            choice = main_menu()
            s.sendall(choice.encode())
            if choice == 'X':
                print("Exiting client. Goodbye!")
                break
            if choice not in ('E', 'N'):
                print("Invalid option locally; try again.")
                continue

            # Vehicle ID handshake
            while True:
                prompt = s.recv(1024).decode()  # USERNAME? or NEW_USERNAME?
                vehicle_id = input(prompt + " ").strip()
                s.sendall(vehicle_id.encode())
                response = s.recv(1024).decode()
                print(response)
                if "Balance" in response:
                    # parse numeric balance (first integer after "Balance:")
                    try:
                        balance = int(response.split("Balance:")[1].split()[0])
                    except Exception:
                        balance = 0
                    break

            # Transaction loop for this vehicle_id
            while True:
                opt = fastag_menu(vehicle_id, balance)
                if opt == '1':  # Recharge FASTag
                    try:
                        amt = int(input("Enter recharge amount (0-65535): ").strip())
                    except ValueError:
                        print("Invalid amount. Enter an integer.")
                        continue
                    if not (0 <= amt <= 65535):
                        print("Amount out of range.")
                        continue
                    s.sendall(struct.pack('>2sH', b'CR', amt))
                elif opt == '2':  # Pass Toll (preset)
                    show_toll_presets()
                    sel = input("Choose vehicle category number: ").strip()
                    if sel not in TOLL_RATES:
                        print("Invalid selection.")
                        continue
                    _, fee = TOLL_RATES[sel]
                    print(f"Passing toll for {TOLL_RATES[sel][0]} — ₹{fee}. Sending payment...")
                    s.sendall(struct.pack('>2sH', b'DB', fee))
                elif opt == '3':  # Logout
                    s.sendall(struct.pack('>2sH', b'LO', 0))
                    print(f"{vehicle_id} logged out. Returning to main menu...")
                    break
                else:
                    print("Invalid option.")
                    continue

                # Receive 4-byte server response
                data = s.recv(4)
                if len(data) != 4:
                    print("Invalid server response. Ending session.")
                    break
                code, value = struct.unpack('>2sH', data)
                if code == b'BA':
                    balance = value
                    print(f"Success — New Balance: ₹{balance}")
                else:
                    print("Operation failed: insufficient balance or invalid operation.")

        # socket closes automatically here

if __name__ == "__main__":
    main()

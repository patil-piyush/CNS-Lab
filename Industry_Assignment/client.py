import socket
import struct

HOST = '127.0.0.1'
PORT = 5555

SHOP_ITEMS = {
    "1": ("Health Potion", 200),
    "2": ("Sword", 500),
    "3": ("Shield", 300),
    "4": ("Legendary Armor", 1000)
}

def main_menu():
    print("\n=== MAIN MENU ===")
    print("E - Login as Existing User")
    print("N - Create New User")
    print("X - Exit")
    return input("Choose option: ").strip().upper()

def transaction_menu(username, balance):
    print(f"\nHello, {username}! Balance: {balance} coins")
    print("1. Earn Coins")
    print("2. Buy Item (Shop)")
    print("3. Logout")
    return input("Choose option: ").strip()

def show_shop():
    print("\nWelcome to the Shop! Items available:")
    for key, (name, price) in SHOP_ITEMS.items():
        print(f"{key}. {name} - {price} coins")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        running = True
        while running:
            # Receive main menu
            s.recv(1024)  # just to sync with server
            choice = main_menu()
            s.sendall(choice.encode())
            if choice == 'X':
                print("Exiting... Goodbye!")
                break
            elif choice not in ['E', 'N']:
                print("Invalid option, try again.")
                continue

            # Username handling
            while True:
                prompt = s.recv(1024).decode()
                username = input(prompt + " ").strip()
                s.sendall(username.encode())
                response = s.recv(1024).decode()
                print(response)
                if "Balance" in response:
                    balance = int(response.split("Balance:")[1].split()[0])
                    break

            # Transaction loop
            transaction_active = True
            while transaction_active:
                option = transaction_menu(username, balance)

                if option == '1':
                    print("\nCaptcha Challenge: Prove you're human to earn coins!")
                    s.sendall(struct.pack('>2sH', b'CP', 0))

                    # Receive captcha from server
                    captcha_msg = s.recv(1024).decode()
                    if not captcha_msg.startswith("CAPTCHA:"):
                        print("Error: No captcha received.")
                        continue
                    captcha = captcha_msg.split(":")[1]
                    print(f"Captcha: {captcha}")

                    # Get user answer
                    user_answer = input("Enter captcha: ").strip()
                    s.sendall(user_answer.encode())

                    # Receive server response
                    data = s.recv(4)
                    if len(data) != 4:
                        print("Invalid server response")
                        continue

                    code, value = struct.unpack('>2sH', data)
                    if code == b'BA':
                        balance = value
                        print(f"✅ Correct! You earned coins. New Balance: {balance} coins")
                    else:
                        print("❌ Incorrect captcha. No coins awarded.")
                    continue  # Return to transaction menu

                elif option == '2':
                    show_shop()
                    item_choice = input("Choose item number to buy: ").strip()
                    if item_choice in SHOP_ITEMS:
                        _, price = SHOP_ITEMS[item_choice]
                        s.sendall(struct.pack('>2sH', b'DB', price))
                    else:
                        print("Invalid choice!")
                        continue

                elif option == '3':
                    s.sendall(struct.pack('>2sH', b'LO', 0))
                    print(f"{username} logged out. Returning to main menu...")
                    transaction_active = False
                    break

                else:
                    print("Invalid option!")
                    continue

                # Receive server response for shop purchase
                data = s.recv(4)
                if len(data) != 4:
                    print("Invalid server response")
                    transaction_active = False
                    break
                code, value = struct.unpack('>2sH', data)
                if code == b'BA':
                    balance = value
                    print(f"New Balance: {balance} coins")
                else:
                    print("Transaction failed!")

if __name__ == "__main__":
    main()

# RSA Algorithm Implementation (Automatic e Selection)

from math import gcd

def mod_inverse(e, phi):
    """Compute modular inverse of e mod phi using Extended Euclidean Algorithm."""
    def egcd(a, b):
        if b == 0:
            return a, 1, 0
        else:
            g, x, y = egcd(b, a % b)
            return g, y, x - (a // b) * y

    g, x, y = egcd(e, phi)
    if g != 1:
        raise Exception("Modular inverse does not exist")
    else:
        return x % phi


# ----------- MAIN PROGRAM -----------

print("------- RSA Algorithm Implementation -------")

# Input primes
p = int(input("Enter first prime number (p): "))
q = int(input("Enter second prime number (q): "))

if p <= 1 or q <= 1:
    print("p and q must be > 1.")
    exit()

# n and phi
n = p * q
phi = (p - 1) * (q - 1)

print(f"\nn = p * q = {n}")
print(f"phi(n) = (p-1)*(q-1) = {phi}")

# Automatically choose e: smallest integer >1 with gcd(e, phi) = 1
e = 2
while e < phi:
    if gcd(e, phi) == 1:
        break
    e += 1

if gcd(e, phi) != 1:
    print("Failed to find suitable e. Choose different primes.")
    exit()

# Calculate d = e^(-1) mod phi
try:
    d = mod_inverse(e, phi)
except Exception as ex:
    print("Error:", ex)
    exit()

print(f"\nAutomatically chosen e = {e}")
print(f"Calculated d = {d}")
print(f"Public Key (e, n) = ({e}, {n})")
print(f"Private Key (d, n) = ({d}, {n})")

# Input message
msg = int(input("\nEnter the message (as integer, 0 < m < n): "))
if msg <= 0 or msg >= n:
    print("Message must be in range 1 .. n-1.")
    exit()

# Encryption: c = m^e mod n
cipher = pow(msg, e, n)
print(f"Encrypted Ciphertext = {cipher}")

# Decryption: m = c^d mod n
plain = pow(cipher, d, n)
print(f"Decrypted Message = {plain}")

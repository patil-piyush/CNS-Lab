# Playfair Cipher Implementation with User Input

def generate_key_matrix(key):
    key = key.upper().replace("J", "I")  # Treat I and J as same
    matrix = []
    used = set()

    for char in key:
        if char.isalpha() and char not in used:
            matrix.append(char)
            used.add(char)

    for char in "ABCDEFGHIKLMNOPQRSTUVWXYZ":  # J excluded
        if char not in used:
            matrix.append(char)

    return [matrix[i:i+5] for i in range(0, 25, 5)]


def find_position(matrix, letter):
    for i in range(5):
        for j in range(5):
            if matrix[i][j] == letter:
                return i, j
    return None


def prepare_text(text):
    text = text.upper().replace("J", "I")
    text = "".join([c for c in text if c.isalpha()])

    prepared = ""
    i = 0
    while i < len(text):
        a = text[i]
        b = ''
        if i + 1 < len(text):
            b = text[i + 1]
        else:
            b = 'X'

        if a == b:
            prepared += a + 'X'
            i += 1
        else:
            prepared += a + b
            i += 2

    if len(prepared) % 2 != 0:
        prepared += 'X'

    return prepared


def encrypt_pair(a, b, matrix):
    row1, col1 = find_position(matrix, a)
    row2, col2 = find_position(matrix, b)

    if row1 == row2:
        return matrix[row1][(col1 + 1) % 5] + matrix[row2][(col2 + 1) % 5]
    elif col1 == col2:
        return matrix[(row1 + 1) % 5][col1] + matrix[(row2 + 1) % 5][col2]
    else:
        return matrix[row1][col2] + matrix[row2][col1]


def decrypt_pair(a, b, matrix):
    row1, col1 = find_position(matrix, a)
    row2, col2 = find_position(matrix, b)

    if row1 == row2:
        return matrix[row1][(col1 - 1) % 5] + matrix[row2][(col2 - 1) % 5]
    elif col1 == col2:
        return matrix[(row1 - 1) % 5][col1] + matrix[(row2 - 1) % 5][col2]
    else:
        return matrix[row1][col2] + matrix[row2][col1]


def encrypt(text, key):
    matrix = generate_key_matrix(key)
    text = prepare_text(text)
    cipher = ""
    for i in range(0, len(text), 2):
        cipher += encrypt_pair(text[i], text[i + 1], matrix)
    return cipher


def decrypt(cipher, key):
    matrix = generate_key_matrix(key)
    text = ""
    for i in range(0, len(cipher), 2):
        text += decrypt_pair(cipher[i], cipher[i + 1], matrix)
    return text


# ----------- MAIN PROGRAM -----------

key = input("Enter the key: ")
plaintext = input("Enter the plaintext: ")

ciphertext = encrypt(plaintext, key)
decrypted_text = decrypt(ciphertext, key)

print("\n--- PLAYFAIR CIPHER ---")
print("Key Matrix:")
for row in generate_key_matrix(key):
    print(row)

print("\nPlaintext:", plaintext.upper())
print("Ciphertext:", ciphertext)
print("Decrypted Text:", decrypted_text)

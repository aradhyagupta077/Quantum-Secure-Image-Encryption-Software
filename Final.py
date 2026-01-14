from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from PIL import Image
import numpy as np
import random
import string

# ======== QKD Simulation (BB84) ========
def qkd_key_generation(key_length=8, seed=None):
    if seed is not None:
        random.seed(seed)  

    alice_bits = [random.randint(0, 1) for _ in range(key_length)]
    alice_bases = [random.choice(['Z', 'X']) for _ in range(key_length)]
    bob_bases = [random.choice(['Z', 'X']) for _ in range(key_length)]

    qc_list = []
    for bit, base in zip(alice_bits, alice_bases):
        qc = QuantumCircuit(1, 1)
        if bit == 1:
            qc.x(0)
        if base == 'X':
            qc.h(0)
        qc_list.append(qc)

    simulator = AerSimulator()
    bob_results = []
    for qc, bob_base in zip(qc_list, bob_bases):
        new_qc = qc.copy()
        if bob_base == 'X':
            new_qc.h(0)
        new_qc.measure(0, 0)
        t_qc = transpile(new_qc, simulator)
        result = simulator.run(t_qc, shots=1).result()
        measured_bit = int(list(result.get_counts().keys())[0])
        bob_results.append(measured_bit)

    shared_key = [a for a, ab, bb in zip(alice_bits, alice_bases, bob_bases) if ab == bb]
    if len(shared_key) == 0:
        shared_key = [random.randint(0, 1) for _ in range(key_length // 2)]

    key_int = int(''.join(map(str, shared_key)), 2)
    return key_int


# ======== Encryption ========
def encrypt_image(image_path, message):
    img = Image.open(image_path).convert('RGB')
    pixels = np.array(img)

    key = qkd_key_generation(seed=len(message))  # Deterministic for given length
    print(f"Quantum Key generated: {key}")

    binary_msg = ''.join(format(ord(ch), '08b') for ch in message)
    msg_len = len(binary_msg)

    flat_pixels = pixels.flatten()
    for i in range(msg_len):
        flat_pixels[i] = (flat_pixels[i] & 0b11111110) | ((int(binary_msg[i]) ^ (key & 1)) & 1)

    new_pixels = flat_pixels.reshape(pixels.shape)
    new_img = Image.fromarray(new_pixels.astype('uint8'))
    new_img.save("encrypted_image.png")
    print("Message encrypted successfully! Saved as encrypted_image.png")

# ======== Decryption ========
def decrypt_image(image_path, msg_length=100):
    img = Image.open(image_path).convert('RGB')
    pixels = np.array(img).flatten()

    key = qkd_key_generation(seed=msg_length)
    print(f"Quantum Key regenerated: {key}")

    total_bits = msg_length * 8
    if total_bits > len(pixels):
        print("Error: Message length exceeds image capacity.")
        return

    extracted_bits = [(pix & 1) ^ (key & 1) for pix in pixels[:total_bits]]

    chars = []
    for i in range(0, len(extracted_bits), 8):
        byte = extracted_bits[i:i+8]
        if len(byte) < 8:
            break
        char = chr(int(''.join(map(str, byte)), 2))
        chars.append(char)

    message = ''.join(chars).rstrip('\x00')

    if not message or any(c not in string.printable for c in message):
        print("********")
    else:
        printable_ratio = sum(c.isprintable() for c in message) / len(message)
        if printable_ratio < 0.9:
            print("********")
        else:
            print("Decrypted Message:", message)


# ======== Main Menu ========
def main():
    print("\nQuantum Cryptography Image Encryption Model")
    print("1. Encrypt a message into image")
    print("2. Decrypt a message from image")
    choice = input("Enter choice (1/2): ")

    if choice == '1':
        img_path = input("Enter image file path (PNG/BMP): ")
        msg = input("Enter message to encrypt: ")
        msg_len = len(msg)
        encrypt_image(img_path, msg)
        print("The original message length (characters) is:", msg_len)

    elif choice == '2':
        img_path = input("Enter encrypted image file path: ")
        msg_len = int(input("Enter original message length (characters): "))
        decrypt_image(img_path, msg_len)

    else:
        print("Invalid choice! Exiting...")

main()

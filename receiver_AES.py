import socket
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import base64

app = Flask(__name__)

def key_exchange(private_key, peer_public_key):
    # Perform key exchange
    shared_key = private_key.exchange(peer_public_key)
    
    # Derive symmetric key from shared key using HKDF
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # Length of the derived key
        salt=None,
        info=b'ECDH Key Derivation',
        backend=default_backend()
    ).derive(shared_key)
    
    return derived_key

def decrypt_message(ciphertext, key):
    # Split IV and ciphertext
    iv = ciphertext[:16]
    ciphertext = ciphertext[16:]
    
    # Create a cipher object
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    
    # Decrypt the ciphertext
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Unpad the decrypted data
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(decrypted_data) + unpadder.finalize()
    
    return plaintext.decode()

@app.route('/deviceA/send_message', methods=['POST'])
def receive_message():
    data = request.json
    encrypted_message = base64.b64decode(data['message'])
    private_key_bytes = base64.b64decode(data['private_key'])
    peer_public_key_bytes = base64.b64decode(data['peer_public_key'])
    
    # Deserialize the private and peer public keys
    private_key = serialization.load_der_private_key(
        private_key_bytes,
        password=None,
        backend=default_backend()
    )
    peer_public_key = serialization.load_der_public_key(
        peer_public_key_bytes,
        backend=default_backend()
    )
    
    # Write encrypted message to encrypted.txt before decryption
    with open("encrypted.txt", "wb") as file:
        file.write(encrypted_message)
    
    # Perform key exchange between A and B
    shared_key = key_exchange(private_key, peer_public_key)
    
    # Decrypt message with shared key
    decrypted_message = decrypt_message(encrypted_message, shared_key)
    
    print('Received:', decrypted_message)
    
    # Write decrypted message to output.txt
    with open("output.txt", "w") as file:
        file.write(decrypted_message)
    
    return jsonify({'response': f'Message received by B: {decrypted_message}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

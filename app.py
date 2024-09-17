from flask import Flask, request, jsonify, render_template
from cryptography.fernet import Fernet
import redis
import os

app = Flask(__name__)

# Generate or retrieve a key for encryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Set up Redis connection
r = redis.Redis(host='redis', port=6379, db=0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/store', methods=['POST'])
def store_secret():
    data = request.json
    secret = data.get('secret')
    expiration = int(data.get('expiration', 300))  # Default to 300 seconds (5 minutes) if not provided

    if not secret:
        return jsonify({'error': 'No secret provided'}), 400

    # Encrypt the secret
    encrypted_secret = cipher_suite.encrypt(secret.encode())

    # Generate a unique token for the link
    token = os.urandom(16).hex()

    # Store the encrypted secret in Redis with the user-defined expiration time
    r.setex(token, expiration, encrypted_secret)

    # Generate the shareable link
    share_link = f"{request.host_url}view/{token}"
    return jsonify({'share_link': share_link})

@app.route('/view/<token>')
def view(token):
    # Check if the token exists in Redis
    encrypted_secret = r.get(token)
    if not encrypted_secret:
        return render_template('view.html', error='Invalid or expired link')

    # Decrypt the secret
    secret = cipher_suite.decrypt(encrypted_secret).decode()

    # Delete the secret from Redis after it’s viewed
    r.delete(token)

    return render_template('view.html', secret=secret)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

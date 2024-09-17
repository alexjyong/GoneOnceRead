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
    print(f"Stored token {token} with expiration {expiration} seconds.")

    # Generate the shareable link
    codespace_name = os.getenv('CODESPACE_NAME')  # Get Codespace name if defined
    github_forwarding_domain = os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')

    if codespace_name and github_forwarding_domain:
        # If running in Codespaces, construct the link using Codespace name and port forwarding domain
        share_link = f"https://{codespace_name}-5000.{github_forwarding_domain}/view/{token}"
        print(f"Generated Codespace share link: {share_link}")
    else:
        # If not in Codespaces, fall back to the default host URL (useful for local dev)
        share_link = f"{request.host_url}view/{token}"
        print(f"Generated local share link: {share_link}")

    return jsonify({'share_link': share_link})

@app.route('/view/<token>')
def view(token):
    # Check if the token exists in Redis
    encrypted_secret = r.get(token)
    if not encrypted_secret:
        print(f"Token {token} not found or expired.")
        return render_template('view.html', error='Invalid or expired link')

    # Decrypt the secret
    secret = cipher_suite.decrypt(encrypted_secret).decode()
    print(f"Retrieved and decrypted secret for token {token}.")

    # Delete the secret from Redis after it’s viewed
    r.delete(token)
    print(f"Deleted token {token} from Redis after viewing.")

    return render_template('view.html', secret=secret)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Default port 5000, dynamic via Codespaces if necessary

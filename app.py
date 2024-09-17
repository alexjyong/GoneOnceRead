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
    password = data.get('password', None)  # Optional password
    expiration = int(data.get('expiration', 300))  # Default to 300 seconds (5 minutes) if not provided

    if not secret:
        return jsonify({'error': 'No secret provided'}), 400

    # Encrypt the secret
    encrypted_secret = cipher_suite.encrypt(secret.encode())

    # Combine the encrypted secret and password (if any)
    stored_data = {
        'secret': encrypted_secret.decode(),
        'password': password
    }

    # Generate a unique token for the link
    token = os.urandom(16).hex()

    # Store the encrypted secret and password in Redis with the user-defined expiration time
    r.setex(token, expiration, str(stored_data))  # Store data as stringified JSON

    # Generate the shareable link
    codespace_name = os.getenv('CODESPACE_NAME')
    github_forwarding_domain = os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN')

    if codespace_name and github_forwarding_domain:
        # If running in Codespaces, construct the link using Codespace name and port forwarding domain
        share_link = f"https://{codespace_name}-5000.{github_forwarding_domain}/view/{token}"
    else:
        # If not in Codespaces, fall back to the default host URL
        share_link = f"{request.host_url}view/{token}"

    return jsonify({'share_link': share_link})

@app.route('/view/<token>', methods=['GET', 'POST'])
def view(token):
    if request.method == 'POST':
        # Handle password submission
        password = request.form.get('password')
        stored_data_str = r.get(token)
        
        if not stored_data_str:
            return render_template('view.html', error='Invalid or expired link')

        # Parse the stored data
        stored_data = eval(stored_data_str.decode())
        stored_password = stored_data.get('password')
        
        # Check if the password matches (if a password was set)
        if stored_password and stored_password != password:
            return render_template('view.html', token=token, error='Invalid password', show_password=True)
        
        # Password is correct, or no password was set
        secret = stored_data.get('secret')
        secret = cipher_suite.decrypt(secret.encode()).decode()

        # Delete the secret from Redis after it’s viewed
        r.delete(token)
        
        return render_template('view.html', secret=secret, formatted=True)

    # First load - Show the password prompt if necessary
    stored_data_str = r.get(token)
    if not stored_data_str:
        return render_template('view.html', error='Invalid or expired link')

    stored_data = eval(stored_data_str.decode())
    if stored_data.get('password'):
        # If password is required, show the password input form
        return render_template('view.html', token=token, show_password=True)

    # If no password, show the secret directly
    secret = cipher_suite.decrypt(stored_data.get('secret').encode()).decode()
    r.delete(token)
    return render_template('view.html', secret=secret, formatted=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

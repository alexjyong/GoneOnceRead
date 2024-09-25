from flask import Flask, request, jsonify, render_template
from cryptography.fernet import Fernet
import redis
import argparse
import os

def get_port():
    """Get the port from command line arguments or default to 8080"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, help='Port number')
    args = parser.parse_args()

    if args.port:
        return int(args.port)
    else:
        return 8080

app = Flask(__name__)
port = get_port()

# Generate or retrieve a key for encryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Set up Redis connection
r = redis.Redis(host='redis', port=6379, db=0)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')


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
        share_link = f"https://{codespace_name}-{port}.{github_forwarding_domain}/view/{token}"
    else:
        # If not in Codespaces, fall back to the default host URL
        share_link = f"{request.host_url}view/{token}"

    return jsonify({'share_link': share_link})

@app.route('/view/<token>', methods=['GET', 'POST'])
def view(token):
    # Handle the GET request with the confirmation logic
    reveal_secret = request.args.get('reveal')

    # Retrieve the secret from Redis
    stored_data_str = r.get(token)
    if not stored_data_str:
        return render_template('view.html', error='Invalid or expired link')

    stored_data = eval(stored_data_str.decode())
    
    # Check if a password is required
    if stored_data.get('password'):
        # Handle the POST request for password submission
        if request.method == 'POST':
            password = request.form.get('password')
            stored_password = stored_data.get('password')

            # Check if the password matches
            if stored_password != password:
                return render_template('view.html', token=token, error='Invalid password', show_password=True)

            # Password is correct, reveal the secret
            secret = cipher_suite.decrypt(stored_data.get('secret').encode()).decode()
            r.delete(token)
            return render_template('view.html', secret=secret, formatted=True)
        
        # Show password prompt if password is required
        return render_template('view.html', token=token, show_password=True)

    # No password required, handle button confirmation logic
    if reveal_secret == 'true':
        # Reveal the secret and delete it from Redis
        secret = cipher_suite.decrypt(stored_data.get('secret').encode()).decode()
        r.delete(token)
        return render_template('view.html', secret=secret, formatted=True)

    # Show the "Reveal Secret" button if no confirmation is given
    return render_template('view.html', token=token, show_reveal_button=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)

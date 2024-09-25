# GoneOnceRead
A simple self-hosted service to securely share sensitive information via one-time links, using encryption and automatic self-destruction after viewing.
Once the information is viewed, the link becomes invalid, ensuring that sensitive data is never stored longer than necessary. The service employs encryption to protect data at rest and is designed for ease of use and deployment with Docker.

## Features

- 🔒 **Secure Sharing:** Uses encryption to protect sensitive information.
- 📜 **One-Time Links:** Generates shareable links that are invalidated after a single view.
- 🕒 **Auto-Destruct:** Data is automatically deleted after it's viewed or after a configurable expiration time.
- 📦 **Docker Support:** Easily deployable with Docker and Docker Compose.
- 🧰 **Self-Hosted:** Take full control by running the service on your own infrastructure.

## How It Works

1. A user submits sensitive information via a web form and sets it to expire after a certain time if not viewed. For an extra layer of protection, a password can be used to protect the secret. 
2. The backend encrypts the information and generates a unique, shareable link.
3. The recipient accesses the link and views the sensitive information. If a password was used in the secret creation, the recipient uses it to access the secret. 
4. After viewing, the link is invalidated and the encrypted data is deleted.

## If you like charts

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#3498db', 'edgeLabelBackground':'#e8e8e8', 'tertiaryColor': '#f0f4f8'}}}%%
%% C4 Context Diagram %%
flowchart TB
    subgraph System_Boundary["GoneOnceRead System"]
        User(End User)
        subgraph Frontend["Frontend"]
            HTML_HTML["HTML / CSS / JS"]
        end
        subgraph Backend["Backend"]
            FlaskApp[Flask Application]
            Encryption[Encryption/Decryption]
        end
        subgraph DataStore["Data Store"]
            Redis_DB[Redis]
        end
    end

    User -->|Interacts with| HTML_HTML["HTML"]
    HTML_HTML -->|API Requests to store and retrieve data| FlaskApp[Flask Application]
    FlaskApp -->|Encrypts & Decrypts| Encryption
    FlaskApp -->|Stores & Retrieves| Redis_DB

    style User fill:#f5c2c7
    style HTML_HTML fill:#3498db,stroke:#3498db,color:#fff
    style FlaskApp fill:#2ecc71,stroke:#2ecc71,color:#fff
    style Encryption fill:#f39c12,stroke:#f39c12,color:#fff
    style Redis_DB fill:#e74c3c,stroke:#e74c3c,color:#fff
```

## Getting Started

### Prerequisites

- **Recommended** Docker and docker-compose for easy setup.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/alexjyong/GoneOnceRead.git
   cd GoneOnceRead
   ```
2. Build and run the app with Docker Compose:
   ```bash
   docker-compose build
   docker-compose up
   ```
3. Open your browser and navigate to http://localhost:8080 (or if you are running this on Github codespaces, the url given to you in ports section) to access the service.

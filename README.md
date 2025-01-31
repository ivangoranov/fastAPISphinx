# FastAPISphinx API

## Overview

FastAPISphinx is a FastAPI-based application that provides an endpoint to trigger an indexing process. The application uses API key authentication and rate limiting to ensure secure and controlled access.

## Features

- **API Key Authentication**: Secure your endpoints with an API key.
- **Rate Limiting**: Control the rate of requests to prevent abuse.
- **Background Tasks**: Run indexing tasks in the background without blocking the main thread.
- **Logging**: Comprehensive logging for monitoring and debugging.

## Requirements

- Python 3.11
- FastAPI
- Uvicorn
- SlowAPI
- Python-dotenv

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/yourusername/fastapisphinx.git
   cd fastapisphinx
   ```

2. **Create a virtual environment**:
   ```sh
   python -m venv env
   source env/bin/activate
   ```

3. **Install the dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** and add your API key and indexer path:
   ```
   SPHINX_API_KEY=your-secure-api-key
   SPHINX_INDEXER_PATH=/full/path/to/indexer
   ```

## Usage

1. **Run the application `uvicorn`**:
   ```sh
   uvicorn main:app --reload
   ```

    ***Run the application with `gunicorn`***:
   ```sh
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```
   
   **Run the application as a background service**:
   Create a systemd service file: Create a new file named fastapisphinx.service in the /etc/systemd/system/ directory with the following content:  
    
         [Unit]
         Description=FastAPISphinx Service
         After=network.target
         
         [Service]
         User=yourusername
         Group=yourgroup
         WorkingDirectory=/path/to/your/project
         ExecStart=/path/to/your/venv/bin/uvicorn main:app --host 0.0.0.0 --port 5001
         Restart=always
         
         [Install]
         WantedBy=multi-user.target

   Replace yourusername, yourgroup, /path/to/your/project, and /path/to/your/venv with the appropriate values for your setup. 
2. Reload the systemd daemon (if not running the service as a background service skip this step):
    ```sh
    sudo systemctl daemon-reload
    ```
     
    Enable the service and start it:
    ```sh
    sudo systemctl enable fastapisphinx
    sudo systemctl start fastapisphinx
    ```
   
3. **Send a POST request to the `/reindex` endpoint**:
   ```sh
   curl -X POST "http://127.0.0.1:5001/reindex" -H "X-API-Key: your-secure-api-key" -H "index: your-index"
   ```

## Endpoints

### POST `/reindex`

Triggers the indexing process.

#### Headers

- `X-API-Key`: Your API key.
- `index`: The index to be reindexed.

#### Responses

- `200 OK`: Indexing started.
- `403 Forbidden`: Unauthorized access.
- `429 Too Many Requests`: Rate limit exceeded.
- `666 Missing index in request`: No index provided in the request.

## Testing

1. **Install the test dependencies**:
   ```sh
   pip install pytest
   ```

2. **Run the tests**:
   ```sh
   pytest
   ```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

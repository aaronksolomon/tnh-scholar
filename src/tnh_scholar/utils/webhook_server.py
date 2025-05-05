import re
import subprocess
import time
from datetime import datetime
from threading import Condition, Event, Thread
from typing import Dict, Optional

import requests
from flask import Flask, jsonify, request


class WebhookServer:
    """A generic webhook server that can receive callbacks from external services."""
    
    def __init__(self, port: int = 5050):
        """
        Initialize webhook server with configuration.
        
        Args:
            port: The port to run the Flask server on
        """
        self.port = port
        self.app = self._create_flask_app()
        self.webhook_received = Condition()
        self.webhook_data = None
        self.flask_running = Event()
        self.flask_server_thread = None
        self.tunnel_process = None
        
    def _create_flask_app(self) -> Flask:
        """Create and configure Flask app with webhook endpoint."""
        app = Flask(__name__)
        
        @app.route('/healthcheck', methods=['GET'])
        def healthcheck():
            """Simple endpoint to verify the server is running."""
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'webhook_received': self.webhook_data is not None
            })
        
        @app.route('/webhook', methods=['POST'])
        def handle_webhook():
            """Receive webhook data from external services."""
            # Get JSON data from the request
            data = request.json
            
            # Log webhook receipt
            print("\n" + "="*40)
            print(f"WEBHOOK RECEIVED at {datetime.now().strftime('%H:%M:%S')}")
            
            if data is not None:
                print(f"Webhook data status: {data.get('status', 'unknown')}")
                
                # Update the shared state with proper synchronization
                with self.webhook_received:
                    self.webhook_data = data
                    self.webhook_received.notify_all()
                    print("Notification sent to waiting threads")
            else:
                print("Webhook received with no JSON data")
            
            # Always return a success response to acknowledge receipt
            return jsonify({'status': 'received'}), 200
        
        @app.route('/shutdown', methods=['POST'])
        def shutdown():
            """Endpoint to gracefully shut down the Flask server."""
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
            return 'Server shutting down...'
        
        return app
    
    def start_server(self) -> None:
        """Start Flask server in a separate thread."""
        # Check if server is already running
        if self.flask_running.is_set() and \
            self.flask_server_thread and \
                self.flask_server_thread.is_alive():
            print(f"Flask server already running on port {self.port}")
            return
        
        # Reset state
        self.flask_running.clear()
        
        # Create thread function that sets event when server starts
        def run_server():
            print(f"Starting Flask server on port {self.port}...")
            self.flask_running.set()
            self.app.run(
                host="0.0.0.0", 
                port=self.port, 
                debug=False, 
                use_reloader=False
                )
            self.flask_running.clear()
            print("Flask server has stopped")
        
        # Start server in a daemon thread
        self.flask_server_thread = Thread(target=run_server, daemon=True)
        self.flask_server_thread.start()
        
        # Wait for server to start
        if not self.flask_running.wait(timeout=5):
            raise RuntimeError("Flask server failed to start within timeout period")
        
        print(f"Flask server started successfully on port {self.port}")
    
    def shutdown_server(self) -> None:
        """Gracefully shut down the Flask server."""
        if not self.flask_running.is_set():
            print("Flask server is not running")
            return
        
        try:
            print("Shutting down Flask server...")
            requests.post(f"http://localhost:{self.port}/shutdown")
            
            # Wait for server to stop
            if self.flask_server_thread:
                self.flask_server_thread.join(timeout=5)
                
            if self.flask_running.is_set():
                print("WARNING: Flask server did not shut down gracefully")
            else:
                print("Flask server shut down successfully")
        except Exception as e:
            print(f"Error shutting down Flask server: {e}")
    
    def create_tunnel(self) -> Optional[str]:
        """
        Create a public webhook URL using py-localtunnel.
        
        Returns:
            Optional[str]: The public webhook URL or None if tunnel creation failed
        """
        # First check if pylt is installed
        try:
            subprocess.run(["pylt", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print("ERROR: pylt not found. Install with: pip install pylt")
            raise RuntimeError("Tunnel not started.") from e

        print(f"Creating public tunnel to port {self.port}...")

        # Start the localtunnel process
        self.tunnel_process = subprocess.Popen(
            ["pylt", "port", str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give it time to establish the tunnel
        time.sleep(3)

        # Check if process started successfully
        if self.tunnel_process.poll() is not None:
            if self.tunnel_process.stderr:
                stderr = self.tunnel_process.stderr.read()
            else:
                raise RuntimeError("ERROR: Tunnel process failed: no stderr")
            if self.tunnel_process.stdout:
                stdout = self.tunnel_process.stdout.read()
            else:
                raise RuntimeError("ERROR: Tunnel process failed: no stderr")
            raise RuntimeError(
                f"ERROR: Tunnel process failed:\nSTDOUT: {stdout}\nSTDERR: {stderr}"
                )

        # Regular expression to find the URL in the output
        url_pattern = re.compile(r'https?://[^\s\'"]+')

        # Read output with timeout
        start_time = time.time()
        tunnel_url = None

        while time.time() - start_time < 15:  # Wait up to 15 seconds
            if not self.tunnel_process.stdout:
                raise RuntimeError("ERROR: tunnel process has no stdout.")

            line = self.tunnel_process.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
            print(f"Tunnel output: {line.strip()}")

            # Check if the URL pattern is found
            if match := url_pattern.search(line):
                tunnel_url = match[0]
                break

        if not tunnel_url:
            print("ERROR: Could not find tunnel URL in output")
            if self.tunnel_process.poll() is None:
                self.tunnel_process.terminate()
            return None

        print(f"Public tunnel created: {tunnel_url}")
        webhook_url = f"{tunnel_url}/webhook"

        # Verify the tunnel works
        try:
            response = requests.get(f"{tunnel_url}/healthcheck", timeout=20)
            if response.status_code == 200:
                print("Tunnel verified: Flask server is accessible")
            else:
                print(f"Tunnel health check returned status {response.status_code}")
                raise RuntimeError("Could not verify Tunnel.") 
        except requests.RequestException as e:
            raise e

        return webhook_url
    
    def close_tunnel(self) -> None:
        """Close the tunnel if it's running."""
        if self.tunnel_process and self.tunnel_process.poll() is None:
            print("Closing tunnel...")
            self.tunnel_process.terminate()
            self.tunnel_process.wait(timeout=5)
            print("Tunnel closed")
    
    def wait_for_webhook(self, timeout: int = 120) -> Optional[Dict]:
        """
        Wait for webhook data to be received.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Optional[Dict]: The webhook data or None if timed out
        """
        print(f"Waiting for webhook callback (timeout: {timeout}s)...")
        
        with self.webhook_received:
            # Wait for notification with timeout
            webhook_received = self.webhook_received.wait(timeout=timeout)
            
            if webhook_received and self.webhook_data is not None:
                print("Webhook received with data")
                return self.webhook_data
        
        print(f"Timed out waiting for webhook after {timeout} seconds")
        return None
    
    def cleanup(self) -> None:
        """Clean up all resources."""
        self.close_tunnel()
        self.shutdown_server()
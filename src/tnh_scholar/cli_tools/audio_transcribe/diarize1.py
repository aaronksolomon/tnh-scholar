import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from threading import Condition, Event, Thread
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pydub import AudioSegment

# Flask app and shared state
app = Flask(__name__)
webhook_received = Condition()
diarization_results = None
flask_running = Event()
flask_server_thread = None
tunnel_process = None

# Configuration
load_dotenv()
API_KEY = os.getenv("PYANNOTEAI_API_TOKEN")
DEFAULT_FLASK_PORT = 5050

# ============================================================================
# Flask Server Management
# ============================================================================

def create_flask_app() -> Flask:
    """Create and configure Flask app with webhook endpoint."""
    app = Flask(__name__)
    
    @app.route('/healthcheck', methods=['GET'])
    def healthcheck():
        """Simple endpoint to verify the server is running."""
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'webhook_received': diarization_results is not None
        })
    
    @app.route('/webhook', methods=['POST'])
    def handle_webhook():
        """Receive diarization results from pyannote API."""
        global diarization_results
        
        # Get JSON data from the request
        data = request.json
        
        # Log webhook receipt
        print("\n" + "="*40)
        print(f"WEBHOOK RECEIVED at {datetime.now().strftime('%H:%M:%S')}")
        
        if data is not None:
            print(f"Job status: {data.get('status', 'unknown')}")
            
            # Update the shared state with proper synchronization
            with webhook_received:
                diarization_results = data
                webhook_received.notify_all()
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

def start_flask_server(port: int = DEFAULT_FLASK_PORT) -> None:
    """Start Flask server in a separate thread."""
    global flask_running, flask_server_thread
    
    # Check if server is already running
    if flask_running.is_set() and flask_server_thread and flask_server_thread.is_alive():
        print(f"Flask server already running on port {port}")
        return
    
    # Reset state
    flask_running.clear()
    
    # Create thread function that sets event when server starts
    def run_server():
        print(f"Starting Flask server on port {port}...")
        flask_running.set()
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
        flask_running.clear()
        print("Flask server has stopped")
    
    # Start server in a daemon thread
    flask_server_thread = Thread(target=run_server, daemon=True)
    flask_server_thread.start()
    
    # Wait for server to start
    if not flask_running.wait(timeout=5):
        raise RuntimeError("Flask server failed to start within timeout period")
    
    print(f"Flask server started successfully on port {port}")

def shutdown_flask_server() -> None:
    """Gracefully shut down the Flask server."""
    global flask_running, flask_server_thread
    
    if not flask_running.is_set():
        print("Flask server is not running")
        return
    
    try:
        print("Shutting down Flask server...")
        requests.post(f"http://localhost:{DEFAULT_FLASK_PORT}/shutdown")
        
        # Wait for server to stop
        if flask_server_thread:
            flask_server_thread.join(timeout=5)
            
        if flask_running.is_set():
            print("WARNING: Flask server did not shut down gracefully")
        else:
            print("Flask server shut down successfully")
    except Exception as e:
        print(f"Error shutting down Flask server: {e}")

# ============================================================================
# Tunnel Management
# ============================================================================

def create_webhook_url(port: int = DEFAULT_FLASK_PORT) -> Optional[str]:
    """
    Create a public webhook URL using py-localtunnel.
    
    Args:
        port: The local port to tunnel
        
    Returns:
        Optional[str]: The public webhook URL or None if tunnel creation failed
    """
    global tunnel_process

    # First check if pylt is installed
    try:
        subprocess.run(["pylt", "--version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print("ERROR: pylt not found. Install with: pip install pylt")
        raise RuntimeError("Tunnel not started.") from e

    print(f"Creating public tunnel to port {port}...")

    # Start the localtunnel process
    tunnel_process = subprocess.Popen(
        ["pylt", "port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Give it time to establish the tunnel
    time.sleep(3)

    # Check if process started successfully
    if tunnel_process.poll() is not None:
        stderr = tunnel_process.stderr.read()
        stdout = tunnel_process.stdout.read()
        print(f"ERROR: Tunnel process failed:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        return None

    # Regular expression to find the URL in the output
    url_pattern = re.compile(r'https?://[^\s\'"]+')

    # Read output with timeout
    start_time = time.time()
    tunnel_url = None

    while time.time() - start_time < 15:  # Wait up to 15 seconds
        line = tunnel_process.stdout.readline()
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
        if tunnel_process.poll() is None:
            tunnel_process.terminate()
        return None

    print(f"Public tunnel created: {tunnel_url}")
    webhook_url = f"{tunnel_url}/webhook"

    # Verify the tunnel works
    try:
        response = requests.get(f"{tunnel_url}/healthcheck", timeout=20)
        if response.status_code == 200:
            print("Tunnel verified: Flask server is accessible")
        else:
            print(f"Tunnel health check FAILED with returned status {response.status_code}")
            raise RuntimeError(f"Could not verify Tunnel: {e}") from e
    except requests.RequestException as e:
        raise e

    return webhook_url

def close_tunnel() -> None:
    """Close the tunnel if it's running."""
    global tunnel_process
    
    if tunnel_process and tunnel_process.poll() is None:
        print("Closing tunnel...")
        tunnel_process.terminate()
        tunnel_process.wait(timeout=5)
        print("Tunnel closed")

# ============================================================================
# Pyannote.ai API Integration
# ============================================================================

def upload_to_pyannote(file_path: Path) -> Optional[str]:
    """
    Upload audio file to pyannote temporary storage.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Optional[str]: The media ID if upload succeeded, None otherwise
    """
    if not API_KEY:
        print("ERROR: PYANNOTEAI_API_TOKEN environment variable not set")
        return None
    
    if not file_path.exists():
        print(f"ERROR: Audio file not found: {file_path}")
        return None
    
    # Step 1: Request an upload URL
    media_id = f"media://diarization-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.post(
            "https://api.pyannote.ai/v1/media/input",
            headers=headers,
            json={"url": media_id}
        )
        
        response.raise_for_status()
        
        # Get the upload URL from the response
        upload_info = response.json()
        upload_url = upload_info.get("url")
        
        print(f"Temporary media ID created: {media_id}")
        
        # Step 2: Upload the file to the provided URL
        print(f"Uploading file to Pyannote.ai: {file_path}...")
        with open(file_path, "rb") as file_data:
            upload_response = requests.put(
                upload_url,
                data=file_data,
                headers={"Content-Type": "audio/mpeg"}
            )
        
        upload_response.raise_for_status()
        print("File uploaded successfully")
        
        return media_id
        
    except requests.RequestException as e:
        print(f"ERROR: API request failed: {e}")
        return None

def start_diarization(media_id: str, webhook_url: str) -> Optional[str]:
    """
    Start diarization job with pyannote.ai API.
    
    Args:
        media_id: The media ID from upload_to_pyannote
        webhook_url: The webhook URL to receive results
        
    Returns:
        Optional[str]: The job ID if started successfully, None otherwise
    """
    if not API_KEY:
        print("ERROR: PYANNOTEAI_API_TOKEN environment variable not set")
        return None
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        print(f"Starting diarization job for {media_id}...")
        print(f"Webhook URL: {webhook_url}")
        
        response = requests.post(
            "https://api.pyannote.ai/v1/diarize",
            headers=headers,
            json={
                "url": media_id,
                "webhook": webhook_url
            }
        )
        
        response.raise_for_status()
        job_info = response.json()
        job_id = job_info.get("jobId")
        
        if not job_id:
            print("ERROR: No job ID in response")
            return None
            
        print(f"Diarization job started with ID: {job_id}")
        print(f"Initial status: {job_info.get('status', 'unknown')}")
        
        return job_id
        
    except requests.RequestException as e:
        print(f"ERROR: API request failed: {e}")
        return None

def check_job_status(job_id: str) -> Optional[Dict]:
    """
    Check the status of a diarization job.
    
    Args:
        job_id: The job ID to check
        
    Returns:
        Optional[Dict]: The job status response or None if request failed
    """
    if not API_KEY:
        print("ERROR: PYANNOTEAI_API_TOKEN environment variable not set")
        return None
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(
            f"https://api.pyannote.ai/v1/jobs/{job_id}",
            headers=headers
        )
        
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        print(f"ERROR: Failed to check job status: {e}")
        return None

def wait_for_diarization_results(timeout: int = 120) -> Optional[Dict]:
    """
    Wait for diarization results to be received via webhook.
    
    Args:
        timeout: Maximum time to wait in seconds
        
    Returns:
        Optional[Dict]: The diarization results or None if timed out
    """
    global diarization_results
    
    print(f"Waiting for webhook callback (timeout: {timeout}s)...")
    
    with webhook_received:
        # Wait for notification with timeout
        webhook_received.wait(timeout=timeout)
        
        if diarization_results is not None:
            print("Webhook received with diarization results")
            return diarization_results
    
    print(f"Timed out waiting for webhook after {timeout} seconds")
    return None

# ============================================================================
# Audio Processing
# ============================================================================

def process_diarization(results: Dict, audio_path: Path, output_dir: Path) -> List[Dict]:
    """
    Process diarization results to create speaker segments.
    
    Args:
        results: The diarization results from the API
        audio_path: Path to the original audio file
        output_dir: Directory to save speaker segments
        
    Returns:
        List[Dict]: Information about the extracted segments
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check job status
    if results.get("status") != "succeeded":
        print(f"ERROR: Job failed with status: {results.get('status')}")
        print(f"Error details: {results.get('error', 'No error details provided')}")
        return []
    
    # Get diarization segments
    segments = results.get("output", {}).get("diarization", [])
    if not segments:
        print("ERROR: No diarization segments found in results")
        return []
    
    print(f"Processing {len(segments)} diarization segments...")
    
    try:
        # Load audio file with pydub
        audio = AudioSegment.from_file(audio_path)
        speaker_segments = []
        
        for i, segment in enumerate(segments):
            start_ms = int(segment["start"] * 1000)
            end_ms = int(segment["end"] * 1000)
            speaker = segment["speaker"]
            
            # Extract segment
            audio_segment = audio[start_ms:end_ms]
            
            # Create segment filename
            filename = f"{output_dir}/{speaker}_{start_ms}_{end_ms}.mp3"
            
            # Save segment
            # audio_segment.export(filename, format="mp3")
            
            # Store segment info
            speaker_segments.append({
                "speaker": speaker,
                "start": segment["start"],
                "end": segment["end"],
                "duration": segment["end"] - segment["start"],
                "filename": str(filename)
            })
            
            # Log progress
            if i % 10 == 0 or i == len(segments) - 1:
                print(f"Processed {i+1}/{len(segments)} segments")
        
        # Save the segment info as JSON
        segments_json = output_dir / "segments.json"
        with open(segments_json, 'w') as f:
            json.dump(speaker_segments, f, indent=2)
        
        print(f"Extracted {len(speaker_segments)} speaker segments to {output_dir}/")
        print(f"Segment info saved to {segments_json}")
        
        return speaker_segments
        
    except Exception as e:
        print(f"ERROR: Failed to process diarization segments: {e}")
        return []

# ============================================================================
# Main Diarization Function
# ============================================================================

def diarize(audio_file_path: Path, output_dir: Path = None, port: int = DEFAULT_FLASK_PORT) -> Optional[List[Dict]]:
    """
    Complete diarization process from audio file to speaker segments.
    
    Args:
        audio_file_path: Path to the audio file
        output_dir: Directory to save speaker segments
        port: Port to use for Flask server
        
    Returns:
        Optional[List[Dict]]: Information about the extracted segments or None if failed
    """
    global diarization_results
    global app


    # Validate input
    audio_file_path = Path(audio_file_path).resolve()
    if not audio_file_path.exists():
        print(f"ERROR: Audio file not found: {audio_file_path}")
        return None

    # Set default output directory if not provided
    if output_dir is None:
        output_dir = audio_file_path.parent / f"{audio_file_path.stem}_segments"
    else:
        output_dir = Path(output_dir).resolve()

    # Reset global state
    diarization_results = None

    # Step 1: Start Flask server
    try:
        app = create_flask_app()
        start_flask_server(port=port)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return None

    # Step 2: Create public webhook URL
    webhook_url = create_webhook_url(port=port)
    if not webhook_url:
        print("ERROR: Failed to create webhook URL")
        shutdown_flask_server()
        return None

    # Step 3: Upload audio to pyannote
    media_id = upload_to_pyannote(audio_file_path)
    if not media_id:
        print("ERROR: Failed to upload audio file")
        close_tunnel()
        shutdown_flask_server()
        return None

    # Step 4: Start diarization job
    job_id = start_diarization(media_id, webhook_url)
    if not job_id:
        print("ERROR: Failed to start diarization job")
        close_tunnel()
        shutdown_flask_server()
        return None

    # Step 5: Wait for results
    results = wait_for_diarization_results(timeout=120)

    # If webhook didn't receive results, check job status directly
    if results is None:
        print("Webhook not received, checking job status directly...")
        results = check_job_status(job_id)

    if not results:
        print("ERROR: Failed to get diarization results")
        close_tunnel()
        shutdown_flask_server()
        return None

    return process_diarization(results, audio_file_path, output_dir)
  
        
# ============================================================================
# Command-line Interface
# ============================================================================

def main():
    """Command-line interface for diarization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Speaker diarization using pyannote.ai")
    parser.add_argument("audio_file", type=str, help="Path to the audio file")
    parser.add_argument("-o", "--output", type=str, help="Output directory for speaker segments", default=None)
    parser.add_argument("-p", "--port", type=int, help="Port for Flask server", default=DEFAULT_FLASK_PORT)
    
    args = parser.parse_args()
    
    diarize(Path(args.audio_file), output_dir=args.output and Path(args.output), port=args.port)

if __name__ == "__main__":
    main()
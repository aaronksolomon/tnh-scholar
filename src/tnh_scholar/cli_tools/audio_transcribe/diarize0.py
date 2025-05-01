import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from threading import Condition

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pydub import AudioSegment

working_dir = Path.home() / "Desktop/transcription_wouter"

# Configuration
load_dotenv()
API_KEY = os.getenv("PYANNOTEAI_API_TOKEN")
audio_file_path = working_dir \
    / "audio_transcriptions"  \
    / "Sr. Abbess Interview Thay's Hut (for transcription).mp3"
if not audio_file_path.exists:
    raise FileNotFoundError("Audio file not found.")
audio_file = str(audio_file_path)
output_dir = "speaker_segments"
flask_port = 5050
os.makedirs(output_dir, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)

# Shared state for webhook handling
webhook_received = Condition()
diarization_results = None

def create_webhook_url():
    """Create a webhook URL using py-localtunnel"""
    
    # Start localtunnel process
    process = subprocess.Popen(
        ["pylt", "port", str(flask_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Give it time to establish the tunnel
    time.sleep(3)

    # Read output looking for the URL
    url_pattern = re.compile(r'(https?://[^\s\'"]+)')

    # Check if process is running
    if process.poll() is not None:
        # Process already terminated
        stderr = process.stderr.read()
        stdout = process.stdout.read()
        print(f"Localtunnel process failed:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        return None

    # Read initial output
    output = ""

    # Keep the process running in the background
    while process.poll() is None:
        # Read any available output without blocking
        line = process.stdout.readline()
        if not line:
            break

        output += line
        print(line.strip())

        if match := url_pattern.search(output):
            tunnel_url = match[0]
            print(f"Localtunnel URL found: {tunnel_url}")
            # Keep process running in background for the tunnel to work
            return f"{tunnel_url}/webhook"

    print("Could not find tunnel URL in pylt output")
    return None

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Receive diarization results from pyannote API"""
    global diarization_results
    data = request.json
    if data is not None:
        print("Webhook received! Job status:", data.get("status", "unknown"))
        
        with webhook_received:
            diarization_results = data
            webhook_received.notify_all()
    else:
        print("Webhook received with no JSON data")
    
    return jsonify({'status': 'received'}), 200

def start_flask():
    """Start Flask server in a background thread"""
    app.run(host="0.0.0.0", port=flask_port)

def upload_to_pyannote(file_path):
    """Upload audio file to pyannote temporary storage"""
    # Step 1: Request an upload URL
    media_id = f"media://diarization-test-{int(time.time())}"

    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(
        "https://api.pyannote.ai/v1/media/input",
        headers=headers,
        json={"url": media_id}
    )

    if response.status_code != 201:
        raise RuntimeError(
            f"Failed to get upload URL: {response.status_code} - {response.text}"
            )

    # Get the upload URL from the response
    upload_info = response.json()
    print(f"upload info {upload_info}")
    upload_url = upload_info.get("url")
    
    print(f"upload_url: {upload_url}")
    print(f"Temporary media ID created: {media_id}")

    # Step 2: Upload the file to the provided URL
    print("Uploading to Pyannote AI...")
    with open(file_path, "rb") as file_data:
        upload_response = requests.put(
            upload_url,
            data=file_data,
            headers={"Content-Type": "audio/mpeg"}
        )

    if upload_response.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to upload file: "
            f"{upload_response.status_code} - {upload_response.text}"
            )

    print("File uploaded successfully to temporary storage")
    return media_id

def process_diarization(results, audio_path):
    """Process diarization results to create speaker segments"""
    if results.get("status") != "succeeded":
        print(f"Job failed with status: {results.get('status')}")
        print(f"Error details: {results.get('error', 'No error details provided')}")
        return
    
    segments = results.get("output", {}).get("diarization", [])
    if not segments:
        print("No diarization segments found in results")
        return
    
    # Load audio file with pydub
    audio = AudioSegment.from_file(audio_path)
    speaker_segments = []
    
    for segment in segments:
        start_ms = int(segment["start"] * 1000)
        end_ms = int(segment["end"] * 1000)
        speaker = segment["speaker"]
        
        # Extract segment
        audio_segment = audio[start_ms:end_ms]
        
        # Create segment filename
        filename = f"{output_dir}/{speaker}_{start_ms}_{end_ms}.mp3"
        
        # Save segment
        audio_segment.export(filename, format="mp3")
        
        # Store segment info
        speaker_segments.append({
            "speaker": speaker,
            "start": segment["start"],
            "end": segment["end"],
            "filename": filename
        })
    
    # Save the segment info as JSON for your transcription pipeline
    with open(f"{output_dir}/segments.json", 'w') as f:
        json.dump(speaker_segments, f, indent=2)
    
    print(f"Extracted {len(speaker_segments)} speaker segments to {output_dir}/")
    return speaker_segments


def get_job(job_id):
    url = f"https://api.pyannote.ai/v1/jobs/{job_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    return requests.request("GET", url, headers=headers)

def diarize_proto():
    global diarization_results
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    time.sleep(1)  # Give Flask time to start

    # Create webhook URL
    webhook_url = create_webhook_url()
    print(f"Webhook URL: {webhook_url}")

    # Upload the file to pyannote's temporary storage
    media_url = upload_to_pyannote(audio_file_path)

    # Send diarization request to pyannote API
    headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    response = requests.post(
        "https://api.pyannote.ai/v1/diarize",
        headers=headers,
        json={
            "url": media_url,
            "webhook": webhook_url
        }
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return

    job_info = response.json()
    job_id = job_info["jobId"]
    print(f"Diarization job started with ID: {job_id}")
    print(f"Status: {job_info.get('status', 'unknown')}")
    print("Waiting for webhook callback...")

    # Wait for webhook to be received (with timeout)
    with webhook_received:
        # Wait up to 2 minutes.
        webhook_received.wait(timeout=120)

    if diarization_results is None:
        print("Webhook not received. Checking for job completion:")
        result = get_job(job_id)
        diarization_results = result.json()

        if status := diarization_results.get("status") == "succeeded":
            print(f"Status: {status}")
            return

    return process_diarization(diarization_results, audio_file_path)
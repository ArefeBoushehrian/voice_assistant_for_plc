import sounddevice as sd
import numpy as np
import requests
import io
import playsound

# Configuration
SERVER_URL = 'http://192.168.1.13:8888/audio'  # Replace with your server IP and port
RATE = 44100
CHUNK_SIZE = 4096  # Size of each chunk in bytes

def record_and_send_audio():
    print("Recording...")
    audio_data = io.BytesIO()
    
    def callback(indata, frames, time, status):
        if status:
            print(status, flush=True)
        audio_data.write(indata.tobytes())
    
    with sd.InputStream(samplerate=RATE, channels=1, dtype='int16', callback=callback):
        while True:
            command = input("Type 'end' to stop recording and send audio, or 'exit' to quit: ").strip().lower()
            if command == 'end':
                print("Sending audio to server...")
                audio_data.seek(0)
                send_audio_chunks(audio_data.getvalue())
                
                print("Waiting for response...")
                response_audio = send_end_signal()
                save_and_play_audio(response_audio)
                break
            elif command == 'exit':
                print("Exiting...")
                break

def send_audio_chunks(audio_data):
    # Send audio data in chunks
    chunk_size = CHUNK_SIZE
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i + chunk_size]
        response = requests.post(SERVER_URL, data=chunk)
        if response.status_code != 200:
            print(f"Failed to send audio chunk. Status code: {response.status_code}")
            return

def send_end_signal():
    # Send 'END' signal to server
    response = requests.post(SERVER_URL, data=b'END')
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to send 'END' signal. Status code: {response.status_code}")
        return None

def save_and_play_audio(audio_data):
    if audio_data:
        with open('response_client.wav', 'wb') as f:
            f.write(audio_data)
        print("Playing response audio...")
        
        playsound.playsound('response_client.wav', block=True)
    else:
        print("No audio data received.")

if __name__ == "__main__":
    record_and_send_audio()

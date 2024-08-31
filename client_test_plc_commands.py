import sounddevice as sd
import wave
import requests
import os
import playsound

# Configuration
SERVER_URL = 'http://192.168.1.13:8888/audio'  # Replace with your server IP and port
RATE = 44100
CHANNELS = 1
FILENAME = 'recorded_audio.wav'

def record_audio():
    print("Recording...")
    audio_data = sd.rec(int(10 * RATE), samplerate=RATE, channels=CHANNELS, dtype='int16')
    sd.wait()  # Wait until recording is finished
    print("Finished recording.")
    
    # Save the recorded audio to a .wav file
    with wave.open(FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(RATE)
        wf.writeframes(audio_data.tobytes())
    
    return FILENAME

def send_wav_to_server(file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(SERVER_URL, files={'file': f})
    
    if response.status_code == 200:
        print("Audio file successfully sent to server.")
        return response.content
    else:
        print(f"Failed to send audio file. Status code: {response.status_code}")
        return None

def save_and_play_audio(audio_data):
    if audio_data:
        response_filename = 'response_from_server.wav'
        with open(response_filename, 'wb') as f:
            f.write(audio_data)
        print("Playing response audio...")
        playsound.playsound(response_filename, block=True)
        os.remove(response_filename)  # Optionally delete the response file after playing
    else:
        print("No audio data received.")

if __name__ == "__main__":
    while True:
        command = input("Type 'start' to begin recording, 'end' to send, or 'exit' to quit: ").strip().lower()
        
        if command == 'start':
            file_path = record_audio()
        elif command == 'end':
            if os.path.exists(FILENAME):
                response_audio = send_wav_to_server(FILENAME)
                save_and_play_audio(response_audio)
                os.remove(FILENAME)  # Delete the recorded file after sending
            else:
                print("No audio file found. Please record first.")
        elif command == 'exit':
            print("Exiting...")
            break
        else:
            print("Unknown command. Please type 'start', 'end', or 'exit'.")

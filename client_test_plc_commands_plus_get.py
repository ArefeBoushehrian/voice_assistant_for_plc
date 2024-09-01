import requests
import os
import playsound

# Configuration
SERVER_URL = 'http://192.168.1.13:8888/audio'  # Replace with your server IP and port
FILENAME = 'downloaded_audio.wav'

def download_wav_from_url(url, file_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Audio file downloaded and saved as {file_path}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

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
        #os.remove(response_filename)  # Optionally delete the response file after playing
    else:
        print("No audio data received.")

if __name__ == "__main__":
    audio_url = "192.168.1.109/recording.wav"  # Replace with the actual URL

    while True:
        command = input("Type 'download' to download the audio, 'send' to send to server, or 'exit' to quit: ").strip().lower()
        
        if command == 'download':
            download_wav_from_url(audio_url, FILENAME)
        elif command == 'send':
            if os.path.exists(FILENAME):
                response_audio = send_wav_to_server(FILENAME)
                save_and_play_audio(response_audio)
                #os.remove(FILENAME)  # Delete the downloaded file after sending
            else:
                print("No audio file found. Please download first.")
        elif command == 'exit':
            print("Exiting...")
            break
        else:
            print("Unknown command. Please type 'download', 'send', or 'exit'.")

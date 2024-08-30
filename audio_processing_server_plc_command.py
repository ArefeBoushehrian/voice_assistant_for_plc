from flask import Flask, request, send_file, jsonify
import wave
import io
import os
from pydub import AudioSegment
import speech_recognition as sr
from gtts import gTTS
from openai import OpenAI
import playsound
"""
import snap7
from snap7.util import *
from snap7.types import *
"""

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key="sk-M4Jl5jb0AthtsEo1mFaULZMTb8rJfWMclyDQuFOsGte3ZeDm",
    base_url="https://api.chatanywhere.tech/v1"
)

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300

audio_chunks = io.BytesIO()
"""
# Connect to PLCSIM
plc = snap7.client.Client()
plc.connect('127.0.0.1', 0, 1)  # Localhost, Rack 0, Slot 1

def set_command(command_bit, value):
    # Read the command area (memory bits)
    data = plc.read_area(areas['MK'], 0, 0, 1)  # MK = Memory Bits (replace with actual DB or address)
    set_bool(data, 0, command_bit, value)
    plc.write_area(areas['MK'], 0, 0, data)

def turn_on_light():
    set_command(0, True)  # Set M0.0 to True

def turn_off_light():
    set_command(1, True)  # Set M0.1 to True

def toggle_light():
    set_command(2, True)  # Set M0.2 to True

def reset_commands():
    # Reset all commands (turn off M0.0, M0.1, M0.2)
    data = plc.read_area(areas['MK'], 0, 0, 1)
    set_bool(data, 0, 0, False)  # Reset M0.0
    set_bool(data, 0, 1, False)  # Reset M0.1
    set_bool(data, 0, 2, False)  # Reset M0.2
    plc.write_area(areas['MK'], 0, 0, data)
"""
def split_first_line_and_rest(text):
    # Split the text into lines
    lines = text.split('\n', 1)
    # Return the first line and the rest of the text
    first_line = lines[0]
    rest_of_text = lines[1] if len(lines) > 1 else ''
    return first_line, rest_of_text

def handling_plc_command_sending(command):
    if command == 'None':
        print("Received command is 'None'. No action will be taken.")
        return
    print(f"Executing command: {command}")
    """
    # Map command strings to function names
    command_map = {
        'turn_on': turn_on_light,
        'turn_off': turn_off_light,
        'toggle': toggle_light
    }

    # Retrieve the function based on command
    func = command_map.get(command)

    if func:
        func()  # Call the function
        print(f"Executed command: {command}")
    else:
        print(f"Unknown command: {command}")
    """

@app.route('/')
def home():
    return "Welcome to the Audio Processing Server!"

@app.route('/test', methods=['POST'])
def test_data():
    if request.data:
        # Assuming the data sent is in plain text for this test
        received_data = request.data.decode('utf-8')
        print(f"Received data: {received_data}")

        # Send a response back to the client
        response_message = f"Data received successfully: {received_data}"
        return jsonify({"message": response_message})
    return 'No data received', 400

@app.route('/audio', methods=['POST'])
def process_audio():
    global audio_chunks

    if request.data:
        if request.data == b'END':
            wav_file_path = 'record_out.wav'
            convert_raw_to_wav(audio_chunks.getvalue(), wav_file_path)
            print('getting audio, now it is time to process')
            audio_chunks = io.BytesIO()

            response_wav_path = process_audio_file(wav_file_path)
            print('outputting....')
            return send_file(response_wav_path, mimetype='audio/wav')
        else:
            audio_chunks.write(request.data)
            return 'Audio chunk recieved', 200
    return 'No audio data received', 400

def convert_raw_to_wav(raw_audio, output_file):
    sample_rate = 44100
    bits_per_sample = 16
    num_channels = 1
    with wave.open(output_file, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(bits_per_sample // 8)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(raw_audio)

def process_audio_file(wav_file_path):
    audio = AudioSegment.from_wav(wav_file_path)
    audio_file = sr.AudioFile(wav_file_path)
    response_text = ""
    with audio_file as source:
        audio_data = recognizer.record(source)
        try:
            question = recognizer.recognize_google(audio_data)
            prompt_question = "Hi GPT, i have following commands for my plc, i want you to process the following text and find what command should be run or there is no command suitable for it. the format of answer i want is that in first line just write the command name or None and then in the next line write your descriptions. "
            prompt_question += " commands: 1. turn_on_light  2. turn_off_light  3. toggle_light "
            prompt_question += "text: " + question
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt_question}],
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    response_text += chunk.choices[0].delta.content

            command_name, answer_text = split_first_line_and_rest(response_text)
            handling_plc_command_sending(command_name)
            tts = gTTS(text=answer_text, lang='en', slow=False)
            mp3_path = "response.mp3"
            tts.save(mp3_path)
            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(mp3_path)
            wav_path = "response.wav"
            audio.export(wav_path, format="wav")
            #playsound.playsound('response.wav', block=True)
            return wav_path
        except sr.UnknownValueError:
            return "unknown_error.wav"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
    #plc.disconnect()
    print("Disconnected from PLCSIM")

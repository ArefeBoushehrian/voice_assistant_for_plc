from flask import Flask, request, send_file, jsonify
import wave
import io
import os
from pydub import AudioSegment
import speech_recognition as sr
from gtts import gTTS
from openai import OpenAI
import playsound

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key="sk-M4Jl5jb0AthtsEo1mFaULZMTb8rJfWMclyDQuFOsGte3ZeDm",
    base_url="https://api.chatanywhere.tech/v1"
)

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300

audio_chunks = io.BytesIO()

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
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": question}],
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    response_text += chunk.choices[0].delta.content
            tts = gTTS(text=response_text, lang='en', slow=False)
            mp3_path = "response.mp3"
            tts.save(mp3_path)
            # Convert MP3 to WAV
            audio = AudioSegment.from_mp3(mp3_path)
            wav_path = "response.wav"
            audio.export(wav_path, format="wav")
            playsound.playsound('response.wav', block=True)
            return wav_path
        except sr.UnknownValueError:
            return "unknown_error.wav"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)

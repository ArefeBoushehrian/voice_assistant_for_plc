from flask import Flask, request, send_file, jsonify
import wave
import io
import os
from pydub import AudioSegment
import speech_recognition as sr
from gtts import gTTS
from openai import OpenAI
import playsound

#import snap7
#from snap7.util import set_bool
#from snap7.client import Client
import struct

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import ExceptionResponse


MK_AREA = 0x83

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
plc = Client()
plc.connect('192.168.0.1', 0, 1)  # Localhost, Rack 0, Slot 1
print(plc.get_cpu_state()) 

db_number = 2
start_offset = 0
bit_offset = 0
value = 1  # 1 = true | 0 = false

start_address = 0  # starting address
length = 4  # double word

def writeBool(db_number, start_offset, bit_offset, value):
	reading = plc.db_read(db_number, start_offset, 1)    # (db number, start offset, read 1 byte)
	snap7.util.set_bool(reading, 0, bit_offset, value)   # (value 1= true;0=false) (bytearray_: bytearray, byte_index: int, bool_index: int, value: bool)
	plc.db_write(db_number, start_offset, reading)       #  write back the bytearray and now the boolean value is changed in the PLC.
	return None

def readBool(db_number, start_offset, bit_offset):
	reading = plc.db_read(db_number, start_offset, 1)  
	a = snap7.util.get_bool(reading, 0, bit_offset)
	print('DB Number: ' + str(db_number) + ' Bit: ' + str(start_offset) + '.' + str(bit_offset) + ' Value: ' + str(a))
	return None

def readMemory(start_address,length):
	reading = plc.read_area(snap7.types.Areas.MK, 0, start_address, length)
	value = struct.unpack('>f', reading)  # big-endian
	print('Start Address: ' + str(start_address) + ' Value: ' + str(value))

def writeMemory(start_address,length,value):
	plc.mb_write(start_address, length, bytearray(struct.pack('>f', value)))  # big-endian
	print('Start Address: ' + str(start_address) + ' Value: ' + str(value))
"""

def connect_to_plc(ip, port):
    client = ModbusTcpClient(ip, port=port)
    if client.connect():
        print("Connected to PLC")
    else:
        print("Failed to connect to PLC")
    return client

def read_register(client, address):
    try:
        response = client.read_holding_registers(address, 1)
        if isinstance(response, ExceptionResponse):
            print(f"Modbus exception: {response}")
            return None
        if not response.isError():
            return response.registers[0]
        else:
            print(f"Error reading register at address {address}: {response}")
            return None
    except ModbusIOException as e:
        print(f"IO error reading register: {e}")
        return None

def write_register(client, address, value):
    try:
        response = client.write_register(address, value)
        if isinstance(response, ExceptionResponse):
            print(f"Modbus exception: {response}")
            return None
    except ModbusIOException as e:
        print(f"IO error writing to register: {e}")

def set_command(command_bit, value):
    # Read the command area (memory bits)
    write_register(client, command_bit, value)

def turn_on_light():
    set_command(0, True)  # Set M0.0 to True

def turn_off_light():
    set_command(1, True)  # Set M0.1 to True

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
    
    # Map command strings to function names
    command_map = {
        'turn_on': turn_on_light,
        'turn_off': turn_off_light
    }

    # Retrieve the function based on command
    func = command_map.get(command)

    if func:
        func()  # Call the function
        print(f"Executed command: {command}")
    else:
        print(f"Unknown command: {command}")

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
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    if file and file.filename.endswith('.wav'):
        wav_file_path = 'received_audio.wav'
        file.save(wav_file_path)
        print('Received .wav file, now processing it...')

        response_wav_path = process_audio_file(wav_file_path)
        print('Outputting response audio...')
        return send_file(response_wav_path, mimetype='audio/wav')

    return 'Invalid file format. Only .wav files are accepted.', 400

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
            prompt_question += " commands: 1. turn_on_light  2. turn_off_light " # 3. toggle_light
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
    #writeMemory(start_address, length, 786.78)
    ip = "192.168.1.17"  # Replace with your PLC's IP address
    port = 139  # Modbus TCP port

    client = connect_to_plc(ip, port)
    app.run(host='0.0.0.0', port=8888)
    #plc.disconnect()
    client.close()
    print("Disconnected from PLCSIM")

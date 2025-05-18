from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
from transformers import pipeline
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import difflib

app = Flask(__name__)
CORS(app)


ASL_IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'ASL')


grammar_spell_checker = pipeline(
    "text2text-generation",
    model="prithivida/grammar_error_correcter_v1"
)


def correct_text(input_text):
    result = grammar_spell_checker(
        input_text, max_length=100, num_return_sequences=1)
    text = result[0]['generated_text'].strip()
    print("MODEL OUTPUT:", repr(text))
    
    phrases = [s.strip() for s in re.split(r'[.؟!?,]+', text) if s.strip()]
    unique_phrases = []
    for s in phrases:
        s_lower = s.lower()
        
        if not any(difflib.SequenceMatcher(None, s_lower, up.lower()).ratio() > 0.9 for up in unique_phrases):
            unique_phrases.append(s)
    return '. '.join(unique_phrases)


def get_asl_image_urls(text):
    urls = []
    for word in text.upper().split():
        for char in word:
            if char.isalpha():
                filename = f"{char}.jpg"
                if os.path.exists(os.path.join(ASL_IMAGE_PATH, filename)):
                    urls.append(f"/asl_images/{filename}")
        
        urls.append(None)
    if urls and urls[-1] is None:
        urls.pop()  
    return urls


@app.route('/asl_images/<filename>')
def serve_asl_image(filename):
    return send_from_directory(ASL_IMAGE_PATH, filename)


@app.route('/text-to-asl', methods=['POST'])
def text_to_asl():
    data = request.get_json()
    input_text = data.get('text', '')
    if not input_text:
        return jsonify({'error': 'No text provided'}), 400
    corrected = correct_text(input_text)
    image_urls = get_asl_image_urls(corrected)
    return jsonify({'corrected_text': corrected, 'asl_image_urls': image_urls})


@app.route('/voice-to-asl', methods=['POST'])
def voice_to_asl():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    audio_file = request.files['audio']
    try:
        
        fd, temp_path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)  
        try:
            audio = AudioSegment.from_file(audio_file)
            audio.export(temp_path, format='wav')
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_path) as source:
                audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
            except Exception as e:
                return jsonify({'error': f'Speech recognition failed: {str(e)}'}), 500
        finally:
            os.remove(temp_path)
    except Exception as e:
        return jsonify({'error': f'Audio conversion failed: {str(e)}'}), 500
    corrected = correct_text(text)
    image_urls = get_asl_image_urls(corrected)
    return jsonify({'corrected_text': corrected, 'asl_image_urls': image_urls})


@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'message': 'ASL API is running'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

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
    
    input_text = input_text.strip()
    
    
    words = input_text.split()
    if len(words) <= 2 and all(word.replace(',', '').replace('.', '').isalpha() or word.isdigit() for word in words):
        return input_text
    
    try:
        result = grammar_spell_checker(
            input_text, max_length=150, num_return_sequences=1)
        text = result[0]['generated_text'].strip()
        print("MODEL OUTPUT:", repr(text))
        
        
        if len(text) > len(input_text) * 3:  
            print("Model output too long, using original text")
            return input_text
            
       
        text = re.sub(r'^(Text:|text:)\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'[=]{2,}', '', text)  
        text = re.sub(r'\s+', ' ', text)  
        
        phrases = [s.strip() for s in re.split(r'[.؟!?,]+', text) if s.strip()]
        unique_phrases = []
        for s in phrases:
            s_lower = s.lower().strip()
            
            if not s_lower:
                continue
                
            is_duplicate = False
            for up in unique_phrases:
                up_lower = up.lower().strip()
                similarity = difflib.SequenceMatcher(None, s_lower, up_lower).ratio()
                
                if (similarity > 0.8 or 
                    s_lower in up_lower or 
                    up_lower in s_lower or
                    len(set(s_lower.split()) & set(up_lower.split())) > len(s_lower.split()) * 0.7):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_phrases.append(s)
        
        result_text = '. '.join(unique_phrases)
        
        
        if not result_text or len(result_text.split()) > len(input_text.split()) * 2:
            return input_text
            
        return result_text
        
    except Exception as e:
        print(f"Grammar correction failed: {e}")
        return input_text


def get_asl_image_urls(text):
    urls = []
    for word in text.upper().split():
        for char in word:
            if char.isalnum():  
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
    
    filename = audio_file.filename.lower() if audio_file.filename else ''
    
    try:
        fd, temp_path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        
        try:
            if filename.endswith('.wav'):
                audio_file.save(temp_path)
            else:
                try:
                    audio = AudioSegment.from_file(audio_file)
                    audio.export(temp_path, format='wav')
                except Exception as pydub_error:
                    return jsonify({
                        'error': f'Audio format not supported. Please use WAV files or install ffmpeg. Error: {str(pydub_error)}'
                    }), 400
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)
            
            try:
                text = recognizer.recognize_google(audio_data)
                print(f"Recognized text: {text}")
            except sr.UnknownValueError:
                return jsonify({'error': 'Could not understand the audio. Please speak clearly.'}), 400
            except sr.RequestError as e:
                return jsonify({'error': f'Speech recognition service error: {str(e)}'}), 500
            except Exception as e:
                return jsonify({'error': f'Speech recognition failed: {str(e)}'}), 500
                
        finally:
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return jsonify({'error': f'Audio processing failed: {str(e)}'}), 500
    
    
    corrected = correct_text(text)
    image_urls = get_asl_image_urls(corrected)
    return jsonify({
        'original_text': text,
        'corrected_text': corrected, 
        'asl_image_urls': image_urls
    })


@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'message': 'ASL API is running'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

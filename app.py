from flask import Flask, request, jsonify, render_template, send_file
import speech_recognition as sr
from gtts import gTTS
import os
import time

app = Flask(__name__)

# Create a recognizer instance
r = sr.Recognizer()


def recognize_speech_from_mic(language, duration=5):
    """
    Transcribe speech from recorded from `microphone`.
    Returns a dictionary with three keys:
    "success": a boolean indicating whether or not the API request was
               successful
    "error":   `None` if no error occurred, otherwise a string containing
               an error message if the API could not be reached or
               speech was unrecognizable
    "text":    `None` if speech could not be transcribed,
               otherwise a string containing the transcribed text
    """
    # set up the microphone
    with sr.Microphone() as source:
        print("Please speak now...")
        # read the audio data from the default microphone
        audio_data = r.record(source, duration=duration)  # Record for specified duration
        print("Recognizing...")
        # Convert speech to text
        try:
            # recognize speech using Google Speech Recognition
            text = r.recognize_google(audio_data, language=language)
            return {
                "success": True,
                "error": None,
                "text": text
            }
        except sr.UnknownValueError:
            # speech was unintelligible
            return {
                "success": False,
                "error": "Google Speech Recognition could not understand audio",
                "text": None
            }
        except sr.RequestError as e:
            # API was unreachable or unresponsive
            return {
                "success": False,
                "error": f"Could not request results from Google Speech Recognition service; {e}",
                "text": None
            }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/record', methods=['POST'])
def record():
    language = request.form.get('language')
    duration = int(request.form.get('duration'))
    result = recognize_speech_from_mic(language, duration)
    return jsonify(result)


@app.route('/generate_voice', methods=['POST'])
def generate_voice():
    text = request.form.get('text')
    language = request.form.get('language')
    filename = f"output_{int(time.time())}.mp3"
    if language == "en-US":
        tts = gTTS(text=text, lang='en')
    elif language == "ar-EG":
        tts = gTTS(text=text, lang='ar')
    else:
        return jsonify({"error": "Unsupported language"})
    tts.save(filename)
    return jsonify({"filename": filename})


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded", "text": None})

    file = request.files['file']
    language = request.form.get('language')

    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file", "text": None})

    # Save the uploaded file temporarily
    temp_filename = f"temp_{int(time.time())}.wav"
    file.save(temp_filename)

    # Recognize speech from the uploaded file
    try:
        with sr.AudioFile(temp_filename) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language=language)
            os.remove(temp_filename)  # Remove the temporary file
            return jsonify({"success": True, "error": None, "text": text})
    except sr.UnknownValueError:
        os.remove(temp_filename)  # Remove the temporary file
        return jsonify(
            {"success": False, "error": "Google Speech Recognition could not understand audio", "text": None})
    except sr.RequestError as e:
        os.remove(temp_filename)  # Remove the temporary file
        return jsonify(
            {"success": False, "error": f"Could not request results from Google Speech Recognition service; {e}",
             "text": None})


@app.route('/download/<filename>')
def download(filename):
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
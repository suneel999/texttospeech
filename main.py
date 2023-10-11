from flask import Flask, render_template, request
import requests
import pandas as pd
import json
app = Flask(__name__)
url = "https://api.elevenlabs.io/v1/voices"

headers = {
  "Accept": "application/json",
  "xi-api-key": "e327fdf320043677a512f1b0dade8403"
}

response = requests.get(url, headers=headers)
json_response = response.text
data = json.loads(json_response)

# Extract the 'voices' data
voices = data.get('voices', [])

# Convert the data into a DataFrame
df = pd.DataFrame(voices)
@app.route('/')
def index():
    data = json.loads(json_response)
    voices = data.get('voices', [])
    return render_template('index.html', voices=voices)


@app.route('/convert', methods=['POST'])
def convert():
    voice_id = request.form['voice_id']
    text = request.form['text']
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": "e327fdf320043677a512f1b0dade8403"  # Replace with your actual API key
    }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        with open('static/output.mp3', 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        message = "Text-to-speech conversion successful. Output saved as 'output.mp3'."
    except requests.exceptions.HTTPError as errh:
        message = f"HTTP Error: {errh}"
    except requests.exceptions.ConnectionError as errc:
        message = f"Error Connecting: {errc}"
    except requests.exceptions.Timeout as errt:
        message = f"Timeout Error: {errt}"
    except requests.exceptions.RequestException as err:
        message = f"Something went wrong: {err}"

    return render_template('index.html', message=message)


if __name__ == '__main__':
    app.run(debug=True)

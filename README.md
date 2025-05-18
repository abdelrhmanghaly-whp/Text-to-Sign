# ASL Text & Speech to Sign API

This project converts text or speech input into American Sign Language (ASL) finger spelling images. It provides endpoints for both text and audio input, returning the corrected text and a list of image URLs for each letter.

## Setup Instructions

### 1. Clone the Repository
Clone this repository to your local machine.

### 2. Install Python Requirements
Make sure you have Python 3.10+ installed. Then, install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Download ASL Images
Place your ASL alphabet images (A.jpg, B.jpg, ..., Z.jpg) in a folder named `ASL` inside the project directory.

### 4. Run the API
You can run the API using Flask for development:
```bash
python app.py
```
Or with Gunicorn for production (if you have it installed):
```bash
gunicorn app:app --bind 0.0.0.0:5000 --timeout 300 --workers 1
```

### 5. (Optional) Run with Docker
Build and run the Docker container:
```bash
docker build -t asl-api .
docker run -p 5000:5000 asl-api
```

## How to Test with Postman

### Text to ASL
1. Set method to POST and URL to `http://localhost:5000/text-to-asl`.
2. In the Body tab, select `raw` and choose `JSON`.
3. Enter:
    ```json
    { "text": "hello i am ghaly, and i am 15 years old" }
    ```
4. Click Send. You will receive the corrected text and image URLs.

#### Example Output
```json
{
  "corrected_text": "hello i am ghaly, and i am 15 years old, and i love math",
  "asl_image_urls": [
    "/asl_images/H.jpg",
    "/asl_images/E.jpg",
    "/asl_images/L.jpg",
    ...
  ]
}
```

### Voice to ASL
1. Set method to POST and URL to `http://localhost:5000/voice-to-asl`.
2. In the Body tab, select `form-data`.
3. Add a key named `audio` (type: File) and upload your audio file (WAV or MP3).
4. Click Send. You will receive the recognized and corrected text and image URLs.

### Get ASL Image
- Open `http://localhost:5000/asl_images/A.jpg` in your browser to view the image for the letter A.

## Input and Expected Output
- **Input:** Any English sentence or paragraph (text or speech).
- **Output:**
  - `corrected_text`: The input, grammar-corrected and deduplicated (no repeated or near-duplicate sentences).
  - `asl_image_urls`: List of URLs for each letter in the corrected text, with `null` separating words.

## Notes
- The API corrects grammar and removes repeated or near-duplicate phrases from input.
- For best results with audio, use clear speech and supported formats (WAV/MP3).
- The API returns a list of image URLs for each letter in the corrected text, with `null` separating words.

---

For any issues or questions, please contact the backend developer. 

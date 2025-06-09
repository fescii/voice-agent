# Ringover Streamer

## Description
This project provides a complete implementation of a websocket streamer for Ringover.
It includes a lot of event you can use to interact with the server like a voicebot.

## Features
- A websocket streaming server to revceive realtime RTP from Ringover media servers.
- Respond directly by sending events and transform the streamer to a real voicebot

## Prerequisites
- Python 3.8+
- pip (https://pip.pypa.io/en/stable/)

## Installation
1. Clone the repository:
```
git clone <repository-url>
```

3. Navigate to the project directory:
```
cd <project-directory>
```

4. Install the dependencies:
```
pip install -r requirements.txt
```

## Running the Application
Start the application using Uvicorn:

```
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
or
```
python app.py
```

## Available Responses

### Play
Websocket server may return JSON object containing audio url to be played by the user. To use this feature, response must follow the format:
```
{
  "event": "play",
  "file": "https://test.com/test.mp3"
}
```

### Stream
You can also do streaming with base64 encoded audio. To use this feature, response must follow the format:
```
{
  "type": "streamAudio",
  "data": {
    "audioDataType": "raw",                      # raw | mp3 | wav | ogg
    "sampleRate": 8000,                          # 8000 | 16000 | 24000
    "audioData": "base64 encoded audio"
  }
}
```

### Break
You can also stop the current streaming by sending a break event.
```
{
  "event": "break"
}
```

### Digits
You may want to send digits to respond to an IVR.
```
{
  "event": "digits",
  "data": 123
}
```

### Transfer
Finally, to transfer a call to an agent, you can put his number into the response.
```
{
  "event": "transfer",
  "data": number
}
```

## License
This project is licensed under the BSD License. See the LICENSE file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Author
Made with Love by Ringover for his customers.
If you do great things with that, feel free to contact us. We have a lot of positions opened.

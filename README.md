# gii-server

This is the transcription server for gii, which lets us easily cache transcriptions as well as not force users to keep track of their own API keys.

## Usage

To run the app, simply install the requirements with `pip install -r requirements.txt`, and then run with `python app.py`. By default, it listens on port 2000. If you want to run in HTTPS, simply pass it a private key and certificate file in that order in the command line. 

The API is quite simple. The only route is '/' and the allowed methods are GET (which will get you a short sentence directing you to this repo) and POST. The json sent with the POST request should look like this: 

    {
        "secret": "secret value, must also be set on the server",
        "url":"http://example.com/example.png"
    }

The API will return one of two things: If the request is erroneous somehow, it will return this:

    {
        "error": "Wrong server secret"
    }

The HTTP response code will be 400. If everything went well, the response will look like this:

    {
        "confidence": 1.0,
        "description": "example description",
        "text": "example text found in image"
    }

The HTTP response code in this case will be 200.

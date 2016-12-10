from flask import Flask, jsonify, request
from gii_keys import mskey, gcvkey, secret
from base64 import b64encode
from re import sub as replace
from hashlib import sha1
from ratelimit import *
import json, requests, pprint, urllib2, sqlite3

app = Flask(__name__)

# This function calls the google OCR API. It's limited to 10 requests a second.
# It takes in two dicts, one for the URL parameters, and one of the json POST
# payload itself. Note that the return can be the empty string if no text
# is found by Google's API.
@rate_limited(10)
def call_google(params, json):
    gcr = requests.post('https://vision.googleapis.com/v1/images:annotate',
                        params=params, json=json)
    try:
        gc_response = json.loads(gcr.content)['responses'][0]
        text = gc_response['textAnnotations'][0]['description']
        text = replace(r"(\r\n|\n|\r)", " ", text)
    except KeyError as e:
        text = ""
    return text

# This function calls the Microsoft API, which is limited to 10 requests/sec.
# It takes in three dicts, one for the headers, one for the URL parameters,
# and one for the json POST payload itself.
@rate_limited(10)
def call_microsoft(headers, params, json):
    msr = requests.post('https://api.projectoxford.ai/vision/v1.0/analyze',
                        headers=headers, params=params, json=payload)
    ms_response = json.loads(msr.content)['description']
    description = ms_response['captions'][0]['text']
    confidence = ms_response['captions'][0]['confidence']
    return description, confidence

# This is the only route for this application, there's really no need for 
# anything else - the application itself is almost completely stateless
@app.route('/', methods = ['POST', 'GET'])
def transcribe():
    if request.method == 'POST':
        # Get DB connection and request data
        conn = sqlite3.connect('cache.db')
        c = conn.cursor()
        requestdictjson = list(request.form)[0]
        requestdict = json.loads(requestdictjson)
        url = requestdict['url']
        # Check secret against the one from disk
        if secret != requestdict['secret']:
            return jsonify({'error': 'Wrong server secret'}), 400

        # Load the image - we need it for hashing and for the google API.
        imgreq = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        imgdata = urllib2.urlopen(imgreq).read()
        imghash = sha1(imgdata).hexdigest()

        # Check if the data is in the cache
        c.execute("select hash from cache where hash='{}'".format(imghash))
        if not c.fetchall():
            # Cache miss - generate dicts for API calls
            headers = {
                    'Content-Type': 'application/json',
                    'Ocp-Apim-Subscription-Key': mskey
                    }
            params = {
                    'visualFeatures': 'Description'
                    }
            payload = {
                    'url': url
                    }

            (description, confidence) = call_microsoft(headers, params, payload)

            params = {
                    'key': gcvkey
                    }

            payload = { 
                        'requests': [{
                            'image': {
                                'content': b64encode(imgdata)
                            },
                            'features': {
                                'type': 'TEXT_DETECTION',
                                'maxResults': '200'
                            }
                        }]
                    }
            text = call_google(params, payload)

            # Add data to cache
            c.execute("insert into cache values ('{}', '{}', '{}', '{}')"
                            .format(imghash, description, confidence, text))
            conn.commit()
        else:
            # Cache hit, load the data from the cache
            c.execute("select * from cache where hash='{}'".format(imghash))
            (hashval, description, confidence, text) = c.fetchall()[0]
        # Return a json dict of the 3 values
        return jsonify({
                    'description': description,
                    'confidence': confidence,
                    'text': text
                    })
    else:
        # In case someone browses to the API with a web browser, show a
        # useful message instead of just a useless 404 page.
        return "Welcome to the GII transcription API. Find code <a href='http"\
               "s://github.com/narenniranjan/gii-server'>here.</a>"

if __name__ == "__main__":
    app.run(debug=True)

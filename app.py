from flask import Flask, jsonify, request
from gii_keys import mskey, gcvkey, secret
from base64 import b64encode
from re import sub as replace
from hashlib import sha1
import json, requests, pprint, urllib2, sqlite3

app = Flask(__name__)

@app.route('/', methods = ['POST', 'GET'])
def transcribe():
    if request.method == 'POST':
        conn = sqlite3.connect('cache.db')
        c = conn.cursor()
        requestdictjson = list(request.form)[0]
        requestdict = json.loads(requestdictjson)
        url = requestdict['url']
        if secret != requestdict['secret']:
            return jsonify({'error': 'Wrong server secret'}), 400
        imgreq = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        imgdata = urllib2.urlopen(imgreq).read()
        imghash = sha1(imgdata).hexdigest()
        c.execute("select hash from cache where hash='{}'".format(imghash))
        if not c.fetchall():
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
            msr = requests.post('https://api.projectoxford.ai/vision/v1.0/analyze', headers=headers, params=params, json=payload)
            ms_response = json.loads(msr.content)['description']
            description = ms_response['captions'][0]['text']
            confidence = ms_response['captions'][0]['confidence']

            params = {
                    'key': gcvkey
                    }

            payload = { 'requests': [{
                            'image': {
                                'content': b64encode(urllib2.urlopen(imgreq).read())
                                },
                            'features': {
                                'type': 'TEXT_DETECTION',
                                'maxResults': '200'
                                }
                            }
                        ]
                    }
            gcr = requests.post('https://vision.googleapis.com/v1/images:annotate', params=params, json=payload)
            try:
                gc_response = json.loads(gcr.content)['responses'][0]
                text = gc_response['textAnnotations'][0]['description']
                text = replace(r"(\r\n|\n|\r)", " ", text)
            except KeyError as e:
                text = ""
            c.execute("insert into cache values ('{}', '{}', '{}', '{}')".format(imghash, description, confidence, text))
            conn.commit()
        else:
            c.execute("select * from cache where hash='{}'".format(imghash))
            (hashval, description, confidence, text) = c.fetchall()[0]
        return jsonify({'description': description, 'confidence': confidence, 'text': text})
    else:
        return "Welcome to the GII transcription API."

if __name__ == "__main__":
    app.run(debug=True)

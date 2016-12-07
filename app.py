from flask import Flask, jsonify, request
from gii_keys import mskey, gcvkey, secret
from base64 import b64encode
from re import sub as replace
import json, requests, pprint, urllib2

app = Flask(__name__)

@app.route('/', methods = ['POST', 'GET'])
def transcribe():
    if request.method == 'POST':
        requestdictjson = list(request.form)[0]
        requestdict = json.loads(requestdictjson)
        url = requestdict['url']
        if secret != requestdict['secret']:
            return jsonify({'error': 'Wrong server secret'}), 400
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

        imgreq = urllib2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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
        return jsonify({'description': description, 'confidence': confidence, 'text': text})
    else:
        return "Welcome to the GII transcription API."

if __name__ == "__main__":
    app.run(debug=True)

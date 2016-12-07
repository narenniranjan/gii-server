from flask import Flask, jsonify, request
from gii_keys import mskey, gcvkey, secret
import json, requests, pprint

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
        return jsonify({'description': description, 'confidence': confidence})
    else:
        return "Welcome to the GII transcription API."

if __name__ == "__main__":
    app.run(debug=True)

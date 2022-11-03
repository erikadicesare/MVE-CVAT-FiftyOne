import os, json
from flask import render_template,request, jsonify
from app import app
import requests

@app.route("/login", methods=['POST', 'GET'])
def login():
      d ={
            "username": "django",
            "email": "",
            "password": "tarantino"
      }
      
      #data.jsonify()
      #print(d) 
      req = requests.post('http://localhost:8080/api/v1/auth/login', json= d)
      #token = req.key
      jsonObj = json.loads(req.text)
      keyLogin = jsonObj['key']
      print(jsonObj['key'])  
  
      req2 = requests.get('http://localhost:8080/api/v1/tasks', headers={"Authorization": f'Token {keyLogin}'})
      print(req2.text)
      data = {
            "chunk_size": 2147483647,
            "size": 2147483647,
            "image_quality": 100,
            "start_frame": 2147483647,
            "stop_frame": 2147483647,
            "frame_filter": "string",
            "compressed_chunk_type": "video",
            "original_chunk_type": "video",
            "client_files": [ ],
            "server_files": [ ],
            "remote_files": [ ],
            "use_zip_chunks": false,
            "cloud_storage_id": 0,
            "use_cache": false,
            "copy_data": false,
            "storage_method": "cache",
            "storage": "cloud_storage",
            "sorting_method": "lexicographical"
      }
      #req2 = requests.get('https://app.cvat.ai/api/tasks/107/data/', json=data)
      print(req2.text)
      
      
      return render_template('index.html')

@app.route("/", methods=['GET'])
def index():
      req = requests.get('https://app.cvat.ai/api/tasks')
      print(req.content)
      return render_template('index.html')
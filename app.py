from flask import Flask, request, redirect, render_template
import json
import requests
import pymongo
from pymongo.errors import DuplicateKeyError

app = Flask(__name__)

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client.get_database("Git_Info")
user_collection = db.get_collection("test")
repo_collection = db.get_collection("test")


import datetime

def fix_datetime_fields(json_obj):
    """
    Converts any datetime strings in a JSON object to Python datetime objects.
    Returns a new JSON object with the fixed fields.
    """
    fixed_obj = {}
    for key, value in json_obj.items():
        if isinstance(value, str):
            try:
                parsed_date = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
                fixed_obj[key] = parsed_date
            except ValueError:
                fixed_obj[key] = value
        # elif isinstance(value, dict):
        #     fixed_obj[key] = fix_datetime_fields(value)
        else:
            fixed_obj[key] = value
    return fixed_obj



@app.route('/')
def index():
    return redirect('/git_user')

@app.route('/giit_user')
def giit_user():
    return render_template('index.html')

@app.route('/git_data', methods=['POST'])
def git_data():
    if request.method == 'POST':
        data = json.loads(request.data)
        username = data['prof']
        user_url = f"https://api.github.com/users/{username}"
        repo_url = f"https://api.github.com/users/{username}/repos"
        
        user_response = requests.get(user_url)
        if user_response.status_code == 200:
            user= user_response.json()
            user_data = fix_datetime_fields(user)
            # print(user_data)

            user_id = user_data['login']
            user_data['_id'] = user_id
            
            try:
                user_collection.insert_one(user_data)
                user_data['Source'] = 'Git API'
            except DuplicateKeyError:
                user_data = user_collection.find_one({"_id": user_id})
                user_data['Source'] = 'MongoDB'
                # print(user_data)
                
            repo_response = requests.get(repo_url)
            if repo_response.status_code == 200:
                repo_data = repo_response.json()
                repo_data = [fix_datetime_fields(repo) for repo in repo_data]
                
                print(repo_data[0])
                for repo in repo_data:
                    # print(repo)

                    repo_id = repo['name']
                    repo['_id'] = f'{user_id}({repo_id})'
                    # repo_collection.delete_many()
                    # repo_id = repo['id']
                    try:
                        repo_collection.insert_one(repo)
                        repo['Source'] = 'Git API'
                    except DuplicateKeyError:
                        repo = repo_collection.find_one({'_id': f'{user_id}({repo_id})'})
                        repo['Source'] = 'MongoDB'
                return {'user_data': user_data, 'repo_data': repo_data}
            else:
                return {'Error': repo_response.status_code}
        else:
            return {'Error': user_response.status_code}

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify
from flask import send_from_directory
import os
import pickle
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests



def download_model():
    file_id = "1_sGbZtAFzZiDwGJqpWe2eaxt8mkxzzzq"  # your actual file ID
    output_path = "artifacts_new.pkl"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    if not os.path.exists(output_path):
        print("Downloading model from Google Drive...")
        r = requests.get(url)
        with open(output_path, "wb") as f:
            f.write(r.content)

download_model()

with open('artifacts_new.pkl', 'rb') as f:
    new, cv, vector, similarity = pickle.load(f)
    
app = Flask(__name__)
CORS(app)
load_dotenv()  
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
if not OMDB_API_KEY:
    raise ValueError("OMDB_API_KEY environment variable not set. Please create a .env file with your OMDb API key.")

print("Loaded new_sample:")
print(new.head(20))
print("\nAll titles in new_sample:")
print(new["title"].str.strip().values)

def omdb_poster(movie_title):
     base_url = "http://www.omdbapi.com/"
     params = {
        "apikey": OMDB_API_KEY,
        "t": movie_title,
        "r": "json"  # Response format: JSON
     }
     response=requests.get(base_url,params=params)
     data = response.json()
     if data:
         poster_url=data.get("Poster")
         if poster_url == "N/A":
                return None
         return poster_url
     else:
         print(f"OMDb data not found for '{movie_title}': {data.get('Error', 'Unknown error')}")
         return None
    
@app.route('/')
def serve_index():
    return send_from_directory('build', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('build', path)

@app.route("/recommend",methods=["POST"])
def recommend():
    data = request.json
    if not data or 'movie' not in data:
         return jsonify({'error': 'Missing "movie" in request body'}), 400
    
    movie = data['movie'].strip().lower()
    new['title_lower'] = new['title'].str.strip().str.lower()
    print(f"\nReceived request for movie: '{movie}'")
    
    if movie not in new["title_lower"].str.strip().values:
        return jsonify({'error': f'Movie "{movie}" not found'}), 404
    
    try:
        idx = new[new['title_lower'].str.strip() == movie].index[0]
        distances = list(enumerate(similarity[idx]))
        movie_list = sorted(distances, key=lambda x: x[1], reverse=True)[1:6]
        recommended_movies_data = []
        # recommend = [new.iloc[i[0]]["title"] for i in movie_list]  
        # poster_url = omdb_poster(recommend)
        for i in movie_list:
            recommend = new.iloc[i[0]]["title"]
            poster_url = omdb_poster(recommend)
            recommended_movies_data.append({
                "title": recommend,
                "poster_url": poster_url
            })
            print(f"Recommendations: {recommend}")
            
        print(f"Recommendations with OMDb data: {recommended_movies_data}")
        return jsonify({'recommendations': recommended_movies_data})
    except IndexError:
        return jsonify({'error': f'Could not find index for movie "{movie}"'}), 500

if __name__ == '__main__':
    app.run(port=5000)

from flask import Flask, render_template, request, jsonify
import pickle
import requests
import pandas as pd

app = Flask(__name__)

movies = pickle.load(open('movies_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path

def recommend_by_title(movie_title):
    movie_title = movie_title.lower()
    index = movies[movies['title'].str.lower() == movie_title].index

    if not index.empty:
        index = index[0]
        distance = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])

        recommend_movie = []
        recommend_poster = []

        for i in distance[1:11]:  
            recommend_movie.append(movies.iloc[i[0]].title)
            recommend_poster.append(fetch_poster(movies.iloc[i[0]].id))

        return recommend_movie, recommend_poster
    else:
        return [], []


def recommend_by_year(release_year):
    movies_in_year = movies[movies['release_date'] == str(release_year)].head(10) 
    if not movies_in_year.empty:
        recommend_movie = list(movies_in_year['title'])
        recommend_poster = [fetch_poster(row['id']) for _, row in movies_in_year.iterrows()]
    else:
        recommend_movie, recommend_poster = [], []

    return recommend_movie, recommend_poster


def recommend_by_genre(input_genre):
    input_genre = input_genre.lower()
    
    movies_with_genre = movies[movies['tags'].str.contains(input_genre)].head(10)  
    
    if not movies_with_genre.empty:
        recommend_movie = []
        recommend_poster = []

        for index, row in movies_with_genre.iterrows():
            recommend_movie.append(row['title'])
            recommend_poster.append(fetch_poster(row['id']))
        
        return recommend_movie, recommend_poster
    else:
        print(f"No movies found for the genre {input_genre}")
        return [], []

def recommend_movies(input_value):
   
    if str(input_value).lower() in movies['genre'].str.lower().unique():
        
        return recommend_by_genre(str(input_value))
    else:
        try:
            
            year = int(input_value)
            return recommend_by_year(year)
        except ValueError:
           
            return recommend_by_title(str(input_value))

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    status = False

    if request.method == "POST":
        try:
            if request.form:
                movies_name = request.form['movies']
                recommended_movies_name, recommended_movies_poster = recommend_movies(movies_name)
                status = True
                min_length = len(recommended_movies_name)

                return render_template("prediction.html",
                                       movies_name=recommended_movies_name,
                                       poster=recommended_movies_poster,
                                       movie_list=movies,
                                       status=status,
                                      min_length=min_length,
                                       )

        except Exception as e:
            error = {'error': e}
            return render_template("prediction.html", error=error, movie_list=movies, status=status)

    else:
        return render_template("prediction.html", movie_list=movies, status=status)

@app.route('/load_one_movie', methods=['GET'])
def load_one_movie():
    # Get the current page number from the query parameters
    page = request.args.get('page', type=int)

    # Set the limit for the number of movies to be fetched
    limit = 52

    # Get the next movie based on the page number
    movie_index = page * 1  # Fetch one movie at a time

    if movie_index < len(movies) and movie_index < limit:
        movie = movies.iloc[movie_index]

        try:
            # Fetch the poster for the current movie
            poster_path = fetch_poster(movie['id'])

            # Convert the data to JSON and return it
            data = {
                'title': movie['title'],
                'poster_path': poster_path
            }
            return jsonify(data)

        except Exception as e:
            # Log the error and return an empty response
            print(f"Error fetching poster for movie '{movie['title']}': {str(e)}")
            return jsonify({})

    else:
        # No more movies to fetch
        return jsonify({})



if __name__ == '__main__':
    app.debug = True
    app.run()

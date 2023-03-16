from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from savalidation import ValidationMixin
from datetime import datetime
from models.db import db
from models.users import User, Movie
# db = SQLAlchemy()
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def create_app():

    app = Flask(__name__)
    app.secret_key = 'your secret key'
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root@localhost:3306/move_recommendation"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app._static_folder = "/home/dhanesh/PycharmProjects/movieRecommendation/static"
    with app.app_context():
        print("INit App===========")
        db.init_app(app)
        db.create_all()
    # db.init_app(app)
    # db.create_all()
    # app.config["DEBUG"] = os.environ.get("DEBUG", True)
    # app.config["USE_PDB"] = os.environ.get("USE_PDB", False)
    # app.config['SECRET_KEY'] = 'this needs to be moved out of this file'
    # app.config['REMEMBER_COOKIE_NAME'] = 'same_with_this'
    # app.config['STRIPE_KEY'] = os.environ.get('STRIPE_KEY')
    return app

app = create_app()
migrate = Migrate(app, db)
movies = pd.read_csv("/home/dhanesh/Downloads/ml-25m (1)/ml-25m/movies.csv")
rating = pd.read_csv("/home/dhanesh/Downloads/ml-25m (1)/ml-25m/ratings.csv")

@app.route('/rating/', methods=['GET', 'POST'])
def movie_rating():
    print("Movie Rating form data ===: ", request.form)
    msg = ""
    if request.method == 'POST' and 'rating' in request.form:
        rating = request.form['rating']
        movie_id = request.form['movie_id']
        for ind, val in enumerate(session.get("movie_data")):
            if str(val.get('movieId')) == movie_id:
                session["movie_data"][ind]['rating'] = rating
                title = session["movie_data"][ind]['title']
                upd_movie = Movie.query.filter_by(movie_id=val["movieId"], user_id=session['id']).first()
                if upd_movie:
                    upd_movie.rating = rating
                    db.session.commit()
                else:
                    movie = Movie(movie_id=movie_id, title=title, rating=rating, user_id=session['id'])
                    db.session.add(movie)
                    db.session.commit()
                break
        return render_template('index.html', result=session["movie_data"])
# @app.route('/movie/<string:title>/', methods=['GET', 'POST'])
@app.route('/movie/', methods=['GET', 'POST'])
def movie_view():
    title = request.args.get("title")
    movie_id = request.args.get("movie_id")

    return render_template('rating.html', title=title,movie_id=movie_id)


@app.route('/search', methods =['GET', 'POST'])
def search():
    print("Search form data ===: ", request.form)
    msg = ""
    if request.method == 'POST' and 'search' in request.form:
        title = request.form['search']
        if len(title) >= 5:
            # msg = "move name found"
            top_five = recommendation_movies_by_title(title=title,movies=movies)
            result = find_similar_movies(movie_id=top_five.iloc[0]["movieId"],movies=movies,rating=rating)
            # import pdb;pdb.set_trace()
            # data = {}
            # for i in result:
            #     import pdb;pdb.set_trace()
            #     if i["movieId"] not in data:
            #         data[i["movieId"]] = i["title"]

            print("result ======= ", result.to_dict('records'))
            data = result.to_dict('records')
            for ind, val in enumerate(data):
                movie = Movie.query.filter_by(movie_id=val["movieId"],user_id=session['id']).first()
                if movie:
                    data[ind]["rating"] = movie.rating
            # import pdb;pdb.set_trace()
            # print("data==== ",data)
            session['movie_data'] = data
            return render_template('index.html', result=data)

    return render_template('index.html', msg="Move name at least 5 letters")

# @app.route('/')
@app.route('/register', methods =['GET', 'POST'])
def register():


    print("Register form data ===: ",request.form)
    msg = ""
    # from models.users import User
    if request.method == 'POST' and 'username' in request.form\
            and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            msg = 'Account already exists !'
            # return render_template('register.html', msg=msg)
        # elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        #     msg = 'Invalid email address !'
        # elif not re.match(r'[A-Za-z0-9]+', username):
        #     msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            msg = 'You have successfully registered !'
            me = User(username=username, email=email, password=password)
            db.session.add(me)
            db.session.commit()
            return render_template('login.html', msg=msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg=msg)

@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    # from models.users import User
    # rating(1)
    msg = ''
    print("Login API Call: ",request.form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        # email = request.form['email']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.username
            msg = 'Logged in successfully !'
            return render_template('index.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)

def recommendation_movies_by_title(title,movies):
    # movies = pd.read_csv("/home/dhanesh/Downloads/ml-25m (1)/ml-25m/movies.csv")

    movies["clean_title"] = movies["title"].apply(clean_title)

    vectorizer = TfidfVectorizer(ngram_range=(1,2))
    tfidf = vectorizer.fit_transform(movies['clean_title'])
    #
    # title = "Harry Potter"
    title = clean_title(title)
    query_vec = vectorizer.transform([title])
    similarity = cosine_similarity(query_vec, tfidf).flatten()
    indices = np.argpartition(similarity,-5)[-5:]
    result = movies.iloc[indices][::-1]
    # result = result['clean_title'].tolist()

    return result

def find_similar_movies(movie_id,movies,rating):
    # movies = pd.read_csv("/home/dhanesh/Downloads/ml-25m (1)/ml-25m/movies.csv")

    movies["clean_title"] = movies["title"].apply(clean_title)

    # rating = pd.read_csv("/home/dhanesh/Downloads/ml-25m (1)/ml-25m/ratings.csv")


    similar_users = rating[(rating["movieId"] == movie_id) &
                           (rating["rating"] > 4)]["userId"].unique()
    similar_user_recs = rating[(rating["userId"].isin(similar_users)) &
                               (rating["rating"] > 4)]["movieId"]

    similar_user_recs = similar_user_recs.value_counts() / len(similar_users)
    similar_user_recs = similar_user_recs[similar_user_recs > .10]

    all_users = rating[(rating["movieId"].isin(similar_user_recs.index)) &
                       (rating["rating"] > 4)]
    all_users_recs = all_users["movieId"].value_counts() / len(all_users["userId"].unique())

    rec_percentage = pd.concat([similar_user_recs,all_users_recs], axis=1)
    rec_percentage.columns = ["similar", "all"]

    rec_percentage["score"] = rec_percentage["similar"] / rec_percentage["all"]

    rec_percentage = rec_percentage.sort_values("score", ascending=False)
    return rec_percentage.head(10).merge(movies,left_index=True, right_on="movieId")[["title","movieId"]]


def clean_title(title):
    return re.sub("[^a-zA-Z0-9 ]","",title)
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # print_hi('PyCharm')
    # login()


    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/




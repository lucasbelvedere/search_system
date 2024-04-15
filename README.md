# Search System in Python

A search system/engine, that works by populating a NoSQL database (MongoDB) with an inverted index to keep track of every token, and in which crawled file it is located at. The database also keeps information such as the term frequency (used later to calculate TF-IDF,) indexes of a term, and the relevance of a term within a file.

After populating the database with the inverted index, if you already have all the requirements below installed (including the websites crawled from the "data" directory,) you can go ahead and run the following command.

```
python3 app.py
```

This will start your application. The project was build with Flask as the backend, and uses first a GET method to fetch the index.html page. Based on the user's query, the program then uses the POST method together with the id (query) to tokenize, lemmatize, calculate TF-IDF of each token in the query, and use cosine similarity to rank and return the 20 best pages to the user.

# Requirements
Before you run the system, please make sure that you have an Ubuntu container. Then, run the following commands in your terminal.

```
pip install beautifulsoup4
pip install pymongo
pip install nltk
pip install Flask
pip install Flask-WTF
pip install numpy
pip install scipy
```

The commands above will install the libraries `BeautifulSoup`, `PyMongo`, `NLTK`, `Flask`, `Flask-WTF`, `Numpy`, and `Scipy`.

You could also run the following.

```
pip install scikit-learn
```

# Webpages Colletion

To be added...

# Demo Video

To be added...

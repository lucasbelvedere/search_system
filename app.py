from flask import Flask, render_template, flash, redirect, url_for, request
from pymongo import MongoClient  # Corrected import
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
# import InvertedIndex
from SearchEngine import *
import os

SECRET_KEY = os.urandom(32)

class BasicForm(FlaskForm):
    ids = StringField("ID", validators=[DataRequired()])
    submit = SubmitField('Search')

class SearchEngineGUI:
    def __init__(self):
        self.engine = SearchEngine()  # Initialize the SearchEngine instance
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = SECRET_KEY
        self.setup_routes()
        self.app.run(debug=True)

    def setup_routes(self):
        @self.app.route("/", methods=['GET'])
        def home():
            form = BasicForm()
            return render_template('index.html', form=form)

        @self.app.route("/search", methods=['GET', 'POST'])
        def search():
            form = BasicForm()
            if form.validate_on_submit():
                input_id = form.ids.data
                search_results = self.engine.run_engine(input_id)  # Assume this returns a list of URLs
                flash(f'ID submitted: {input_id}', 'success')
                # Render a template directly with search results
                return render_template('search_results.html', form=form, search_results=search_results)
            else:
                # If it's a GET request, just show the form
                return render_template('index.html', form=form)

if __name__ == "__main__":
    SearchEngineGUI()
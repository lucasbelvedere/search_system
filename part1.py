from bs4 import BeautifulSoup
# from pymongo import MongoClient
import re
import os
import json
import math
import sqlite3

# Natural language library that will be used.
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk import pos_tag
from nltk.tokenize import word_tokenize

# nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('stopwords')
# nltk.download('punkt')

class search_system_index_gen:
    '''
    A complete inverted index generator for a search system.
    '''
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.inverted = {} # Empty dictionary that will contain dictionaries within each token.
        self.words_per_doc = {} # Empty dictionary that  will contain document as key and number of words as value.
        self.num_docs = 0
        self.stop_words = set(stopwords.words('english'))

        '''
        TODO: FOR MILESTONE 2, CHANGE DICTIONARY TO LIST FOR POSTING
        FOR THURSDAY, MAYBE JUST IMPLEMENT A SEARCH SYSTEM WITH A WHILE(TRUE) LOOP. EVERY TIME YOU SEARCH SOMETHING,
        THIS GOES ON INTO A FILE.
        ALSO, IMPLEMENT IT AS A CLASS CALLED SEARCH_ENGINE AND CHANGE THIS ONE TO INVERTED_INDEX (OUTPUTS), 
        AND CHECK IF INVERTED_INDEX IS WITHIN YOUR DOCS. IF NOT, YOU RUN THIS CLASS, OTHERWISE JUST OPENS THE JSON
        FILE CALLED OUTPUTS.
        SELF.INVERTED{ "token1" : {
                                    "doc1" : {
                                                "frequency" : 3,
                                                "Indeces" : 1, 3
                                                "tfidf": 0.24
                                                "relevance": 8
                                             }
                                   }
                      }
        '''
    

    def __parse_html(self, path: str, key: str):
        '''
        Takes a path to an html file. Parses the html, __tokenizes the content of the page, \
        and key value of the document which is a string containing the folder number and the \
        number of the document within that folder.
        '''
        try:
            with open(path, 'r', encoding='utf-8') as file:
                # print("Fuck")
                # TODO: CHANGE HTML PARSER TO XML?
                soup = BeautifulSoup(file, 'html.parser')
                list_tags = soup.findAll()
                content = soup.get_text() # gets all the text content of page without html tags.
                content = word_tokenize(content) # __tokenize all possible tokens; for the search system, we will consider tokens that have alphanumeric characters also tokens.
                content = [word.lower() for word in content if word.lower() not in self.stop_words]

                has_content = False
                self.words_per_doc[key] = len(content) # counts how many words there is to be used in the future with a more complex tf-idf search tool.

                if content is None:
                    return None, None
                else:
                    word_index_doc = 1 # index used to check what position is that word within a page.
                    for tag in list_tags:
                        relevance = 0 # basic heuristics for milestone 1 will be a relevance level that will be higher based on frequency and tag that a word is.
                        tag_name = str(tag.name).lower()
                        # tags that were choosen arbitrarily. Comment out to test if a tag should/shouldn't be relevanced.
                        if tag_name == 'h1':
                            relevance += 5
                        elif tag_name == 'h2':
                            relevance += 4
                        elif tag_name == 'h3':
                            relevance += 3
                        elif tag_name == 'h4' or tag_name == 'h5' or tag_name == 'h6':
                            relevance += 2
                        elif tag_name == 'p':
                            relevance += 1

                        if relevance > 0:
                            has_content = True
                            tag_content = word_tokenize(tag.get_text())
                            tag_content = [word.lower() for word in tag_content if word.lower() not in self.stop_words]
                            for token in tag_content:
                                if token not in self.inverted:
                                    self.inverted[token] = {key: {"frequency": 1, "indeces": [word_index_doc], "relevance": relevance}}
                                else:
                                    if key not in self.inverted[token]:
                                        self.inverted[token][key] = {"frequency": 1, "indeces": [word_index_doc], "relevance": relevance}
                                    else:
                                        self.inverted[token][key]["frequency"] += 1
                                        self.inverted[token][key]["indeces"].append(word_index_doc)
                                        self.inverted[token][key]["relevance"] += relevance
                                word_index_doc += 1  # Ensure this increment is correctly placed to reflect the overall document indexing
                    
                    if has_content:
                        self.num_docs += 1
                    return
                
        except Exception as e:
            print(f"There was an error trying to process the file in the path {path}. \n \
                The following exception was thrown: {str(e)}.")
            return
        
    def _load_json_file(self, path: str):
        '''
        Opens and returns a json file.
        '''
        try:
            with open(path, 'r') as file:
                json_file = json.load(file)
                return json_file
        except Exception as e:
            print(f"There was an error trying to process the file in the path {path}. \n \
                The following exception was thrown: {str(e)}.")
            return
        
    def run_search_system(self, path:str, extension=''):
        '''
        Takes a path_file, which is a path to a json file containing keys that are \
        an extension that will be joined with the path of a url and the url as a value. \
        Extension is an optional string that will be used if user has a specific path to \
        look for the urls.

        extension in our case should be ./webpages/webpages/
        
        '''
        file = "./index.json"
        if os.path.exists(file):
            with open(file, 'r') as file:
                self.inverted = json.load(file)
        else:
            json_file = self._load_json_file(path) # loads json file
            for key in json_file:
                # print(key + ' ' + json_file[key]) # prints key with the url
                print(key)
                filepath = os.path.join(extension, key)
                parsed_html = self.__parse_html(filepath, key)

        # self.__update_db() # Updates database
        self.__update_file() # Updates file
 
        # TODO: MILESTONE 2: TF-IDF SYSTEM PLUS INTERFACE OF SEARCH SYSTEM.

    def __update_file(self):
        try:
            file = 'index.json'
            with open(file, 'w') as file:
                json.dump(self.inverted, file, indent=4)  # The indent parameter is optional but helps with readability

            file2 = 'results.txt' 
            with open(file2, 'w') as file2:
                # Writes total htmls parsed to results.txt
                file2.write(f'TOTAL HTML  USED: {self.num_docs}\n')
                file2.write('-----------------------------------------------------------------------------------------\n')

                # Writes amount of unique words to results.txt
                unique_words = len(self.inverted)
                file2.write(f'UNIQUE WORDS (TOKENS): {unique_words}\n')
                file2.write('-----------------------------------------------------------------------------------------\n')

                # Writes size of index.json, which is inverted index, to results.txt
                size_bytes = os.path.getsize("./index.json")
                size_kbs = size_bytes / 1024
                size_kbs = "{:.2f} KB".format(size_kbs) # formats to two decimals
                file2.write(f'SIZE OF INVERTED INDEX IN KB: {size_kbs}\n')

        except Exception as e:
            print(f"There was an error trying to write to one of the files. \n \
                The following exception was thrown: {str(e)}.")

    def __update_db(self):
        '''
        Updated db with values from self.inverted.
        TODO: ADD TRY/EXCEPT TO HANDLE EXCEPTIONS.
        '''
         # DATABASE
        self.client = MongoClient("localhost", 27017)
        self.db = self.client['search_system'] # initializes our database
        self.collection_in = self.db['inverted'] # initializes collection called 'inverted' which is the same as a table in SQL.
        # self.collection_doc = self.db['doc'] # initilaizes collection called 'doc' to keep track of each doc and how many values they keep.

        for token, docs in self.inverted.items():
            document = {
                "_id": token,  # Use the token as the document ID to ensure uniqueness
                "docs": docs  # Embed the associated document details directly
            }
            try:
                self.collection_in.insert_one(document)
                print(f"Inserted document for token: {token}")
            except Exception as e:
                print(f"Failed to insert document for token: {token}. Error: {e}")

        self.client.close()

    def __compute_tf(self, key: str):
        '''
        Given a key that will be used in dictionary num_words_per_doc to get the total words \
        in that doc, compute_tf will calculate tf of a document based on the formula:

        TF(t, d) = (Number of times term t appears in a document d) / (Total number of words in document d)
        
        TF will be a dictionary containing key and its TF (term-frequency) value
        '''
        if key not in self.num_words_per_doc:
            return {} # returns an empty dictionary.
        
        computed_tf = {}
        for word, doc in (self.inverted).items():
            if key in doc: # found a match
                computed_tf[word] = doc[key]['frequency'] / self.num_words_per_doc[key]

        return computed_tf
    
    def __compute_df(self):
        '''
        Computes how many documents each term in self.invert are contained.

        DF(t) = Total number of documents that contain each term.
        '''
        compute_df = {}
        for key in self.inverted:
            compute_df[key] = len(self.inverted[key])
        return compute_df


    def __compute_idf(self, compute_df=None):
        '''
        Computes Inverse Document Frequency. For that, it needs the total number of documents in the corpus.

        IDF(t, d) = log(N/ df(t)), where N is the total number of documents and df(t) is document frequency \
        of term t.

        returns a dictionary that contains IDF for each term.
        '''
        if len(compute_df) == 0 or compute_df == None:
            return {}
        
        compute_idf = {}
        N = self.num_docs
        for key, df in compute_df.items():
            compute_idf[key] = math.log((N + 1)/(df + 1)) + 1
        return compute_idf
    
    def __compute_tf_idf(self, tf, idf):
        '''
        Computes TF-IDF, which should take token frequency with each term and its tf value, and inverse document frequency \
        which has idf value for each token.

        TODO: ADD FORMULA
        '''
        if tf == None or idf == None:
            return {}
        if len(tf) == 0 or len(idf) == 0:
            return {}
        
        compute_tf_idf = {}
        for key, tf_val in tf.items():
            compute_tf_idf[key] = tf_val * idf.get(key, 0)


    def __tokenize(self, content: str):
        '''
        Takes a string with all kinds of characters as an input, tokenizes the string, filters stop words and words/characters \
        that have no meaning, and returns a list with meaningful tokens.
        '''
        processed_text = (''.join([char if char.isalpha() else '' if char == '\'' else ' ' for char in content])).lower() # changes any non-alphabethic character to a spac, and apostrophe for an empty string.
        possible_tokens = pos_tag(processed_text.split()) # a list of possible tokens together with their tags (pos).
        tokens = [] # list that will be returned with all tokenized words.
        lemmatizer = WordNetLemmatizer() # lemmatizer that will be used from NLTK

        for word, pos in possible_tokens:
            if (len(word) > 1) and (word not in self.stop_words): # checks for stop words and characters.
                pos_ = self.__get_pos(pos) # used together with wordNetLemmatizer
                lem_word = lemmatizer.lemmatize(word, pos_) # lemmantizes
                tokens.append(lem_word)
        return tokens

    def __get_pos(self, pos):
        '''
        Returns a pos of a word provided as parameter.
        '''
        if pos.startswith('J'):
            return wordnet.ADJ
        elif pos.startswith('R'):
            return wordnet.ADV
        elif pos.startswith('V'):
            return wordnet.VERB
        else:
            return wordnet.NOUN


class search_engine:
    def __init__(self):
        # creates and runs index for search engine
        self.search_engine = search_system_index_gen()
        self.search_engine.run_search_system("./webpages/webpages/bookkeeping.json", "./webpages/webpages")


    def run_engine(self):

        try:
            file = 'search_results.txt'
            with open(file, 'w') as file:
                while True:
                    query = input("Search Query:")
                    if query == None or query == "":
                        break # search is done
                    
                    # TODO: MILESTONE 2, IMPLEMENT A SEARCH QUERY THAT WORKS WITH MULTIPLE WORDS IN A QUERY
                    query = query.split() # will split query if more than one word is found
                    for q in query: # for milestone 1, it will just go through each query and find urls
                        if q in self.search_engine.inverted:
                            list_urls = {}
                            for doc in self.search_engine.inverted[q]:
                                list_urls[doc] = self.search_engine.inverted[q][doc]['relevance'] # our heuristics are based on relevance for now.

                            list_urls = dict(sorted(list_urls.items(), key=lambda item: item[1], reverse=True)) # sorts based on relevance
                            json_file = self.search_engine._load_json_file("./webpages/webpages/bookkeeping.json")
                            index = 0
                            file.write(f'QUERY: {q} | TOTAL URLS: {len(list_urls)}\n\n')
                            for key in list_urls:
                                if index >= 20:
                                    break
                                str = f"{json_file[key]}"
                                file.write(f'{str}\n')
                                index += 1
                            file.write('-----------------------------------------------------------------------------------------\n')

                        else:
                            file.write(f'QUERY: {q} | TOTAL URLS: 0\n')
                            file.write('-----------------------------------------------------------------------------------------\n')

                    

        except Exception as e:
            print(f"There was an error trying to write to one of the files. \n \
                The following exception was thrown: {str(e)}.")

        
# search_engine = search_system_index_gen()
# search_engine.run_search_system("./webpages/webpages/bookkeeping.json", "./webpages/webpages")

search = search_engine()
search.run_engine()

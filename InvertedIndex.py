from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
import os
import json
import math

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

MAX_BUCKET_SIZE = 10000

class InvertedIndex:
    '''
    A complete inverted index generator for a search system.
    '''
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.words_per_doc = {} # Empty dictionary that  will contain document as key and number of words as value.
        self.num_docs = 0
        self.stop_words = set(stopwords.words('english'))
        self.tokens = [] # this dictionary will be used to create a new token on mongoDB and keep the new ID.
    

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
                content = soup.get_text().lower() # gets all the text content of page without html tags.
                content = word_tokenize(content) # tokenize all possible tokens; for the search system, we will consider tokens that have alphanumeric characters also tokens.
                possible_tokens = pos_tag(content) # a dictionary of possible tokens together with their tags (pos).
                lemmatizer = WordNetLemmatizer() # lemmatizer that will be used from NLTK
                content = [lemmatizer.lemmatize(word, self.__get_pos(pos)) for word, pos in possible_tokens if word not in self.stop_words]

                doc_words = {} # dictionary with word as key and list as information to be added for posting list.
                has_content = False
                self.words_per_doc[key] = len(content) # counts how many words there is to be used in the future with a more complex tf-idf search tool.

                if content is None:
                    return None, None
                else:
                    ind = 1 # index used to check what position is that word within a page.
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
                            tag_content = word_tokenize(tag.get_text().lower())
                            tag_possible_tokens = pos_tag(tag_content)
                            tag_content = [lemmatizer.lemmatize(word, self.__get_pos(pos)) for word, pos in tag_possible_tokens if word not in self.stop_words]
                            for token in tag_content:
                                if token not in doc_words:
                                    doc_words[token] = [[ind], 1, relevance]
                                else:
                                    doc_words[token][0].append(ind) # adds index of correctly to posting.
                                    doc_words[token][1] += 1
                                    doc_words[token][2] += relevance
                                ind += 1  # Ensure this increment is correctly placed to reflect the overall document indexing
                    
                    # Updates database with tokens and postings here.
                    if has_content:
                        for token, posting in doc_words.items():
                            if token in self.tokens:
                                # adds posting to list of postings for that particular token.
                                posting_id = self.postings.insert_one({'document': key, 'indexes': posting[0], 'frequency': posting[1], 'relevance': posting[2]}).inserted_id
                                self.tokens_table.update_one({'token': token},{'$push':{'posting': posting_id}})
                            else:
                                posting_id = self.postings.insert_one({'document': key, 'indexes': posting[0], 'frequency': posting[1], 'relevance': posting[2]}).inserted_id
                                self.tokens_table.insert_one({'token': token, 'posting': [posting_id]}) # inserts posting_id that will be used in collection to get posting.
                                self.tokens.append(token)
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
        
    def run_index_generator(self, path:str, extension=''):
        '''
        Takes a path_file, which is a path to a json file containing keys that are \
        an extension that will be joined with the path of a url and the url as a value. \
        Extension is an optional string that will be used if user has a specific path to \
        look for the urls.

        extension in our case should be ./webpages/webpages/
        
        '''
        try:
            # runs database.
            self.client = MongoClient() # runs on regular MongoClient
            self.db = self.client['index']
            self.tokens_table = self.db['inverted_index']
            self.postings = self.db['postings']
            self.tokens_table.drop()
            self.postings.drop()
            index_name = self.tokens_table.create_index([('token', 1)]) # Update index to have faster operations.
            json_file = self._load_json_file(path) # loads json file
            for key in json_file:
                # print(key + ' ' + json_file[key]) # prints key with the url
                print(key)
                filepath = os.path.join(extension, key)
                parsed_html = self.__parse_html(filepath, key)
        except Exception as e:
            print('Error inside run_index_generator')
            self.client.close()
            exit()

        self.__update_db() # Updates database
        self.__update_file() # Updates file
        self.compute_tf_idf() # computes tf-idf for values.
 
        # closes connection with database
        self.client.close()

    def __update_file(self):
        try:
            file = 'results.txt' 
            with open(file, 'w') as file:
                # Writes total htmls parsed to results.txt
                file.write(f'TOTAL HTML  USED: {self.num_docs}\n')
                file.write('-----------------------------------------------------------------------------------------\n')

                # Writes amount of unique words to results.txt
                unique_words = len(self.tokens)
                file.write(f'UNIQUE WORDS (TOKENS): {unique_words}\n')
                file.write('-----------------------------------------------------------------------------------------\n')

                # Writes size of index.json, which is inverted index, to results.txt
                size_bytes = os.path.getsize("./index.json")
                size_kbs = size_bytes / 1024
                size_kbs = "{:.2f} KB".format(size_kbs) # formats to two decimals
                file.write(f'SIZE OF INVERTED INDEX IN KB: {size_kbs}\n')

        except Exception as e:
            print(f"There was an error trying to write to one of the files. \n \
                The following exception was thrown: {str(e)}.")

    def __update_db(self):
        '''
        Update database with necessary tables and ids.
        '''
        self.information = self.db['information']
        self.information.insert_one({'INFORMATION_TYPE': 'TOTAL_DOCS','TOTAL_DOCS': self.num_docs}) # updates 'information' collection with total number of documents.
        return

    
    def compute_tf_idf(self):
        '''
        Computes TF-IDF, which should take token frequency with each term and its tf value, and inverse document frequency \
        which has idf value for each token.
        '''
        N = self.num_docs # keeps total number of documents.
        self.tf_idf_ = self.db['tf_idf'] # creates new table for TF-IDF scores.

        for token in self.tokens:
            token_doc = self.tokens_table.find_one({'token': token})
            for post_id in token_doc["posting"]:
                post_doc = self.postings.find_one({"_id": post_id})
                if post_doc:
                    TF = post_doc['frequency']
                    n = len(token_doc['posting'])
                    IDF = math.log10(N / float(n) + 1)
                    TF_IDF = TF * IDF
                    print(f'{post_doc["document"]}, {TF_IDF}')
                    self.postings.update_one({"_id": post_id},{"$set": {"tf-idf": TF_IDF}})
    


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
        
# class PageRank:

        
search_engine = InvertedIndex()
search_engine.run_index_generator("./webpages/webpages/bookkeeping.json", "./webpages/webpages")

# search = search_engine("./webpages/webpages/bookkeeping.json", "./webpages/webpages")
# search.run_engine()

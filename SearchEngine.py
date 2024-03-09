# import InvertedIndex
import numpy as np
from scipy.spatial.distance import cosine
from pymongo import MongoClient
import math
import json


# Natural language library that will be used.
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk import pos_tag
from nltk.tokenize import word_tokenize

class SearchEngine:
    def __init__(self):
        # creates and runs index for search engine
        self.query = '' # TODO: SAVE SUBMITTED QUERIES TO EITHER DATABASE OR TO A LIST TO HAVE IT TEMPORARILY.
        self.stop_words = set(stopwords.words('english'))


    def run_engine(self, query):
        try:
            self.query = query.lower()
            print(f'[!] QUERY PROCESSING: {self.query}')

            content = word_tokenize(self.query) # __tokenize all possible tokens; for the search system, we will consider tokens that have alphanumeric characters also tokens.
            possible_tokens = pos_tag(content) # a dictionary of possible tokens together with their tags (pos).
            lemmatizer = WordNetLemmatizer() # lemmatizer that will be used from NLTK
            content = [lemmatizer.lemmatize(word, self.__get_pos(pos)) for word, pos in possible_tokens if word not in self.stop_words]

            print(content)
            self.client = MongoClient() # runs on regular MongoClient
            self.db = self.client['index']
            self.tokens_table = self.db['inverted_index']
            self.postings = self.db['postings']
            index_name = self.tokens_table.create_index([('token', 1)]) # Update index to have faster operations.

            query_vector = self.__query_tf_idf(content)
            query_vector = np.array(query_vector)
            ''' 
            TODO: CALCULATE VECTORS FOR ALL THE POSSIBLE DOCUMENTS FROM QUERY. IN THE FUTURE, INSTEAD OF VECTORS, WE WILL \
            SUBSTITUTE THEM FOR THE COSINE SIMILARITY RESULT BETWEEN EACH VECTOR AND THE QUERY VECTOR LOCATED BELOW.
            '''
            vectors = {}
            
            for word in content:
                token = self.tokens_table.find_one({'token': word})
                if token:
                    for posting_id in token["posting"]:
                        posting_doc = self.postings.find_one({"_id": posting_id})
                        if posting_doc["document"] not in vectors:
                            vectors[posting_doc["document"]] = [posting_doc["tf-idf"]]
                        else:
                            vectors[posting_doc["document"]].append(posting_doc["tf-idf"])


            for document in vectors:
                print(document)
                while(len(vectors[document]) < len(query_vector)):
                    vectors[document].append(0) # normalizes the vectors so we can calculate the cosine similarity later.

                # after normalizing vectors, we calculate cosine similarity with scipy, and change the list with tf-idf values to cosine_similarity values.
                vector_tmp = np.array(vectors[document])
                cosine_similarity = 1 - cosine(query_vector, vector_tmp)
                vectors[document] = cosine_similarity

            search_result = dict(sorted(vectors.items(), key=lambda x: x[1], reverse=True)) # sorts the search result dictionary in reverse order, from highest to lowest cosine similarity.
            # for document, cos in search_result.items():
            #     print(f'{document} : {cos}')
            json_file = self._load_json_file("./webpages/webpages/bookkeeping.json")
            search_urls = []
            for key, cos in search_result.items():
                search_urls.append(json_file[key])

            # print(search_urls)
            self.client.close()
            self.__update_file(search_urls[:20])
            print('[+] QUERY PROCESSED SUCCESSFULLY!')
            return search_urls[:20]


        except Exception as e:
            print(f"[-] There was an error trying to write to one of the files. \n \
                The following exception was thrown: {str(e)}.")
            
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
            
    def __query_tf_idf(self, query):
        '''
        Calculates TF-IDF OF QUERY
        '''
        term_frequency = {}
        for word in query:
            if word not in term_frequency:
                term_frequency[word] = 1
            else:
                term_frequency[word] += 1

        self.information = self.db['information']
        N = self.information.find_one({'INFORMATION_TYPE': 'TOTAL_DOCS'})['TOTAL_DOCS']

        query_tf_idfs = []
        for token in query:
            token_doc = self.tokens_table.find_one({'token': token})
            if token_doc:
                TF = term_frequency[token] # term frequency from the query
                n = len(token_doc['posting'])
                IDF = math.log10(N / float(n) + 1)
                TF_IDF = TF * IDF
                query_tf_idfs. append(TF_IDF)

        print(query_tf_idfs)
        return query_tf_idfs
    
            
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
            
    def __update_file(self, results):
        try:

            file = 'search_results.txt' 
            with open(file, 'a') as file:
                # Writes total htmls parsed to results.txt
                file.write(f'QUERY: {self.query}\n\n')
                for url in results:
                    file.write(f'{url}\n')
                file.write('-----------------------------------------------------------------------------------------\n')

        except Exception as e:
            print(f"There was an error trying to write to one of the files. \n \
                The following exception was thrown: {str(e)}.")
from rdflib import Graph , Literal, RDF, URIRef
from pyparsing import ParseException
from rdflib.namespace import RDF
from mapper import Mapper
import log
import validators
from cache import Cache
from config import Config
import scispacy
import spacy
import json
import requests
import urllib
from augmentation_model import AugmentationModel

nlp = spacy.load("en_ner_bionlp13cg_md")
# nlp = spacy.load("en_core_web_md")
"""_summary_
    Import spacy
"""
class Processing: 
    """
        increases all received objects
    """
    def __init__(self, graph=None, objects=[], config={}, count_model=3, input_file=None):
        self.config = config 
        self.graph = graph
        self.objects = objects
        self.count_model = count_model
        self.input_file = input_file
        self.count_objects = len(objects)
        self.limit = 1

    def load_graph(self, input_file=''):
        g = Graph()
        try:
            g.parse(input_file)
        except Exception as _ :
            log.critical('#Not converted to graph >> ' + input_file + ' ....%')
            return None
        return g
    
    def clean(self, text=''):
        output = text
        if any(not c.isalnum() for c in text) :
            output = ''
        return output
    
    def get_subject_instance(self, uri=''):
        return Cache().get_ressource(uri=uri)

    def run_get(self, api_encoded='', headers=None):
        output = None
        try:
            r = requests.get(api_encoded,  headers=headers)
            # print(r.text)
            if r.status_code == requests.codes.ok :
                data_json = json.loads(r.text)
                tmp = [v['subject']['value'] for v in data_json['results']['bindings'] if 'uniprot' in v['subject']['value']] # filter
                output = tmp if len(tmp) > 0 else None                
        except Exception as _:
            log.error('GET #Request on the ressource failed : ' + api_encoded)
        return output
    
    def update_graph(self, graph=None, _subject='', _predicate='', _old_object='', _new_object=''):
        """[updates the value of the old object with the new]
        Args:
            _subject (str): [the subject's value].
            _predicate (str): [the predicate's value].
            _old_object (str): [the old object's value].
            _new_object (str): [the new object's value].
        Returns:
            [obj]: [obj]
        """
        fork_data = """INSERT DATA { <?subject>  <?predicate>    ?object }"""
        query = """
            DELETE { <?subject>  <?predicate>    ?old_object .  }
            INSERT {    <?subject>  <?predicate>    ?object .   }
            WHERE   { 
                <?subject>  <?predicate>    ?old_object .
            }
            """
        query = query.replace('?subject', _subject).replace('?predicate',  _predicate)
        fork_data = fork_data.replace('?subject', _subject).replace('?predicate',  _predicate)
                
        if validators.url(_old_object) : 
            query = query.replace('?old_object', '<' + _old_object + '>')
        else :
            query = query.replace('?old_object', '"' + _old_object + '"')
        
        if validators.url(_new_object) : 
            fork_data = fork_data.replace('?object', '<' + _new_object + '>')
            query = query.replace('?object', '<' + _new_object + '>')
        else :
            fork_data = fork_data.replace('?object', '"' + _new_object + '"')
            query = query.replace('?object', '"' + _new_object + '"')
        
        # fork_data_result = graph.update(fork_data)
        query_result = None
        try:
            query_result = graph.update(query)
        except ParseException as _ :
            print('Exception during updating graph')
            log.critical('Exception during updating graph')
        return query_result

    def extract_entities(self, text=''):
        output = {}
        doc = nlp(text)
        config = self.config['topic_modeling']
        accepted_predicates = config['accepted_predicates']
        accepted_values = config['accepted_values']
        # print('First >>> ', text)
        tmp = []
        for token in doc.ents:
            # solve entity
            # isRelevant
            _, _subject = self.get_entity_subject(value=token.text, label=token.label_)
            tmp = self.get_subject_instance(uri=_subject) if not 'entities.org' in _subject else []
            # filtered specific type
            tmp = [v for v in tmp if v['p'] in accepted_predicates or v['o'] in accepted_values]
            tmp.append({'p': 'http://www.w3.org/2000/01/rdf-schema#type', 'o': token.label_})
            tmp.append({'p': 'http://www.w3.org/2000/01/rdf-schema#label', 'o': token.text})
            output[token.text] = [] if not token.text in output else output[token.text]
            for v in tmp:
                output[token.text].append((_subject, v['p'], v['o']))
        return output

    def get_entity_subject(self, value='', label=''):
        output = 'http://entities.org/name/' + label + '/' + value.replace(' ','_')
        isRelevant = 0
        config = self.config['endpoints']
        config = config[label] if label in config else None
        if config == None:
            return isRelevant, output
        else:
            # print('\t', value, label)
            param = config['params'] 
            query = config['query']#.replace(' ','+')
            api = config['api']
            query = query.replace(param, value)
            # api = api.replace(param, query)
            # build query and run it
            api = api.replace(param, urllib.parse.quote(query.encode('utf-8')))
            # print(api)
            _subjects = self.run_get(api_encoded=api)
            # print('response # ', _subjects)
            if _subjects != None and len(_subjects) > 0 :
                output = _subjects[0]
                isRelevant = 1                        
        return isRelevant, output
    
    def run(self):
        # copy_objects = self.objects
        # graph = self.graph
        # i = 0
        copy_objects = self.objects
        _graphs = [self.load_graph(input_file=self.input_file) for _ in range(self.count_model)]
        _objects = []
        object_counter = 0
        for _object in self.objects :
            _objects.append(_object)
            result = self.extract_entities(text=str(_object))
            copy_objects[_object]['values'] = result
        
        for _object in _objects:
            # update graph with  new models
            # parallel 
            _graphs = AugmentationModel(graphs=_graphs,
                                      config=self.config,
                                      input_file=self.input_file,
                                      _object=_object,
                                      percent=((object_counter/self.count_objects) * 100),
                                      subjects=copy_objects[_object]['subjects'],
                                      predicates=copy_objects[_object]['predicates'],
                                      triplets=copy_objects[_object]['values']).run()
            object_counter+=1
        return _graphs

# result = Processing().indexing(uri='http://purl.obolibrary.org/obo/TO_0000691')

# result = Processing().increase(_object='http://purl.obolibrary.org/obo/TO_0000691')
# print(result)

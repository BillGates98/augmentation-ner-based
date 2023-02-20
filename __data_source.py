from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from processing import Processing
import log
from decimal import *
from  config import Config
import os


class DataSource: 

    def __init__(self, index_file=-1, total=0, input_file='', output_file='', config={}):
        super().__init__()
        self.count_model = 3
        self.config = config if config else Config().load()
        self.output_dir = config['outputs']
        self.input_file = input_file
        self.output_files = self.update_output_file(value=output_file)
        self.index_file = index_file
        self.total = total
        self.dataset = []
        log.info('Dataset Augmentation Process start on ' + self.input_file + ' at 0% of the end and represent ' + str(index_file+1) + '/' + str(total) + ' of all')
        self.limit = 1000
    
    def update_output_file(self, value=''):
        output = []
        for i in range(self.count_model):
            file_name = value.replace(self.output_dir, self.output_dir + 'model' + (str(i+1)) + '/')
            path = file_name.split('/')[:-1]
            path = '/'.join(path)
            if not os.path.exists(path): 
                os.makedirs(path)
            output.append(file_name)
        return output
    
    def get_predicates(self, g=None):
        """
            Get all predicate of the current graph
        """
        query = """SELECT ?p WHERE { ?s ?p ?o .}"""
        return g.query(query)

    def load_graph(self):
        _models = self.config['models']
        """
            expands the data and puts the new version in the associated output file
        """
        g = Graph()
        try:
            g.parse(self.input_file)
        except Exception as _ :
            log.critical('#Not converted to graph >> ' + self.input_file + ' ....%')
            return

        """
            all the predicates found the marks to be considered or not for the augmentation process
        """
        if self.config['make_configuration'] == "True":
            predicates = []
            for pred in self.get_predicates(g=g):
                predicates.append(pred['p'])
            predicates = list(dict.fromkeys(predicates))
            for pred in predicates:
                Config().update(parent='predicates', pair={'key': pred, 'value': '0'})
        
        """
            Search all unique objects to increase  
        """
        if self.config['increasing_process'] == "True":
            objects = {}
            counter = 0
            both_object_type = self.config['object_type']
            for subject, predicate, object_ in g:
                if ((both_object_type == "literal" and isinstance(object_, Literal)) or (both_object_type == "both")):
                    if not object_ in objects :
                        objects[object_] = { 'value': object_, 'subjects': [], 'predicates': []}
                    subjects = objects[object_]['subjects']
                    subjects.append(subject)
                    predicates = objects[object_]['predicates']
                    predicates.append(predicate)
                    objects[object_]['subjects'] = subjects
                    objects[object_]['predicates'] = predicates
                else:
                    if ((both_object_type == "uri" and isinstance(object_, URIRef))):
                        if not object_ in objects :
                            objects[object_] = { 'value': object_, 'subjects': [], 'predicates': []}
                        subjects = objects[object_]['subjects']
                        subjects.append(subject)
                        predicates = objects[object_]['predicates']
                        predicates.append(predicate)
                        objects[object_]['subjects'] = subjects
                        objects[object_]['predicates'] = predicates
                
                if counter == self.limit :
                    break
                counter = counter + 1
        
            graphs = Processing(graph=g, objects=objects, config=self.config, input_file=self.input_file).run(graph=g)
            try:
                [graphs[i].serialize(destination=self.output_files[i], format='turtle') for i in range(self.count_model) if str((i+1)) in _models]
                log.info('#Augmentation Done on dataset ' + self.input_file + ' -> (' + str(self.progression()) + '% of all)')
                # log.info(g.serialize(format="turtle").decode("UTF-8"))    
            except Exception :
                pass
        return
            

    def progression(self, value=0):
        value = Decimal((self.index_file+1)/self.total)
        value = value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        return value*100

    def run(self):
        self.load_graph()
        log.info('Dataset Augmentation Process on ' + self.input_file + ' is 100%, that represent ' + str(self.index_file+1) + '/' + str(self.total) + ' of all')
        
        
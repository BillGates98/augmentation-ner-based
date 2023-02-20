from rdflib import Graph, Literal, URIRef
import os
from processing import Processing
import log
from decimal import *


class DataSource:

    def __init__(self, index=-1, total=0, input_file='', output_file='', config={}):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.index = index
        self.count_model = 3
        self.output_dir = config['outputs']
        self.config = config
        self.total = total
        self.output_files = self.update_output_file(value=output_file)
        self.dataset = []
        log.info('Data source augmentation : ' + self.input_file +
                 ' 0% => ' + str(index+1) + '/' + str(total))
        self.limit = 50

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

    def get_format(self, value=''):
        extensions = ['.rdf', '.owl', '.xml']
        for ext in extensions:
            if ext in value:
                return 'xml'
        return 'trig'

    def load_graph(self):
        _models = self.config['models']
        """
            expands the data and puts the new version in the associated output file
        """
        g = Graph()
        try:
            g.parse(self.input_file, format=self.get_format(
                value=self.input_file))
        except Exception as _:
            log.critical('#Not converted to graph >> ' +
                         self.input_file + ' ....%')
            return

        """
            Search all unique objects to increase
        """
        objs = []
        objects = {}
        counter = 0
        # for subject, predicate, object_ in g:
        # objs.append(object_)
        # # if str(predicate) in ['http://www.w3.org/2000/01/rdf-schema#label']:
        #     if not object_ in objects:
        #         objects[object_] = {'value': object_,
        #             'subjects': [], 'predicates': []}
        #         subjects = objects[object_]['subjects']
        #         subjects.append(subject)
        #         predicates = objects[object_]['predicates']
        #         predicates.append(predicate)
        #         objects[object_]['subjects'] = subjects
        #         objects[object_]['predicates'] = predicates
        both_object_type = self.config['object_type']
        for subject, predicate, object_ in g:
            objs.append(object_)
            if ((both_object_type == "literal" and isinstance(object_, Literal)) or (both_object_type == "both")):
                if not object_ in objects:
                    objects[object_] = {'value': object_, 'subjects': [], 'predicates': []}
                    subjects = objects[object_]['subjects']
                    subjects.append(subject)
                    predicates = objects[object_]['predicates']
                    predicates.append(predicate)
                    objects[object_]['subjects'] = subjects
                    objects[object_]['predicates'] = predicates
                else:
                    if ((both_object_type == "uri" and isinstance(object_, URIRef))):
                        if not object_ in objects:
                            objects[object_] = {
                                'value': object_, 'subjects': [], 'predicates': []}
                        subjects = objects[object_]['subjects']
                        subjects.append(subject)
                        predicates = objects[object_]['predicates']
                        predicates.append(predicate)
                        objects[object_]['subjects'] = subjects
                        objects[object_]['predicates'] = predicates

                if counter == self.limit:
                    break
                counter = counter + 1
        graphs = Processing(graph=g, objects=objects, config=self.config, input_file=self.input_file).run()
        # exit()
        try:
            [graphs[i].serialize(destination=self.output_files[i], format='turtle') for i in range(self.count_model) if str((i+1)) in _models]
            log.info('#Augmentation Done on dataset ' + self.input_file + ' -> (' + str(self.progression()) + '% of all)')
            # log.info(g.serialize(format="turtle").decode("UTF-8"))
        except Exception:
            pass
        # print( len( list(dict.fromkeys(objs)) ))
        # g.serialize(destination=self.output_file, format='turtle') # uncomment
        log.info('#Done ' + self.input_file + ' -> (' + str(self.progression()) + '%)')
        # print(g.serialize(format="turtle").decode("UTF-8"))

    def progression(self, value=0):
        value = Decimal((self.index+1)/self.total)
        value = value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        return value*100

    def run(self):
        self.load_graph()
        log.info('Data source augmentation : ' + self.input_file + ' 100% => ' + str(self.index+1) + '/' + str(self.total))

from unittest import result
from pyparsing import ParseException
from rdflib.namespace import RDF
import log
import validators
from datetime import datetime
from dump import dump


class AugmentationModel:

    def __init__(self, graphs=None, config=None, input_file=None, _object=None, percent=-1, subjects=[], predicates=[], triplets=[]):
        self.graphs = graphs
        self.config = config
        self._object = _object
        self.percent = percent
        self.input_file = input_file
        self.subjects = subjects
        self.predicates = predicates
        self.triplets = triplets  # {cm: [(s, p, o),...]}
        self.keywords_labels = self.config['keywords_label']
        self.linking_predicate   = self.config['linking_predicate']
        # log.info('Start using model')
    
    """
       filter function for triplets based on an initial selection
    """
    def filtered_triplets(self, data=[], _predicates=[]):
        if len(_predicates) > 0 :
            return [(s, p, o) for s, p, o in data for kw in _predicates if kw in p]
        return data

    """
        Model 1 : substitution of the initial object after the disappearance of complex terms
    """
    def update_substitution_based_model(self, graph=None, _subject='', _predicate='', _old_object='', _new_object=''):
        query = """
            DELETE { <?subject>  <?predicate>    ?old_object .  }
            INSERT {    <?subject>  <?predicate>    ?object .   }
            WHERE   { 
                <?subject>  <?predicate>    ?old_object .
            }
            """
        query = query.replace('?subject', _subject).replace(
            '?predicate',  _predicate)

        query_result = None
        try:
            if validators.url(_old_object):
                query = query.replace('?old_object', '<' + (_old_object) + '>')
            else:
                query = query.replace('?old_object', '"' + (_old_object) + '"')

            if validators.url(_new_object):
                query = query.replace('?object', '<' + (_new_object) + '>')
            else:
                query = query.replace('?object', '"' + (_new_object) + '"')
            dump().write_to_txt(file_path='./outputs/motifs/update_queries.txt', values=['Query 1', query])
            query_result = graph.update(query)
            if query_result != None :
                log.critical("Model 1 : Error when Updating : " + _subject + ' ' +_predicate + ' ' + _old_object + ' ' +_new_object )                       
        except ParseException as _:
            log.critical('Model 1 : Exception during updating graph')
        return graph        
        
    def model_substitution_based(self, graph=None, _subject='', _predicate='', _old_object='', _triplets={}):
        """[updates the value of the old object with the new]
        Args:+
            _subject (str): [the subject's value].
            _predicate (str): [the predicate's value].
            _old_object (str): [the old object's value].
            _triplets (dict): [the results of all complex models].

        Returns:
            [obj]: [the updated of the initial object]
        """
        predicates_to_be_filtered = self.keywords_labels
        _complex_models = list(dict.fromkeys(_triplets))
        _object = _old_object
        _graph = graph
        for complex_model in _complex_models :
            _data = _triplets[complex_model]
            _filtered_triplets = self.filtered_triplets(data=_data, _predicates=predicates_to_be_filtered)
            if len(_filtered_triplets) > 0 :
                _all_objects = [ '' if o in _object else o for _, _, o in _filtered_triplets]
                _value = ' '.join(_all_objects)
                if len(_value.lstrip()) > 0 :
                    _object = _object.replace(complex_model, _value)
            
            for s, p, o in _data :
                _graph = self.update_instance_linking_based_model(graph=_graph, _subject=_subject, _predicate=p, _new_object=o)
        _new_object = _object
        _graph = self.update_substitution_based_model(graph=_graph, _subject=_subject, _predicate=_predicate, _old_object=_old_object, _new_object=_new_object)
        log.info('substitution maked')
        return _graph

    """
        Model 2 : linking the instance of the model encountered with the subject of the object of that model
    """
    def update_instance_linking_based_model(self, graph=None, _subject='', _predicate='', _new_object=''):
        query = """INSERT DATA { <?subject>  <?predicate>  ?object . }"""
        query = query.replace('?subject', _subject).replace('?predicate',  _predicate)
        query_result = None
        try:
            if validators.url(_new_object):
                query = query.replace('?object', '<' + (_new_object) + '>')
            else:
                query = query.replace('?object', '"' + (_new_object) + '"')
            dump().write_to_txt(file_path='./outputs/motifs/update_queries.txt', values=['Query 2', query])
            query_result = graph.update(query)
            if query_result != None :
                log.critical("Model 2 : Error when Updating : " + _subject + ' ' + _predicate + ' ' + _new_object )
        except ParseException as _:
            log.critical('Model 2 : Exception during updating graph')
        return graph 
    
    def model_instance_linking_based(self, graph=None, _subject='', _predicate='',  _triplets={}, _old_object=''):
        _complex_models = list(dict.fromkeys(_triplets))
        _current_subject = None
        for complex_model in _complex_models :
            _data = _triplets[complex_model]
            # _filtered_triplets = self.filtered_triplets(data=_data, _predicates=predicates_to_be_filtered)
            for s, p, o in _data :
                print('\t \t ### ', s)
                graph = self.update_instance_linking_based_model(graph=graph, _subject=s, _predicate=p, _new_object=o) # , _old_object=_old_object
                _current_subject = s
            graph = self.update_instance_linking_based_model(graph=graph, _subject=_subject, _predicate=_predicate, _new_object=_current_subject) # , _old_object=_old_object
        log.info('instance linking based')                
        return graph
        

    """
        Model 3 : addition of triples whose predicate is the uri associated with the model encountered
    """
    def update_instance_adding_triple_based_model(self,  graph=None, _subject='', _predicate='', _new_object=''):
        query = """INSERT DATA { <?subject>  <?predicate>    ?object . }"""
        query = query.replace('?subject', _subject).replace('?predicate',  _predicate)
        query_result = None
        try:
            if validators.url(_new_object):
                query = query.replace('?object', '<' + (_new_object) + '>')
            else:
                query = query.replace('?object', '"' + (_new_object) + '"' )
            dump().write_to_txt(file_path='./outputs/motifs/update_queries.txt', values=['Query 3', query])
            query_result = graph.update(query)
            if query_result != None :
                log.critical("Model 3 : Error when Updating : " + _subject + ' ' + _predicate + ' ' + _new_object )
        except ParseException as _:
            log.critical('Model 3 : Exception during updating graph')
        return graph 
    
    def model_instance_adding_triple_based(self, graph=None, _subject='', _triplets={}):
        _complex_models = list(dict.fromkeys(_triplets))
        for complex_model in _complex_models :
            _data = _triplets[complex_model]
            # _filtered_triplets = self.filtered_triplets(data=_data, _predicates=predicates_to_be_filtered)
            for s, _, o in _data :
                print('Build model 3 ')
                graph = self.update_instance_adding_triple_based_model(graph=graph, _subject=_subject, _predicate=s, _new_object=o)
        log.info('instance adding triple based')
        return graph

    def run(self):
        _models = self.config['models']
        _linking_predicate = self.config['linking_predicate']
        _subjects = self.subjects
        _predicates = self.predicates
        _triplets = self.triplets
        _object = self._object
        if validators.url(self._object) :
            _object = (_object)
                
        for _subject, _predicate in list(zip(_subjects, _predicates)):
            _subject = (_subject)
            _predicate = (_predicate)
            try:
                # [(s, p, o), ...]
                if "1" in _models :
                    self.graphs[0] = self.model_substitution_based(graph=self.graphs[0], _subject=_subject, _predicate=_predicate, _old_object=_object, _triplets=_triplets)
                    
                if "2" in _models :
                    self.graphs[1] = self.model_instance_linking_based(graph=self.graphs[1], _subject=_subject, _predicate=_linking_predicate, _triplets=_triplets)

                if "3" in _models :
                    self.graphs[2] = self.model_instance_adding_triple_based(graph=self.graphs[2], _subject=_subject, _triplets=_triplets)
            except Exception as _:
                log.info(str(_subject) + '\t ' + str(_predicate) + '\t' +  str(_object) + '\t' + '# AugMod : Error while updating the graph')
                    
        now = datetime.now()
        date_string = now.strftime("%m/%d/%Y at %H:%M:%S")
        log.info("Dataset '" + self.input_file  + "' is augmented of " +  "{0:.2f}".format(self.percent) + "% the " + date_string)
        return self.graphs

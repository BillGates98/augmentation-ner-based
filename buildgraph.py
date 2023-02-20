import os
import json
import pandas as pd
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import FOAF, RDF, RDFS, DC
from config import Config

class BuildGraph:
    
    def __init__(self, input_file='', output_file=''):
        self.input_file = input_file
        self.output_file = output_file
        _ , self.extension = os.path.splitext(input_file)
        print('Build Graph from Csv')

    def mapOntology(self, value=""):
        if value in ['label'] :
            return RDFS[value]
        
        if value in ['date']:
            return DC[value]
        
        return FOAF.knows
    
    def readDataFrame(self):
        ext = self.extension
        dataFrame = None
        if ext == '.json' :
            dataFrame = pd.read_json(self.input_file)
        else: 
            if ext == '.csv' : 
                dataFrame = pd.read_csv(self.input_file)
        return dataFrame
    
    def buildGraph(self):
        graph = Graph()
        dataFrame = self.readDataFrame()
        columnMapping = Config().load()['mapping_ontocolumn']
        col_subject = columnMapping['subject']
        cols_predicate = columnMapping['predicate']
        for _, row in dataFrame.iterrows():
            _subject = URIRef(row[col_subject])
            for column in cols_predicate :
                _predicate = self.mapOntology(value=cols_predicate[column])
                _object = Literal(row[column])
                graph.add((_subject, _predicate, _object))
                # print(_subject, _predicate, _object)
        graph.serialize(destination=self.output_file)
        return None
    
    def run(self):
        self.buildGraph()

BuildGraph(input_file='./inputs/formatted/query.csv', output_file='./inputs/dataset.nt').run()
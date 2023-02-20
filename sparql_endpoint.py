from rdflib import Graph , Literal, RDF, URIRef
from rdflib.namespace import RDF
from mapper import Mapper
import log
import re
from config import Config
import urllib
import requests
import json

class SparqlEndpoint: 

    def __init__(self, graph=None, subject=''):
        super().__init__()
        self.config = Config().load()
        self.subject = subject
        self.datas = []

    def threat_datas(self, datas=None):
        outputs = []
        for data in datas : 
            for binding in data['results']['bindings'] :
                tmp = {
                    'p': binding['p']['value'],
                    'o': binding['o']['value']
                }
                if not tmp in outputs :
                    outputs.append(tmp)
        return outputs

    def run_get(self, api_encoded='', headers=None):
        try:
            r = requests.get(api_encoded,  headers=headers)
            if r.status_code == requests.codes.ok :
                data_json = json.loads(r.text)
                if len(data_json['results']['bindings']) > 0 :
                    self.datas.append(data_json)
                self.datas.append(data_json)                
            else:
                raise                
        except Exception as _:
            log.error('GET #Request on the ressource ' + api_encoded + ' failed')
        return
    
    def run_post(self, api_encoded='', payload=None, headers=None):
        try:
            r = requests.post(api_encoded, headers=headers, data=payload)
            if r.status_code == requests.codes.ok :
                data_json = json.loads(r.text)
                if len(data_json['results']['bindings']) > 0 :
                    self.datas.append(data_json)
                self.datas.append(data_json)                                
            else: 
                raise
        except Exception as _:
            log.error('POST #Request on the ressource ' + api_encoded + ' failed')
        return

    def run(self):
        endpoints = self.config['endpoints']
        query = endpoints['RESOLVE_SUBJECT']['query'].replace('?dontouch', '<' + self.subject + '>')
        for endpoint in endpoints :
            _endpoint = endpoints[endpoint]
            api = _endpoint['api'].strip()
            verb = _endpoint['verb'].strip().lower()
            param = _endpoint['params'][0].strip()
            headers = _endpoint['headers'] if 'headers' in _endpoint else ''
            if int(_endpoint['status'].strip()) == 1 :
                if verb == 'get' :
                    api = api.replace(param, urllib.parse.quote(query.encode('utf-8')))
                    self.run_get(api_encoded=api)
                elif verb == 'post' :
                    payload = {}
                    payload[param] = query
                    self.run_post(api_encoded=api,payload=payload, headers=headers)
        return self.threat_datas(datas=self.datas)
        

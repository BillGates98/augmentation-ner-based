import os
from warnings import catch_warnings
from data_source import DataSource
import log
from config import Config

class Main: 

    def __init__(self, path_input='', path_output=''):
        self.path_input = path_input
        self.path_output = path_output
        self.input_files = []
        self.output_files = []
        self.extensions = ['.ttl', '.nt']
        log.info('###   Augmentation started    ###')
    
    def accept_extension(self, file='') :
        for ext in self.extensions :
            if file.endswith(ext) :
                return True
        return False
    
    def build_list_files(self):
        """
            building the list of input and output files
        """
        for current_path, folders, files in os.walk(self.path_input):
            for file in files:
                if self.accept_extension(file=file):
                    tmp_current_path = os.path.join(current_path, file)
                    self.input_files.append(tmp_current_path)
                    path = current_path.replace(self.path_input, self.path_output)
                    if not os.path.exists(path):
                        tmp_path = os.path.join(path, file)
                        self.output_files.append(tmp_path)
                        os.makedirs(path)
                    else: 
                        tmp_path = os.path.join(path, file)
                        self.output_files.append(tmp_path)
        log.info('Input Files')
        log.info(self.input_files)
        log.info('Output Files')
        log.info(self.output_files)
        return self.input_files, self.output_files

    def run(self):
        """
            Second entry point of the class after constructor
        """
        inputs, outputs = self.build_list_files()
        log.warning("Start increasing on each dataset ...")
        try :
            for i in range(len(inputs)):
                try:
                    DataSource(index=i, total=len(inputs), input_file=inputs[i], output_file=outputs[i], config=Config().load()).run()
                except UnicodeDecodeError:
                    log.error("File content errors : " + inputs[i])
                    continue
                # exit()
            log.info('End of process')
            print('End of Process')
        except RuntimeError:
            log.error("Increasing on each dataset -> Failed")

Main(path_input='./inputs/', path_output='./outputs/').run()

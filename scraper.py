class Scraper:

    def __init__(self, value='', prefix={}):
        super().__init__()
        self.value = value
        self.prefix = prefix
    
    def run(self):
        print('Scrapped')
import re
import validators

class RegexpFunction:

    def __init__(self, value = '', namespaces=[]):
        super().__init__()
        self.value = value
        self.namespaces = namespaces

    # prefix:identifier
    def function_one(self, value=''):
        """[Return the url from prefix:identifier]

        Args:
            value (str): [the value on the format prefix:identifier].

        Returns:
            [str]: [the url value]
        """
        output = value
        for prefix, url in self.namespaces :
                if prefix in output :
                    first_part = output.replace(prefix, url)
                    last_part = output.replace(prefix, '')
                    _specials_chars_detected = re.findall(r"[:^+%]", last_part)
                    if len(output) > 0 and last_part[0] in _specials_chars_detected :
                        output = first_part + last_part[1:]
                    else:
                        output = ''
                else:
                    output = ''
        return output
    
    def run(self):
        outputs = [self.function_one(value=self.value)]
        for output in outputs :
            if validators.url(output) :
                return output
        return ''
    
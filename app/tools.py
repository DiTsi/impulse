import yaml


class NoAliasDumper(yaml.Dumper):
    """
    A Dumper that does not use aliases. This is useful when you want to dump
    a data structure to a YAML file, and you don't want to use aliases to
    represent duplicate data.
    """

    def ignore_aliases(self, data):
        return True

from collections import UserDict


class AttrDict(UserDict):
    def __init__(self, mapping=None):
        super().__init__(mapping)

    def __getattr__(self, name):
        value = self.data.get(name)
        if isinstance(value, dict):
            return AttrDict(value)
        elif isinstance(value, list):
            return [AttrDict(item) if isinstance(item, dict)
                    else item for item in value]
        return self.data.get(name)

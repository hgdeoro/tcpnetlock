class Action:

    def __init__(self, action: str, params: dict):
        self.action = action
        self.params = params

    @property
    def name(self):
        return self.action

    def is_valid(self):
        # action, and param keys must be non-empty
        return \
            len(self.action) > 0 \
            and all(len(p) > 0 for p in self.params.keys())

    @classmethod
    def from_line(cls, line: str):
        action, *raw_params = line.split(',')
        params = []
        for key, *values in [p.split(':', 1) for p in raw_params]:
            if values:
                assert len(values) == 1
                param = [key.strip(), values[0].strip()]
            else:
                param = [key.strip(), '']
            params.append(param)
        return Action(action.strip(), dict(params))

    def __str__(self):
        if self.params:
            params = ', '.join(['{}:{}'.format(k, v)
                                for k, v in self.params.items()])
            return "Action: '{name}'; {params}".format(name=self.action, params=params)
        else:
            return "Action: '{name}'".format(name=self.action)

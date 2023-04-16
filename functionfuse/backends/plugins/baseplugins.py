from abc import ABC, abstractmethod


class Plugin:
    
    def local_initialize(self):
        pass

    def remote_initialize(self):
        pass
    

class InitializerPlugin(Plugin):
    def __init__(self, func):
        self._func = func

    def remote_initialize(self):
        _func = self._func
        def func():
            return _func()
        return func
    
    
class RandomStatePlugin(Plugin):
    
    def __init__(self, min, max, seed, seed_func):
        self.min, self.max = min, max
        self.seed = seed
        self.seed_func = seed_func

    def local_initialize(self):
        self.seed += 1
        if self.seed > self.max:
            self.seed = self.min

    def remote_initialize(self):
        seed = self.seed
        set_seed = self.seed_func
        def func():
            set_seed(seed)
        return func


class PluginCollection:

    def __init__(self, plugins):
        self.plugins = plugins

    def local_initialize(self):
        result = [i.local_initialize() for i in self.plugins]
        return result
    
    def remote_initialize(self):
        funcs = [i.remote_initialize() for i in self.plugins]
        def func():
            for i in funcs:
                i()
        return func








        

    


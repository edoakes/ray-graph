class Broadcast(object):
    """
    Params: a task, the number to broadcast, and args to the task
    Returns: a list of objects

    TODO: this should be able to accept other objects
    """
    def __init__(self, task, n, args=None):
        self.task = task
        self.n = n
        self.args = args

class Map(object):
    """
    Params: a task, list of objects, and args to each task
    Returns: a list of objects
    """
    def __init__(self, task, objects, args=None):
        self.task = task
        self.objects = objects
        self.args = args

class InitActors(object):
    """
    Params: an actor class, the number to init, and args to each
    Returns: a list of actors
    """
    def __init__(self, actor, n, args=None):
        self.actor = actor
        self.n = n
        self.args = args

class MapActors(object):
    """
    Params: a task, list of actors, a list of objects, and args to each task
    Returns: a list of futures (possibly null)
    """
    def __init__(self, task, actors, objects, args=None):
        self.task = task
        self.actors = actors
        self.objects = objects
        self.args = args

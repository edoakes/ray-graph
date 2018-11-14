import uuid

nodes = []

class RayIRNode(object):
    def __init__(self):
        self.id = uuid.uuid4()
        nodes.append(self)

    def short_id(self):
        return str(self.id)[:8]

    def __repr__(self):
        return self.__str__()

class Broadcast(RayIRNode):
    """
    Params: a task, the number to broadcast, and args to the task
    Returns: a list of objects

    TODO: this should be able to accept other objects
    """
    def __init__(self, task, n, args=None):
        self.task = task
        self.n = n
        self.args = args

        super(Broadcast, self).__init__()

    def __str__(self):
        return 'Broadcast(%s): %s' % (self.task, self.short_id())

class Map(RayIRNode):
    """
    Params: a task, list of objects, and args to each task
    Returns: a list of objects
    """
    def __init__(self, task, objects, args=None):
        self.task = task
        self.objects = objects
        self.args = args

        super(Map, self).__init__()

    def __str__(self):
        return 'Map(%s): %s' % (self.task, self.short_id())

class InitActors(RayIRNode):
    """
    Params: an actor class, the number to init, and args to each
    Returns: a list of actors
    """
    def __init__(self, actor, n, args=None):
        self.actor = actor
        self.n = n
        self.args = args

        super(InitActors, self).__init__()

    def __str__(self):
        return 'InitActors(%s): %s' % (self.actor, self.short_id())

class MapActors(RayIRNode):
    """
    Params: a task, list of actors, a list of objects, and args to each task
    Returns: a list of futures (possibly null)
    """
    def __init__(self, task, actors, objects, args=None):
        self.task = task
        self.actors = actors
        self.objects = objects
        self.args = args

        super(MapActors, self).__init__()

    def __str__(self):
        return 'MapActors(%s): %s' % (self.task, self.short_id())

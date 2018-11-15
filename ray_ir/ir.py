import uuid

nodes = []

def run():
    results = {}
    for node in nodes:
        node.run(results)
    return results

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
    """
    def __init__(self, task, n, *args):
        self.task = task
        self.n = n
        self.args = args

        super(Broadcast, self).__init__()

    def run(self, results):
        results[self.id] = [self.task.remote(*self.args) for _ in range(self.n)]

    def __len__(self):
        return self.n

    def __str__(self):
        return 'Broadcast(%s): %s' % (self.task._function_name, self.short_id())

class Map(RayIRNode):
    """
    Params: a task, list of objects, and args (tuples) to each task
    Returns: a list of objects
    """
    def __init__(self, task, objects, args=None):
        self.task = task
        self.objects = objects
        if args is None:
            args = [() for _ in range(len(objects))]
        self.args = args

        super(Map, self).__init__()

    def run(self, results):
        results[self.id] = [self.task.remote(results[self.objects.id][i], *self.args[i]) for i in range(len(self.args))]

    def __len__(self):
        return len(self.objects)

    def __str__(self):
        return 'Map(%s): %s' % (self.task._function_name, self.short_id())

class InitActors(RayIRNode):
    """
    Params: an actor class, the number to init, and args (tuples) to each
    Returns: a list of actors
    """
    def __init__(self, actor, n, args=None):
        self.actor = actor
        self.n = n
        if args is None:
            args = [() for _ in range(n)]
        self.args = args

        super(InitActors, self).__init__()

    def run(self, results):
        results[self.id] = [self.actor.remote(*args) for args in self.args]

    def __len__(self):
        return self.n

    def __str__(self):
        return 'InitActors(%s): %s' % (self.actor._class_name, self.short_id())

class MapActors(RayIRNode):
    """
    Params: a task, list of actors, a list of objects, and args (tuples) to each task
    Returns: a list of futures (possibly null)
    """
    def __init__(self, task, actors, objects, args=None):
        self.task = task
        self.actors = actors
        self.objects = objects
        if args is None:
            args = [() for _ in range(len(actors))]
        self.args = args

        super(MapActors, self).__init__()

    def run(self, results):
        actors = results[self.actors.id]
        objects = results[self.objects.id]
        for k,actor in enumerate(actors):
            getattr(actor, self.task).remote(objects[k], *self.args[k])

    def __len__(self):
        return len(self.actors)

    def __str__(self):
        class_name = self.actors.actor._class_name
        return 'MapActors(%s.%s): %s' % (class_name, self.task, self.short_id())

import uuid

class RayIRNode(object):
    def __init__(self):
        self.result = None
        self.id = uuid.uuid4()

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
        super(Broadcast, self).__init__()
        self.task = task
        self.n = n
        self.args = args

    def eval(self):
        if self.result is None:
            print('Evaluating: %s' % self)
            self.result = [self.task.remote(*self.args)] * self.n

        return self.result

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
        super(Map, self).__init__()
        self.task = task
        self.objects = objects
        if args is None:
            args = [[] for _ in range(len(objects))]
        elif len(args) != len(objects):
            raise ValueError('Length of args (%d) must match objects (%d)'
                             % (len(args), len(objects)))
        self.args = args

    def eval(self):
        if self.result is None:
            objs = self.objects.eval()

            print('Evaluating: %s' % self)
            self.result = []
            for i,obj in enumerate(objs):
                self.result.append(self.task.remote(*(self.args[i] + [obj])))

        return self.result

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
        super(InitActors, self).__init__()
        self.actor = actor
        self.n = n
        if args is None:
            args = [[] for _ in range(n)]
        elif len(args) != n:
            raise ValueError('Length of args (%d) must match n (%d)'
                             % (len(args), n))
        self.args = args

    def eval(self):
        if self.result is None:
            print('Evaluating: %s' % self)
            self.result = [self.actor.remote(*args) for args in self.args]

        return self.result

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
        super(MapActors, self).__init__()
        self.task = task
        self.actors = actors
        self.objects = objects
        if args is None:
            args = [[] for _ in range(len(actors))]
        elif len(args) != n:
            raise ValueError('Length of args (%d) must match actors (%d)'
                             % (len(args), len(actors)))
        self.args = args

    def eval(self):
        if self.result is None:
            actors = self.actors.eval()
            objects = self.objects.eval()

            print('Evaluating: %s' % self)
            self.result = []
            for k,actor in enumerate(actors):
                task = getattr(actor, self.task)
                self.result.append(task.remote(*(self.args[k] + objects)))

        return self.result

    def __len__(self):
        return len(self.actors)

    def __str__(self):
        class_name = self.actors.actor._class_name
        return 'MapActors(%s.%s): %s' % (class_name, self.task, self.short_id())

import json

from ray import ObjectID
from ray.utils import random_string

USE_GROUPS = False

def scheduler_free_group(group_id):
    pass

class RayIRNode(object):
    def __init__(self):
        self.results = None
        self.group_id = ObjectID(random_string())

    def short_id(self):
        return self.group_id.hex()[:8]

    def remote(self, task, args, group_id=None, group_dep=None):
        if USE_GROUPS:
            return task._remote(args, kwargs={}, group_id=group_id, group_dependency=group_dep)
        return task._remote(args, {})

    def __del__(self):
        scheduler_free_group(self.group_id)

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, key):
        assert self.results is not None
        return self.results.__getitem__(key)

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
        if self.results is None:
            print('Evaluating: %s, group %s' % (self, self.group_id))
            self.results = [self.remote(self.task, self.args, self.group_id)] * self.n

        return self.results

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
        if self.results is None:
            group_dependency = None
            if isinstance(self.objects, Broadcast):
                group_dependency = self.objects.group_id
            results = self.objects.eval()

            print('Evaluating: %s, group %s' % (self, self.group_id))
            self.results = []
            for i,obj in enumerate(results):
                self.results.append(self.remote(self.task, self.args[i] + [obj], self.group_id, group_dep=group_dependency))

        return self.results

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

    def eval(self, group_dep=None):
        if self.results is None:
            print('Evaluating: %s' % self)
            self.results = [self.remote(self.actor, args, self.group_id, group_dep) for args in self.args]

        return self.results

    def __len__(self):
        return self.n

    def __str__(self):
        return 'InitActors(%s): %s' % (self.actor._class_name, self.short_id())

class ReduceActors(RayIRNode):
    """
    Params: a task, list of actors, a list of objects, and args (tuples) to each task
    Returns: a list of futures (possibly null)
    """
    def __init__(self, task, actors, objects, args=None):
        super(ReduceActors, self).__init__()
        self.task = task
        self.actors = actors
        self.objects = objects
        if args is None:
            args = [[] for _ in range(len(actors))]
        elif len(args) != len(actors):
            raise ValueError('Length of args (%d) must match actors (%d)'
                             % (len(args), len(actors)))
        self.args = args

    def eval(self):
        if self.results is None:
            actors = self.actors.eval(self.objects.group_id)
            objects = self.objects.eval()

            print('Evaluating: %s' % self)
            self.results = []
            for i,actor in enumerate(actors):
                task = getattr(actor, self.task)
                self.results.append(self.remote(task, self.args[i] + objects, self.actors.group_id))

        return self.results

    def __len__(self):
        return len(self.actors)

    def __str__(self):
        class_name = self.actors.actor._class_name
        return 'ReduceActors(%s.%s): %s' % (class_name, self.task, self.short_id())

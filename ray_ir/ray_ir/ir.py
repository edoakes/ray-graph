import json
import uuid

def scheduler_free_task(task_id):
    pass

def scheduler_free_group(task_id):
    pass

class SchedulerHint(object):
    def __init__(self, task_id, group_id, task_dep=None, group_dep=None):
        self.task_id = task_id
        self.group_id = group_id
        self.task_dep = task_dep
        self.group_dep = group_dep

class RayIRNode(object):
    def __init__(self):
        self.results = None
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
        if self.results is None:
            print('Evaluating: %s' % self)
            self.hint = SchedulerHint(self.id, self.id)
            self.results = [(self.id, self.task.remote(*self.args))] * self.n

        return self.results

    def __del__(self):
        scheduler_free_group(self.id)
        scheduler_free_task(self.id)

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
            results = self.objects.eval()

            print('Evaluating: %s' % self)
            self.results = []
            for i,(task_dep, obj) in enumerate(results):
                task_id = uuid.uuid4()
                hint = SchedulerHint(task_id, self.id, task_dep=task_dep)
                self.results.append((task_id, self.task.remote(*(self.args[i] + [obj]))))

        return self.results

    def __del__(self):
        scheduler_free_group(self.id)
        for task_id,_ in self.results:
            scheduler_free_task(task_id)

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
        if self.results is None:
            print('Evaluating: %s' % self)
            self.results = []
            for args in self.args:
                task_id = uuid.uuid4()
                hint = SchedulerHint(task_id, self.id)
                self.results.append((task_id, self.actor.remote(*args)))

        return self.results

    def __del__(self):
        scheduler_free_group(self.id)
        for task_id,_ in self.results:
            scheduler_free_task(task_id)

    def __len__(self):
        return self.n

    def __str__(self):
        return 'InitActors(%s): %s' % (self.actor._class_name, self.short_id())

class ReduceActors(RayIRNode):
    """
    Params: a task, list of actors, a list of objects, and args (tuples) to each task
    Returns: a list of futures (possibly null)
    """
    def __init__(self, task, actors, objects, args=None, pairwise=False):
        super(ReduceActors, self).__init__()
        self.task = task
        self.actors = actors
        self.objects = objects
        self.pairwise = pairwise
        if args is None:
            args = [[] for _ in range(len(actors))]
        elif len(args) != len(actors):
            raise ValueError('Length of args (%d) must match actors (%d)'
                             % (len(args), len(actors)))
        elif pairwise and len(objects) != len(actors):
            raise ValueError('Length of objects (%d) must match actors (%d)'
                             % (len(objects), len(actors)))
        self.args = args

    def eval(self):
        if self.results is None:
            actors = self.actors.eval()
            results = self.objects.eval()
            objects = [result[1] for result in results]

            print('Evaluating: %s' % self)
            self.results = []
            for i,(_, actor) in enumerate(actors):
                task = getattr(actor, self.task)
                objs = objects[i] if self.pairwise else objects
                task_id = uuid.uuid4()
                hint = SchedulerHint(task_id, self.id, group_dep=self.objects.id)
                self.results.append((task_id, task.remote(*(self.args[i] + objects))))

        return self.results

    def __del__(self):
        scheduler_free_group(self.id)
        for task_id,_ in self.results:
            scheduler_free_task(task_id)

    def __len__(self):
        return len(self.actors)

    def __str__(self):
        class_name = self.actors.actor._class_name
        return 'ReduceActors(%s.%s): %s' % (class_name, self.task, self.short_id())

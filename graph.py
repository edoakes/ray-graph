class RayGraphNode(object):
    def __init__(self, name):
        self.name = name

class Object(RayGraphNode):
    pass

class Future(RayGraphNode):
    pass

class Actor(RayGraphNode):
    pass

class ActorHandle(RayGraphNode):
    pass

class ActorTaskInvocation(RayGraphNode):
    pass

class Get(RayGraphNode):
    pass

class Wait(RayGraphNode):
    pass

class Put(RayGraphNode):
    pass

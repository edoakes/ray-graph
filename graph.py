class RayGraphNode(object):
    def __init__(self, name, deps=None):
        self.name = name
        if deps is None:
            deps = []
        self.deps = deps

# "Grammar".
Graph = Task(Str label)
  | Actor(Str label)
  | Map(Str label, Array args) -> Array
  | Broadcast(Str label, Array args) -> Array
  | InitActors(Str label, Array args) -> ActorArray
  | MapActors(Str label, ActorArray actors, Array args) -> ActorArray, Array
  | Repeat(Value v, Int n) -> Array

Value = Array | Object
ActorArray = [ Actor ]
Array = [ (Object, ...) ]
Object = Task | Actor | python primitive

For(Graph *graphs, Int n)  # The loop body needs to return a graph or list of graphs?


# Example from mapreduce_tasks.py
reducers = InitActors("Reducer.__init__", num_reducers, args)
dependencies = Task("generate_dependencies")

maps = Broadcast("map_step", dependencies)
shuffles = Map("shuffle", maps)
reducers = MapActors("Reducer.reduce", reducers, shuffles)

# Introduction
Machine learning systems in production may require a diverse array of applications, requiring everything from hyperparameter search to train a model to stream processing to ingest data.
In the past, specialized systems have been built for each of these individual applications, leaving the burden of integrating these systems on the user, with a potentially prohibitive performance cost.
Ray is a system that makes it easy to develop and deploy applications in machine learning by exposing higher-level Python libraries for traditionally disparate applications, all supported by a common distributed framework.
Ray does this by exposing a relatively low-level API that is flexible enough to support a variety of computation patterns.
This API allows the user to define *tasks*, which represent an asynchronous and possibly remote function invocation, and *actors*, which represent some state bound to a process.

- [ed]Problem: Can we support specific applications (e.g., stream processing) with a low-level API like Ray's?
- [ed]stream processing application example

# [stephanie]Background
## Ray API
The Ray API exposes two main primitives: *tasks* to represent functional programming and *actors* to represent object-oriented programming.
A task may be specified and created as follows:
```python
@ray.remote
def random(shape):
    return np.random.rand(shape)
id1 = random.remote()
id2 = random.remote()
```
In this code example, the `ray.remote` decorator indicates that the `random` function may be run as a task.
A task can be created by calling `random.remote()`, which triggers an asynchronous and possibly remote invocation of the `random` task.
The returned *future* can be used to either get the value returned by the `random` task, or as an input to another task:
```python
@ray.remote
def dot(a, b):
  return np.dot(a, b)
id3 = dot.remote(id1, id2)  # Pass the futures as arguments to another task.
ray.get(id3)  # Returns the result of the dot task.
```

To support distributed *state*, a Ray user can also define and create an *actor*, which represents an object that is bound to a particular Python process.
When an actor is created, the user receives a *handle* to the actor that can be used to submit methods on the actor's state.
```python
@ray.remote
class Reducer(object):
    def __init__(self):
        self.value = 0
    def get(self):
        return self.value
    def add(self, value)
        self.value += value

reducer = Reducer.remote()
ray.get(reducer.get.remote())  # Returns 0.
```
Both tasks and methods called on an actor can take in and return a future, making it easy to interoperate between functions and objects.
For instance, the `reducer` actor can be used to store the results of previous `dot` tasks:
```python
reducer.add.remote(id3)
ray.get(reducer.get.remote())  # Returns the result of the dot task.
```

## Ray Architecture
- [figure]
## Stream Processing Example
- [code]
- [figure]
# Design

## [ed]Intermediate Representation
IR currently consists of 4 nodes:
- Broadcast
- Map
- InitActors
- ReduceActors

```python
def main(args):
    reducer_args = [[i] for i in range(args.num_reducers)]
    reducers = InitActors(Reducer, args.num_reducers, reducer_args)
    dependencies = Broadcast(generate_dependencies, args.num_nodes * NUM_CPUS, args.data_size)

    for _ in range(args.num_iterations):
        map_ins = dependencies
        for _ in range(args.num_maps):
            map_ins = Map(map_step, map_ins, args=[[start] for _ in range(len(map_ins))])

        shuffle_args = [[args.num_reducers, args.use_groups] for _ in range(len(map_ins))]
        shuffled = Map(shuffle, map_ins, shuffle_args)
        ReduceActors('reduce', reducers, shuffled).eval()

        time.sleep(0.1)

    latencies = ray.get([reducer.get_latencies.remote() for reducer in reducers.eval()])
```

A dependency tree is built up by passing references to new IR nodes.
Subtrees are evaluated when `node.eval()` is called on an IR node, returning the resulting Ray futures.

The IR introduces semantics between groups of submitted tasks, which we can use to make more intelligent scheduling decisions in the backend.
This semantic model mimics those of BSP systems while using a slightly extended Ray API under the hood.
Describe how dependencies are submitted from the frontend.
More details about backend in next section.

Actors can only be placed once, as they are stateful.
Semi-lazy evaluation gives us flexibility to make the actor placement intelligently.
Currently, the `InitActors` inherits its dependency from the first corresponding `ReduceActors` that's evaluated.
Could do more in the future.

## [stephanie][pseudocode]Scheduler algorithm for group scheduling

# [stephanie]Evaluation
- [figure(plot against data size, CDF)]Comparison against vanilla Ray scheduler

# [ed]Discussion/Future work
- Static analysis to automatically infer the IR from pure Ray code
  - Recognizing data dependency patterns
  - Recognizing evaluation points
- Extending the IR to support other data dependency patterns
- Designing an IR to support other features, e.g., garbage collection

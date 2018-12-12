# Introduction
Machine learning systems in production may require a diverse array of applications, requiring everything from hyperparameter search to train a model to stream processing to ingest data.
In the past, specialized systems have been built for each of these individual applications, leaving the burden of integrating these systems on the user, with a potentially prohibitive performance cost.
[Ray](https://github.com/ray-project/ray) is a system that makes it easy to develop and deploy applications in machine learning by exposing higher-level Python libraries for traditionally disparate applications, all supported by a common distributed framework.
Ray does this by exposing a relatively low-level API that is flexible enough to support a variety of computation patterns.
This API allows the user to define *tasks*, which represent an asynchronous and possibly remote function invocation, and *actors*, which represent some state bound to a process.

Although Ray's low-level API enables it to support a diverse set of distributed applications, there are often large performance gains that can be realized by exploiting a higher-level semantic model.
For example, Apache Spark leverages constrained, well-defined distributed data abstractions (i.e., RDDs and DataFrames) and operations (e.g., `map`, `join`, etc) to offer high performance and low-cost fault tolerance for MapReduce- and SQL-like computations.
This project is the first step in exploring whether it is possible to provide high performance for well-defined applications such as MapReduce and stream processing using the low-level Ray API.
To achieve high performance, we expose a scheduling interface for specifying dependencies between logically connected groups of tasks, implement a scheduling policy that uses this information, and introduce a simple intermediate representation with MapReduce semantics that takes advantage of it.
We focus on scheduling, as it has a high impact on end-to-end application performance, but this idea could be applied to other performance-critical problems, such as garbage collection.

To demonstrate the performance gains realized by group scheduling, we implement and evaluate a simple stream-processing application on top of our IR.
The application emulates receiving an input batch of data every 100MS, then transforming it through a set of stateless map and stateful reduce operations.
We chose this as a target application because it has a clear semantic model, is performance-sensitive, and is an example of something that might be done by a Ray user but is not what Ray was designed for.

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
The Ray API is relatively low-level, so a typical Ray program will often consist of a large number of tasks or actor methods of possibly short (<10ms) duration.
Therefore, the architecture is designed to scale horizontally while also reducing the computation overhead, in terms of latency per task, as much as possible.
There are two important architecture features to note for this project: (1) application data management and (2) distributed scheduling.

![Ray multinode architecture](figures/ray-architecture.jpg "Ray multinode architecture")

As Ray was originally designed for machine learning applications, interoperability with popular Python libraries like [`numpy`](http://www.numpy.org/) is a priority.
Ray also aims to make it easier to run Python programs on multicore machines.
Therefore, Ray stores application data in a shared-memory object store per node using a zero-copy format called [Apache Arrow](https://arrow.apache.org/).
Worker processes interact with the object store directly to retrieve and store task arguments and return values, respectively, allowing worker processes on the same node to efficiently share common data.

Ray uses a distributed scheduler to manage resources on a single node and across the cluster.
An instance of the scheduler runs on each node and is responsible for dispatching tasks according to the local resource availability (e.g., number of CPUs).
The scheduler is also responsible for managing each task's data dependencies and dispatching a task only when its data dependencies are local.
Data dependencies can become local if the task that creates the data executes locally, or if the scheduler fetches the data from another node.

The Ray scheduler has to contend with a number of potentially conflicting requirements.
For instance, since fetching an object incurs some delay, it is often beneficial to colocate dependent tasks.
However, achieving the best performance overall for certain workloads may require a balance between colocating tasks and global load-balancing, to account for resource capacity.
The right balance may depend on the application-specific factors such as task duration, data size, and task load.

## Stream Processing Example
- [code]
- [figure]

# Design

## Intermediate Representation
To support the target streaming application, we created an intermediate representation that supports MapReduce-style semantics.
The IR currently consists of four nodes:
- `Broadcast(task, n)`: Invokes `task` once and returns `n` handles to its result.
- `Map(task, objects)`: Invokes `task` on each object in `objects`.
- `InitActors(actor, n)`: Initializes `n` stateful actors of the type `actor`.
- `ReduceActors(task, actors, objects)`: Invokes `task` on each actor in `actors`. Each task is passed the full set of `objects`.

Each of these nodes includes optional arguments to be passed to each Ray task/actor call.
To build a Ray program using the IR, the programmer first defines Ray actors and tasks in the usual way.
These actors and tasks can then be passed into constructors of the IR nodes.
IR nodes are subsequently passed into the constructors of other IR nodes, building up a dependency tree for the application.
This dependency tree can then be "semi-lazily" by making a call to the `.eval()` method of a node, which evaluates all necessary dependencies (i.e., a subtree) and returns the result (i.e., an array of futures).

Below is the implementation of our stream-processing application using the IR:
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

    latencies = ray.get([reducer.get_latencies.remote() for reducer in reducers])
```

In this example, a set of actors is first initialized using `InitActors` and input data is initialized via `Broadcast`.
The data is then iteratively mapped, shuffled, and reduced on a 100MS cadence to emulate a stream-processing application.
Note that in each iteration, the dependency tree is explicitly evaluated using the `.eval()` call.
During the first evaluation, actors are placed, the dependendencies are created, and then the map and reduce tasks are executed.
In subsequent evaluations, only map and reduce tasks will be executed.

We use the semantics between groups of submitted tasks to pass hints to the scheduler for backend placement decisions.
In this case, each map task in the first group depends on the same object (`dependencies`), map tasks in subsequent groups each depend on a single map task from the previous group, and the reduce task depends on the entire final group of map tasks.
Details about how this information is leveraged in the scheduler are described in the following section.
In addition, the semi-lazy evaluation allows for intelligent placement of actors tasks, which is important as stateful actors cannot be moved once they are first initialized.
In this case, the actor inherits its dependency information from its first submitted reduce task.


## [stephanie][pseudocode]Group Scheduling

# [stephanie]Evaluation
- [figure(plot against data size, CDF)]Comparison against vanilla Ray scheduler

# [ed]Discussion/Future work
- Static analysis to automatically infer the IR from pure Ray code
  - Recognizing data dependency patterns
  - Recognizing evaluation points
- Extending the IR to support other data dependency patterns
- Designing an IR to support other features, e.g., garbage collection

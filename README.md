# Introduction
## Ray Intro
- [stephanie]Ray is a framework for distributed Python with a low-level API
## Problem Statement
- [ed]Problem: Can we support specific applications (e.g., stream processing) with a low-level API like Ray's?
- [ed]stream processing application example

# [stephanie]Background
## Ray API
- [code]
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

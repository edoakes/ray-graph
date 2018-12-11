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

## [ed]IR
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

A dependency tree is built up by passing references to new IR nodes. Subtrees are evaluated when .eval() is called on an IR node, returning the result (futures).
  - "Group" dependencies to mimic BSP
  - Actor scheduling
## [stephanie][pseudocode]Scheduler algorithm for group scheduling

# [stephanie]Evaluation
- [figure(plot against data size, CDF)]Comparison against vanilla Ray scheduler

# [ed]Discussion/Future work
- Static analysis to automatically infer the IR from pure Ray code
  - Recognizing data dependency patterns
  - Recognizing evaluation points
- Extending the IR to support other data dependency patterns
- Designing an IR to support other features, e.g., garbage collection

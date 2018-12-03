import ray
import time
import argparse
import numpy as np

from ray_ir import *

NUM_CPUS = 4

parser = argparse.ArgumentParser()
parser.add_argument('--num-nodes', type=int, default=1)
parser.add_argument('--num-maps', type=int, default=1)
parser.add_argument('--num-reducers', type=int, default=1)
parser.add_argument('--num-iterations', type=int, default=1)
parser.add_argument('--data-size', type=int, default=100)

def get_partition(index, element, num_reducers):
    return index % num_reducers

@ray.remote
def generate_dependencies(data_size):
    return 0, np.random.rand(data_size)

@ray.remote
def warmup(dependencies):
    time.sleep(1)


@ray.remote
def map_step(start_time, batch):
    batch = batch[1]
    out = np.array([e for e in batch])
    return start_time, batch

@ray.remote
def shuffle(num_reducers, batch):
    start_time, batch = batch
    partitions = [[] for _ in range(num_reducers)]
    for i, e in enumerate(batch):
        partitions[get_partition(i, e, num_reducers)].append(e)
    return start_time, partitions

@ray.remote
class Reducer(object):
    def __init__(self, reduce_index):
        self.reduce_index = reduce_index
        self.sum = 0
        self.latencies = []

    def reduce(self, *partitions):
        for start_time, partition in partitions:
            self.sum += sum(partition[self.reduce_index])
            self.latencies.append(time.time() - start_time)

    def get_sum(self):
        return self.sum

    def get_latencies(self):
        return self.latencies


def main(args):
    reducer_args = [[i] for i in range(args.num_reducers)]
    reducers = InitActors(Reducer, args.num_reducers, reducer_args)
    dependencies = Broadcast(generate_dependencies, args.num_nodes, args.data_size)

    for _ in range(args.num_iterations):
        start = time.time()
        map_ins = dependencies
        # Submit map tasks.
        for _ in range(args.num_maps):
            map_ins = Map(map_step, map_ins, args=[[start] for _ in range(len(map_ins))])

        # Shuffle data and submit reduce tasks.
        shuffle_args = [[args.num_reducers] for _ in range(args.num_nodes)]
        shuffled = Map(shuffle, map_ins, shuffle_args)
        ReduceActors('reduce', reducers, shuffled).eval()

        time.sleep(0.1)

    latencies = ray.get([reducer.get_latencies.remote() for reducer in reducers.eval()])
    latencies = [latency for lst in latencies for latency in lst]
    print(latencies)
    print("Avg:", sum(latencies) / len(latencies))
    print("Min:", min(latencies))
    print("Max:", max(latencies))


if __name__ == '__main__':
    args = parser.parse_args()
    ray.worker._init(
            start_ray_local=True,
            num_local_schedulers=args.num_nodes,
            num_cpus=NUM_CPUS
    )
    main(args)

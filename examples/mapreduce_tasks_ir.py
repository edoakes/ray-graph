import os
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
parser.add_argument('--data-size', type=int, default=int(1e3))
parser.add_argument('--no-dump', action='store_true')
parser.add_argument('--cluster', action='store_true')
parser.add_argument('--use-groups', action='store_true')

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
    return start_time, ray.worker.global_worker.plasma_client.store_socket_name, batch

@ray.remote
def shuffle(num_reducers, use_groups, batch):
    start_time, location, batch = batch
    if use_groups:
        assert location == ray.worker.global_worker.plasma_client.store_socket_name
    partitions = np.split(batch, range(0, len(batch), len(batch) // num_reducers)[1:])
    return start_time, [np.sum(partition) for partition in partitions]

@ray.remote
class Reducer(object):
    def __init__(self, reduce_index):
        self.reduce_index = reduce_index
        self.sum = 0
        self.latencies = []

    def reduce(self, *partitions):
        for start_time, partition in partitions:
            self.sum += partition[self.reduce_index]
            self.latencies.append(time.time() - start_time)

    def get_sum(self):
        return self.sum

    def get_latencies(self):
        return self.latencies


def main(args):
    reducer_args = [[i] for i in range(args.num_reducers)]
    reducers = InitActors(Reducer, args.num_reducers, reducer_args)
    dependencies = Broadcast(generate_dependencies, args.num_nodes * NUM_CPUS, args.data_size)

    for _ in range(args.num_iterations):
        start = time.time()
        map_ins = dependencies
        # Submit map tasks.
        for _ in range(args.num_maps):
            map_ins = Map(map_step, map_ins, args=[[start] for _ in range(len(map_ins))])

        # Shuffle data and submit reduce tasks.
        shuffle_args = [[args.num_reducers, args.use_groups] for _ in range(len(map_ins))]
        shuffled = Map(shuffle, map_ins, shuffle_args)
        ReduceActors('reduce', reducers, shuffled).eval()

        time.sleep(0.1)

    latencies = ray.get([reducer.get_latencies.remote() for reducer in reducers.eval()])
    latencies = [latency for lst in latencies for latency in lst]
    latencies = latencies[len(latencies)//5:]

    try: os.mkdir('logs')
    except: pass

    path = '{}nodes_{}maps_{}reducers_{}iterations_{}'.format(
        args.num_nodes, args.num_maps, args.num_reducers,
        args.num_iterations, args.data_size
    )

    with open(path, 'w') as f:
        print('Avg:', sum(latencies) / len(latencies))
        print('Avg:', sum(latencies) / len(latencies), file=f)
        print('Min:', min(latencies))
        print('Min:', min(latencies), file=f)
        print('Max:', max(latencies))
        print('Max:', max(latencies), file=f)
        print('')
        for l in latencies:
            print(l, file=f)

    if not args.no_dump:
        if args.use_groups:
            filename = "dump-groups.json"
        else:
            filename = "dump-no-groups.json"
        ray.global_state.chrome_tracing_dump(filename)


if __name__ == '__main__':
    args = parser.parse_args()
    if args.cluster:
        ray.init(redis_address="localhost:6379")
    else:
        ray.worker._init(
                start_ray_local=True,
                num_local_schedulers=args.num_nodes,
                num_cpus=NUM_CPUS
        )
    from ray_ir import ir
    ir.USE_GROUPS = args.use_groups
    main(args)

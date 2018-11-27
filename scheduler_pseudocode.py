# Static dictionary containing all nodes' CPU resources.
resources = {
        node_id: int,
        }


group_schedule = {
        group_id: {
            node_id: int,
            },
        }


task_schedule = {
        task_id: node_id,
        }


def get_group_placement(group_id, group_dependency):
    # Try to pack the group onto the same nodes that the dependency is on,
    # resources allowing.
    nodes = sorted(group_schedule[group_dependency].keys())
    for node in nodes:
        if group_schedule[group_id][node] < resources[node]:
            return node

    # If there is no more room left on the nodes where the dependency was,
    # then start trying to pack onto the other nodes.
    for node in sorted(resources.keys()):
        if group_schedule[group_id][node] < resources[node]:
            return node

    # If there is no more room left on any of the nodes, then load-balance
    # evenly.
    load = group_schedule[group_id]
    min_load = min(load.items(), key=lambda pair: pair[1])
    return min_load[0]


def submit_task(task, group_id=None, task_dependency=None, group_dependency=None):
    assert not (task_dependency and group_dependency)
    if task_dependency:
        node_id = task_schedule[task_dependency]
    elif group_dependency:
        node_id = get_group_placement(group_id, group_dependency)
    else:
        node_id = random.choice(resources.keys())

    task_schedule[task.id] = node_id
    if group_id is not None:
        group_scheduler[group_id][node_id] += 1

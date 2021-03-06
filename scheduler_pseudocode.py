# Static dictionary containing all nodes' CPU resources.
cluster_resources = {
        node_id: int,
        }

# The current task load on each node. This information is updated with Ray
# heartbeats and may be stale.
cluster_load = {
        node_id: int,
        }

# History of which node tasks have been placed on. Each task is
# garbage-collected when its corresponding group is freed.
task_schedule = {
        task_id: node_id,
        }

# History of which nodes a group of tasks have been placed on. Each group is
# garbage-collected when the frontend notifies the backend that the group can
# be freed.
group_schedule = {
        group_id: {
            node_id: int,
            },
        }

# History of which tasks belong in which groups. This is used to
# garbage-collect task_schedule.
groups = {
        group_id: [task_id],
        }


def get_placement_by_group(group_id, group_dependency):
    # Try to pack the group onto the same nodes that the dependency is on,
    # resources allowing.
    nodes = sorted(group_schedule[group_dependency].keys())
    for node in nodes:
        if group_schedule[group_id][node] < cluster_resources[node]:
            return node

    # If there is no more room left on the nodes where the dependency was,
    # then start trying to pack with the rest of the group.
    for node in group_schedule[group_id]:
        if group_schedule[group_id][node] < cluster_resources[node]:
            return node

    # The group has been packed as tightly as possible, so schedule according
    # to global resource load.
    return None


def place_task(task, group_id=None, task_dependency=None, group_dependency=None):
    assert not (task_dependency and group_dependency)
    node_id = None
    if task_dependency:
        node_id = task_schedule[task_dependency]
    elif group_dependency:
        node_id = get_placement_by_group(group_id, group_dependency)

    if node_is is None:
        # No scheduling decision has been made yet, so pick a node from the
        # global cluster that has the least load so far.
        min_load = min(cluster_load.items(), key=lambda pair: pair[1])
        return min_load[0]

    task_schedule[task.id] = node_id
    if group_id is not None:
        group_schedule[group_id][node_id] += 1
        groups[group_id].append(task.id]

def free_group(group_id):
    for task_id in groups[group_id]:
        del task_schedule[task_id]
    del group_schedule[group_id]
    del groups[group_id]

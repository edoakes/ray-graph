import ast

from graph import *

class RayDefParser(ast.NodeVisitor):
    """
    Parses and returns globally-defined Ray tasks and actors.

    Returns a separate dictionary of names to AST nodes for tasks and actors.
    """

    def __init__(self):
        self.tasks = {}
        self.actors = {}

    def _is_ray_def(self, decorator):
        return decorator.value.id == 'ray' and decorator.attr == 'remote'

    def visit_FunctionDef(self, node):
        for d in node.decorator_list:
            if self._is_ray_def(d):
                self.tasks[node.name] = node

    def visit_ClassDef(self, node):
        for d in node.decorator_list:
            if self._is_ray_def(d):
                self.actors[node.name] = node

    def visit_Module(self, node):
        for n in node.body:
            self.visit(n)
        return self.tasks, self.actors

class GraphParser(ast.NodeVisitor):
    """
    Base class for parsing a dependency graph from a Python AST.
    """

    def __init__(self, tasks, actors):
        self.graph = {}
        self.tasks = tasks
        self.actors = actors

class FunctionSubgraphParser(GraphParser):
    """
    Parses a dependency subgraph from a Python function.

    Returns a single graph.
    """

    # Entrypoint.
    def visit_FunctionDef(self, node):
        pass

class ActorSubgraphParser(GraphParser):
    """
    Parses a dependency subgraph for each method of a Ray actor.

    Returns a dictionary of methods to graphs.
    """

    def visit_FunctionDef(self, node):
        pass

    # Entrypoint.
    def visit_ClassDef(self, node):
        self.functions = {}
        for n in node.body:
            self.visit(n)
        return self.functions

class GlobalGraphParser(GraphParser):
    """
    Translate a Ray application file into a dependency graph.
    """

    def __init__(self, tasks, actors, function='main'):
        super().__init__(tasks, actors)
        self.function = function
        self.task_subgraphs = {}
        self.actor_subgraphs = {}
        self.actor_parser = ActorSubgraphParser(self.tasks, self.actors)
        self.function_parser = FunctionSubgraphParser(self.tasks, self.actors)

    # In the first pass, call nodes in the graph are just references. Here, we
    # expand them to include their parsed dependency information.
    def _expand_graph(self):
        pass

    def visit_FunctionDef(self, node):
        if node.name != self.function:
            return
        self.graph = FunctionSubgraphParser(self.tasks, self.actors).visit(node)

    # Entrypoint.
    def visit_Module(self, node):
        for name,n in self.tasks.items():
            self.task_graphs[name] = self.function_parser.visit(n)
        for name,n in self.actors.items():
            self.actor_subgraphs[name] = self.actor_parser.visit(n)
        for n in node.body:
            self.visit(n)

        self._expand_graph()
        return self.graph

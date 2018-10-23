import ast
import symtable

from graph import *

class GraphParser(ast.NodeVisitor):
    """
    Translate a Ray application file into a dependency graph.
    """

    def __init__(self):
        self.graph = {}
        self.task_defs = set()
        self.actor_defs = set()

    def generic_visit(self, node):
        pass

    def visit_Assign(self, node):
        pass

    def visit_If(self, node):
        for n in node.body+node.orelse:
            self.visit(n)

    def visit_For(self, node):
        for n in node.body:
            self.visit(n)

    def visit_ClassDef(self, node):
        for d in node.decorator_list:
            if d.value.id == 'ray' and d.attr == 'remote':
                self.actor_defs.add(node.name)

        for n in node.body:
            self.visit(n)

    def visit_FunctionDef(self, node):
        for d in node.decorator_list:
            if d.value.id == 'ray' and d.attr == 'remote':
                self.task_defs.add(node.name)

        for n in node.body:
            self.visit(n)

    def visit_Module(self, node):
        for n in node.body:
            self.visit(n)

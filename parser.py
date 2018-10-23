import ast
import symtable

from graph import *

class GraphParser(ast.NodeVisitor):
    """
    Translate a Ray application file into a dependency graph.
    """

    def __init__(self):
        self.graph = []
        self.sym_table = {}

    def generic_visit(self, node):
        pass

    def visit_Assign(self, node):
        pass

    def visit_If(self, node):
        pass

    def visit_For(self, node):
        pass

    def visit_Return(self, node):
        pass

    def visit_ClassDef(self, node):
        pass

    def visit_FunctionDef(self, node):
        pass

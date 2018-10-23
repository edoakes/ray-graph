import ast
import argparse
import sys

from parser import GraphParser

parser = argparse.ArgumentParser(description='Parse dependency graph from a Ray application file.')
parser.add_argument('input', help='Ray application file to parse.')

def main(args):
    with open(args.input) as fh:
        tree = ast.parse(fh.read())

    gp = GraphParser()
    gp.visit(tree)
    print(gp.graph)

if __name__ == '__main__':
    main(parser.parse_args())

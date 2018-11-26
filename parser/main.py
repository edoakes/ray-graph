import ast
import argparse
import sys

from parser import RayDefParser, GlobalGraphParser

parser = argparse.ArgumentParser(description='Parse dependency graph from a Ray application file.')
parser.add_argument('input', help='Ray application file to parse.')

def main(args):
    with open(args.input) as fh:
        tree = ast.parse(fh.read())

    tasks, actors = RayDefParser().visit(tree)
    print('tasks: %s' % tasks)
    print('actors: %s' % actors)

    graph = GlobalGraphParser(tasks, actors).visit(tree)

if __name__ == '__main__':
    main(parser.parse_args())

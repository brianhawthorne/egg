#!/usr/bin/env python
from argparse import ArgumentParser
from itertools import chain
from pkg_resources import working_set, Environment, Requirement


def clean_term(term):
    return ''.join(term.lower().split())

argparser = ArgumentParser(
    description='Show information about installed python package distributions.'
)
argparser.add_argument('terms', metavar='T', type=clean_term, nargs='*')
argparser.add_argument(
    '--list', action='store_true',
    help='show distributions matching the given terms (or all if no terms ' \
         'given)'
)
argparser.add_argument(
    '--require', action='store_true',
    help='show distributions with requirements matching the given terms (or ' \
         'all if no terms given)'
)

env = Environment()
distributions = chain.from_iterable(env[p] for p in sorted(env))

def main():
    args = argparser.parse_args()

    if args.list:
        list_action(args)

    if args.require:
        require_action(args)


def list_action(args):
    reqs = [Requirement.parse(t) for t in args.terms]
    def dist_matches(d):
        if not reqs:
            return True
        return any(d in r for r in reqs)
    print_dists_and_reqs((d,()) for d in distributions if dist_matches(d))


def require_action(args):
    if not args.terms:
        print_dists_and_reqs((d, d.requires()) for d in distributions)
        return 

    query_req = Requirement.parse(args.terms[0])

    def generate_matching_dists_and_reqs():
        for d in distributions:
            r = matching_dist_req(d, query_req)
            if r is not None:
                yield d, (r,)

    print_dists_and_reqs(generate_matching_dists_and_reqs())


def print_dists_and_reqs(dists_and_reqs):
    for d, reqs in dists_and_reqs:
        status = 'A' if d in working_set else 'i'
        print '[%s] %s-%s'% (status, d.key, d.version)
        for r in reqs:
            print '     ', r,normalize_req(r)

def matching_dist_req(dist, req):
    for r in dist.requires():
        if r.key == req.key:
            return r

def normalize_req(req):
    return req.key + ','.join(s[0]+s[1] for s in req.specs)


if __name__ == '__main__':
    main()


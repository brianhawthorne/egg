#!/usr/bin/env python
import os, sys
from zipimport import zipimporter, ZipImportError
from itertools import chain
from operator import attrgetter
from argparse import ArgumentParser
from pkg_resources import (
    working_set,
    Distribution,
    Environment,
    Requirement,
    parse_version,
    PathMetadata,
    EggMetadata,
)


def clean_term(term):
    return ''.join(term.lower().split())

argparser = ArgumentParser(
    description='Show information about installed python package distributions.'
)
argparser.add_argument('terms', metavar='T', type=clean_term, nargs='*')
argparser.add_argument(
    '-v', '--verbose', action='store_true',
    help='show all requirements of matching distributions'
)
argparser.add_argument(
    '-l', '--list', action='store_true',
    help='show distributions matching the given terms (or all if no terms ' \
         'given)'
)
argparser.add_argument(
    '-r', '--require', action='store_true',
    help='show distributions with requirements matching the given terms (or ' \
         'all if no terms given)'
)
argparser.add_argument(
    '-e', '--eggs', nargs='+',
    help='include the one or more given egg files or directories in the ' \
         'distribution pool to be searched'
)
argparser.add_argument(
    '-a', '--all', action='store_true',
    help='include installed but inactive distributions'
)



def main():
    args = argparser.parse_args()

    if args.eggs:
        distributions = compact(map(egg_dist, args.eggs))
    else:
        distributions = get_env_distributions()

    distributions = sorted(distributions, key=attrgetter('key'))

    if args.list:
        list_action(args, distributions)

    if args.require:
        require_action(args, distributions)


def list_action(args, distributions):
    reqs = [Requirement.parse(t) for t in args.terms]

    def dist_matches(d):
        if not reqs:
            return True
        return any(d in r for r in reqs)

    def generate_matching_dists_and_reqs():
        for d in distributions:
            if dist_matches(d):
                reqs = d.requires() if args.verbose else ()
                yield (d, reqs)

    print_dists_and_reqs(args, generate_matching_dists_and_reqs())


def require_action(args, distributions):
    if not args.terms:
        print_dists_and_reqs(args, [(d, d.requires()) for d in distributions])
        return 

    query_req = Requirement.parse(args.terms[0])

    def generate_matching_dists_and_reqs():
        for d in distributions:
            r = matching_dist_req(d, query_req)
            if r is not None:
                yield d, (r,)

    print_dists_and_reqs(args, generate_matching_dists_and_reqs())



def print_dists_and_reqs(args, dists_and_reqs):
    for d, reqs in dists_and_reqs:

        # Skip inactive dists unless --all was given.
        if not args.all and dist_status(d) != STATUS.ACTIVE:
            continue

        print('[%s] %s-%s'% (dist_status_label(d), d.key, d.version))
        for r in reqs:
            print('     ', normalize_req(r))


def dist_status_label(dist):
    status = dist_status(dist)
    if status == STATUS.ACTIVE:
        return '*'
    elif status == STATUS.INACTIVE:
        return ' '
    else:
        return '?'

def dist_status(dist):
    if dist_req_is_in_dists(dist, working_set):
        return STATUS.ACTIVE
    if dist_req_is_in_dists(dist, get_env_distributions()):
        return STATUS.INACTIVE
    return STATUS.UNKNOWN

class STATUS:
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    UNKNOWN = 'unknown'

def dist_req_is_in_dists(dist, dists):
    return dist.as_requirement() in [d.as_requirement() for d in dists]

def get_env_distributions():
    env = Environment()
    return list(chain.from_iterable(env[p] for p in sorted(env)))

def matching_dist_req(dist, req):
    for r in dist.requires():
        if r.key == req.key:
            return r

def normalize_req(req):
    return req.key + ','.join(s[0]+s[1] for s in req.specs)

def egg_dist(egg_path):
    metadata_func = \
        egg_path_metadata if os.path.isdir(egg_path) else egg_zip_metadata
    metadata = metadata_func(egg_path)

    if metadata is not None:
        return Distribution.from_filename(egg_path, metadata=metadata)

def egg_path_metadata(egg_path):
    return PathMetadata(egg_path, os.path.join(egg_path,'EGG-INFO'))

def egg_zip_metadata(egg_path):
    try:
        return EggMetadata(zipimporter(egg_path))
    except ZipImportError as e:
        sys.stderr.write(e.message + '\n')

def compact(iterable):
    return (item for item in iterable if item)

#------------------------------------------------------------------------------
# work in progress below
def spec_satisfies_specs(spec, specs):
    interval = interval_for_specs(specs)

def interval_for_specs(specs):
    specs = sort_specs_by_version(specs)
    ceilings = [s for s in specs if '<' in s[0]]
    floors = [s for s in specs if '<' in s[0]]

    min_ceiling = ceilings[0] if ceilings else ('<', LARGEST)
    max_floor = floors[-1] if floors else ('>', SMALLEST)
    return (max_floor, min_ceiling)

def sort_specs_by_version(specs):
    return sorted(specs, key=spec_version_sort_key)

def spec_version_sort_key(spec):
    return parse_version(spec[1])
#------------------------------------------------------------------------------


SMALLEST = None
LARGEST = type('LargestType', (), dict(__cmp__=lambda s,o: 1))


if __name__ == '__main__':
    main()


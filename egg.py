#!/usr/bin/env python
from argparse import ArgumentParser
from itertools import chain
from pkg_resources import working_set, Environment, Requirement

"""
defaults = attrdict(
    etl_type='partial',
    config_class='development',
    src_dburl='postgresql://strain:strain@localhost/strain',
    dst_dburl= \
        'mssql+mxodbc://etl_superstrain:etl_superstrain@sqletldev-datawarehouse',
    #dst_dburl='sqlite:///db/dataout-local.db',
    verbose=False,
)


optparser.add_option(
    '-t', '--type', dest='etl_type',
    help='{full | partial} [default=%s]' % defaults.etl_type)

optparser.add_option(
    '-c', '--config-class', dest='config_class',
    help='{development | staging | production} '
         '(or a prefix of one of these three) [default=%s]'
         % defaults.config_class)

optparser.add_option(
    '-s', '--src-dburl', dest='src_dburl',
    help='db URL for the source strain database [default=%s]'
         % defaults.src_dburl)

optparser.add_option(
    '-d', '--dst-dburl', dest='dst_dburl',
    help='db URL for the destination dataout database [default=%s'
         % defaults.dst_dburl)

optparser.add_option('-v', '--verbose', action='store_true',
                     dest='verbose', help='print info about what is happening')

optparser.set_defaults(**defaults)
"""


argparser = ArgumentParser(
    description='Show information about installed python package distributions.'
)
argparser.add_argument('terms', metavar='T', nargs='+')
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

def main():
    env = Environment()
    args = argparser.parse_args()
    #import ipdb; ipdb.set_trace()
    query_req = Requirement.parse(args.terms[0].lower())

    def project_matches_req(project, req):
        return any(dist_matches_req(d, req) for d in env[project])

    def dist_matches_req(dist, req):
        # consider a dist to match the req if either dist itself satisfies req
        # or one of dist's requirements satisfies req
        return req_satisfies_req(dist.as_requirement(), req) or \
               matching_dist_req(dist, req) is not None

    def matching_dist_req(dist, req):
        for r in dist.requires():
            if req_satisfies_req(r, req):
                return r

    all_distributions = chain.from_iterable(env[p] for p in sorted(env))

    def generate_matching_dists_and_reqs():
        for d in all_distributions:
            if req_satisfies_req(d.as_requirement(), query_req):
                yield d, ()
            r = matching_dist_req(d, query_req)
            if r is not None:
                yield d, (r,)

    print_dists_and_reqs(generate_matching_dists_and_reqs())



def print_dists_and_reqs(dists_and_reqs):
    for d, reqs in dists_and_reqs:
        status = 'A' if d in working_set else 'i'
        print '[%s] %s-%s'% (status, d.key, d.version)
        for r in reqs:
            print '     -',r
        print

def req_satisfies_req(r1, r2):
    """
    r1 satisfies r2 if their keys (normalized project names) match and any
    version of the project satisfying r1 also satisfies r2, ie the set of
    versions satisfying r1 is a subset of those satisfying r2, ie every one of
    r1's specs satisfies at least one of r2's specs.
    """
    return  r1.key == r2.key
    #return all(
    #    any(spec_satisfies_spec(s1,s2) for s2 in r2.specs) for s1 in r1.specs)


def spec_satisfies_spec(s1, s2):
    """
    s1 satisfies s2 if every version satisfying s1 also satisfies s2, 
    """
    op, ver = s1
    return True
    #print '         spec_satisfies_spec(%r, %r'% (s1, s2)


if __name__ == '__main__':
    main()


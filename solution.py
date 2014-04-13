#!/usr/bin/python

"""
PyCon 2014 Twitter Coding Challenge

Tim Van Steenburgh <tvansteenburgh@gmail.com>
@vansteenburglar

"""

import itertools
import unittest


OP_MERGES = {
    '<': {
        '<=': '<',
        '!=': '<' },
    '>': {
        '>=': '>',
        '!=': '>' },
    '<=': {
        '<': '<',
        '==': '==',
        '!=': '<',
        '>=': '==' },
    '>=': {
        '>': '>',
        '==': '==',
        '!=': '>',
        '<=': '==' },
    '==': {
        '<=': '==',
        '>=': '==' },
    '!=': {
        '<': '<',
        '>': '>',
        '<=': '<',
        '>=': '>' },
}


class TestSolution(unittest.TestCase):
    def test_solve(self):
        self.assertEqual(solve(''), '')
        self.assertEqual(solve('!=1'), '!=1')
        self.assertEqual(solve('>=3 !=3'), '>3')
        self.assertEqual(solve('>2 >=2.1 <4 !=4.5'), '>=2.1 <4')
        self.assertEqual(solve('>2 >=2.1 <4 !=4.5 !=3.7'), '>=2.1 !=3.7 <4')
        self.assertEqual(solve("<5.0.1 >=3.0"), ">=3.0 <5.0.1")
        self.assertEqual(solve("<3.0 <3.1"), "<3.0")
        self.assertEqual(solve(">3.0 >3.1"), ">3.1")
        self.assertEqual(solve(">2 >=2.1 <4 !=4.5"), ">=2.1 <4")
        self.assertEqual(solve(">3 >=2.1 <=4.5 !=5.0"), ">3 <=4.5")

        # Tests I failed in my original submission:

        # These first two were wrong just b/c I forgot two entries in the
        # OP_MERGES dictionary. :(
        self.assertEqual(solve('>=3 <=3.0'), '==3')
        self.assertEqual(solve('>=3.0 <=3.0.0'), '==3.0')

        # All of these I incorrectly categorized as "unsatisfiable". For some
        # reason I was thinking that if you were pinned to a specific revision
        # (e.g. ==2.1), any other <, >, <=, >= requirements would be invalid. Doh!
        self.assertEqual(solve('>=1 ==2.1.2'), '==2.1.2')
        self.assertEqual(solve('<=3 ==2.1.2'), '==2.1.2')
        self.assertEqual(solve('>=1 <=3 ==2.1.2'), '==2.1.2')
        self.assertEqual(solve('>=1 <=1'), '==1')


    def test_unsatisfiable(self):
        expected = 'unsatisfiable'
        self.assertEqual(solve('<1 >2'), expected)
        self.assertEqual(solve('<1 >1'), expected)
        self.assertEqual(solve('==1 !=1'), expected)
        self.assertEqual(solve('==1 ==2'), expected)
        self.assertEqual(solve('<3.0 ==3.1'), expected)

    def test_merge(self):
        def make_reqs(s):
            return sorted([Requirement(r) for r in s.split()])
        def string_reqs(l):
            return ' '.join([r.string for r in l])

        reqs = make_reqs('>=3')
        self.assertEqual(string_reqs(merge(reqs)), '>=3')
        reqs = make_reqs('>=3 !=3')
        self.assertEqual(string_reqs(merge(reqs)), '>3')
        reqs = make_reqs('>=3 !=3 >=4.5 ==4.5')
        self.assertEqual(string_reqs(merge(reqs)), '>3 ==4.5')
        reqs = make_reqs('>=3 !=3 !=5 >=4.5 ==4.5 !=6')
        self.assertEqual(string_reqs(merge(reqs)), '>3 ==4.5 !=5 !=6')


class TestVersion(unittest.TestCase):
    def test_cmp(self):
        self.assertTrue(Version('2.10') > Version('2.1'))
        self.assertTrue(Version('2.10') < Version('2.10.5'))
        self.assertTrue(Version('2.0') == Version('2'))
        self.assertTrue(Version('2.0.0') == Version('2.0'))
        self.assertTrue(Version('3.0.1') != Version('3.1'))


class TestRequirement(unittest.TestCase):
    def test_init(self):
        r = Requirement('!=3.0')
        self.assertEqual(r.op, '!=')
        self.assertEqual(r.version.string, '3.0')
        r = Requirement('<2')
        self.assertEqual(r.op, '<')
        self.assertEqual(r.version.string, '2')

    def test_sort(self):
        l = [
            Requirement('!=4.5'),
            Requirement('>4.6'),
            Requirement('<1.5'),
            Requirement('>=3'),
            Requirement('!=3.0'),
            ]
        expected = '<1.5 >=3 !=3.0 !=4.5 >4.6'.split()
        self.assertEqual([r.string for r in sorted(l)], expected)

    def test_merge(self):
        r1 = Requirement('<3')
        r2 = Requirement('!=3')
        r3 = r1.merge(r2)
        self.assertEqual(r3.string, '<3')


class Unsatisfiable(Exception): pass


class Version(object):
    def __init__(self, s):
        self.string = s

    def __cmp__(self, other):
        for me, other in itertools.izip_longest(
            self.string.split('.'), other.string.split('.'), fillvalue='0'):
            if me != other:
                return cmp(int(me), int(other))
        return 0


class Requirement(object):
    def __init__(self, string_req):
        self.op = None
        self.version = None
        for i, c in enumerate(string_req):
            if c.isdigit():
                self.op = string_req[:i]
                self.version = Version(string_req[i:])
                break
        if not (self.op and self.version):
            raise RuntimeError('Invalid requirement: ' + string_req)

    @property
    def string(self):
        return self.op + self.version.string

    def merge(self, other):
        if self.version != other.version:
            return None
        new_op = OP_MERGES[self.op].get(other.op)
        if new_op:
            return Requirement(new_op + self.version.string)
        raise Unsatisfiable('{} {}'.format(self.string, other.string))

    def __cmp__(self, other):
        return cmp(self.version, other.version)

    def __repr__(self):
        return self.string


def merge(reqs):
    if len(reqs) == 1:
        return reqs
    last_req = reqs[0]
    for i, cur_req in enumerate(reqs[1:]):
        if cur_req.version != last_req.version:
            last_req = cur_req
            continue
        return merge(reqs[:i] + [last_req.merge(cur_req)] + reqs[i+2:])
    return reqs


def minimize(reqs):
    if len(reqs) == 1:
        return reqs

    op_str = ' '.join([r.op for r in reqs])
    if '==' in op_str:
        found = None
        for i, req in enumerate(reqs):
            if req.op == '==':
                if found:
                    raise Unsatisfiable
                found = req
            elif ('<' in req.op and not found) or ('>' in req.op and found):
                raise Unsatisfiable
        return [found]
    
    for i, req in enumerate(reqs):
        remainder = reqs[i + 1:]
        remainder_ops = [r.op for r in remainder]
        remainder_ops_str = ' '.join(remainder_ops)
        if '<' in req.op:
            if '>' in remainder_ops_str:
                raise Unsatisfiable
            return reqs[:i + 1]
        if '>' in req.op:
            if '>' in remainder_ops_str:
                return minimize(reqs[i + 1:])
            return [reqs[i]] + minimize(reqs[i + 1:])
    return reqs


def solve(string_reqs):
    if not string_reqs:
        return string_reqs
    reqs = sorted([Requirement(r) for r in string_reqs.split()])
    try:
        reqs = merge(reqs)
        reqs = minimize(reqs)
    except Unsatisfiable:
        return 'unsatisfiable'
    return ' '.join([req.string for req in reqs])


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Version inequalities minimizer/validator")
    parser.add_argument('-t', '--test', dest='test', action='store_true',
            help='Run tests')
    options = parser.parse_args()
    if options.test:
        sys.argv = sys.argv[:1]
        unittest.main()
    else:
        print solve(raw_input('Enter version inequalities: '))

#!/usr/bin/env python3
import unittest

from bpc_factor_mixture_v31 import MixturePolicy


class Cube:
    def __init__(self,row):self.row=row
    def probabilities(self,_):return self.row
    def rotated(self):return Cube(self.row[-1:]+self.row[:-1])


class Learner:
    def __init__(self):self.factors={(1,2):Cube([.7,.1,.1,.1]),(1,3):Cube([.1,.5,.3,.1])}
    def active(self,_):return tuple(self.factors)


class FactorMixtureTest(unittest.TestCase):
    def test_probability_average_normalizes(self):
        row=MixturePolicy(Learner()).probabilities(b'')
        for actual,expected in zip(row,(.4,.3,.2,.1)):self.assertAlmostEqual(actual,expected)
        self.assertAlmostEqual(sum(row),1.)

    def test_global_drop_does_not_shift(self):
        self.assertEqual(MixturePolicy(Learner(),drop=(0,)).probabilities(b''),[.1,.5,.3,.1])


if __name__=='__main__':unittest.main()

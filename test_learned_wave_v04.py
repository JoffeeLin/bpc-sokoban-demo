#!/usr/bin/env python3
"""Fast contract checks; the full frozen experiment is intentionally separate."""
import json,unittest
from pathlib import Path

from bpc_learned_wave_v04 import parse,replay

ROOT=Path(__file__).resolve().parent


class LearnedWaveV04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads((ROOT/'artifacts/v04/result.json').read_text())
        cls.maps={x['id']:x for x in json.loads((ROOT/'holdout_v04.json').read_text())}

    def test_all_frozen_gates_pass(self):
        self.assertTrue(self.result['adopted'])
        self.assertTrue(all(self.result['gate'].values()))
        self.assertEqual(0,self.result['frozen_model_writes'])

    def test_every_published_sequence_replays(self):
        for name,outcome in self.result['conditions']['primary'].items():
            self.assertTrue(replay(parse(self.maps[name]['map']),outcome['sequence'])[0],name)

    def test_joint_relation_is_causal(self):
        validation=self.result['validation']
        self.assertEqual(688,validation['full']['box_change_correct'])
        self.assertEqual(0,validation['no_far']['box_change_correct'])
        self.assertEqual(0,sum(x['solved'] for x in self.result['conditions']['no_far'].values()))


if __name__=='__main__':unittest.main()

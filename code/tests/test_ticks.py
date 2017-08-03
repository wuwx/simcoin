from unittest import TestCase
from mock import patch
import ticks
from nodesconfig import NodeConfig


class TestIntervals(TestCase):

    def test_calc_expected_events_two_events_per_tick(self):
        expected_events = ticks.calc_expected_events(10, 0.5)

        self.assertEqual(expected_events, 70)

    def test_calc_expected_events_one_event_every_two_tick(self):
        expected_events = ticks.calc_expected_events(10, 2)

        self.assertEqual(expected_events, 25)

    def test_calc_expected_events_one_event_per_tick(self):
        expected_events = ticks.calc_expected_events(10, 1)

        self.assertEqual(expected_events, 40)

    def test_create_ticks(self):
        end = 4
        tx_per_tick = 2
        node_0 = NodeConfig('type', 'node-0', 0, 0)
        node_1 = NodeConfig('type', 'node-1', 0, 0)
        nodes = [node_0, node_1]
        block_events = {'node-0': [0.5, 2.1, end], 'node-1': [0.5, 2.1, end]}

        event_ticks = ticks.create_ticks(nodes, block_events, tx_per_tick, end)

        self.assertEqual(len(event_ticks), 4)
        self.assertEqual(len(event_ticks[0]), 4)
        self.assertEqual(len(event_ticks[1]), 2)
        self.assertEqual(len(event_ticks[2]), 4)
        self.assertEqual(len(event_ticks[3]), 2)
        self.assertTrue('tx ' in event_ticks[0][0])
        self.assertTrue('tx ' in event_ticks[1][0])
        self.assertTrue('tx ' in event_ticks[2][0])
        self.assertTrue('tx ' in event_ticks[3][0])
        self.assertTrue('block ' in event_ticks[0][2])
        self.assertTrue('block ' in event_ticks[0][3])
        self.assertTrue('block ' in event_ticks[2][2])
        self.assertTrue('block ' in event_ticks[2][3])

    def test_create_ticks_with_multiple_blocks_in_one_tick(self):
        end = 4
        node_0 = NodeConfig('type', 'node-0', 0, 0)
        block_events = {'node-0': [0.5, 0.6, end]}

        with self.assertRaises(Exception) as context:
            ticks.create_ticks([node_0], block_events, 0, end)
        self.assertTrue('Intervals per block is too low.' in str(context.exception))

    def test_create_block_series(self):
        block_events = ticks.create_block_series(0.5, 5, 10)

        self.assertEqual(len(block_events), 10)

    @patch('ticks.calc_expected_events', lambda a, b: 5)
    @patch('ticks.create_block_series', lambda a, b, c: [10, 11, 9])
    def test_create_block_events(self):
        nodes = [NodeConfig('type', 'node-0', 0.5, 0), NodeConfig('type', 'node-1', 0.5, 0)]
        amount_of_ticks = 10
        ticks_per_block = 2

        block_events = ticks.create_block_events(nodes, amount_of_ticks, ticks_per_block)
        self.assertEqual(len(block_events), 2)
        for block_events in block_events.values():
            self.assertEqual(block_events, [10, 11, 9])
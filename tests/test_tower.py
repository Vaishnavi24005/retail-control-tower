import unittest

from tower import DEMO_HOUR, analyze, scenario, simulate, zscore


class ControlTowerTest(unittest.TestCase):
    def test_start_of_day_receipt_and_lost_sales(self):
        self.assertEqual(scenario(15, 30, 2, [10, 10, 10, 10], 0), (0, None, 5))
        self.assertEqual(scenario(15, 30, 2, [10, 10, 10, 10], 2), (15, 2, 20))
        self.assertEqual(scenario(0, 20, 3, [10, 10], 0), (20, 1, 0))

    def test_zscore_constant_baseline(self):
        self.assertEqual(zscore(7, [3, 3, 3]), 4)
        self.assertEqual(zscore(3, [3, 3, 3]), 0)

    def test_fixture_and_metrics(self):
        result, (demand, inventory, shipments, snapshots, forecasts) = analyze(DEMO_HOUR, 'weekday')
        self.assertEqual((len(demand), len(inventory), len(shipments), len(snapshots), len(forecasts)),
                         (336, 4, 48, 672, 56))
        self.assertEqual(len(result['scenarios']), 32)
        self.assertEqual(len({(row['sku'], row['delay_days']) for row in result['scenarios']}), 32)
        self.assertTrue(all(row['incremental_unmet'] >= 0 for row in result['scenarios']))
        self.assertTrue(all(0 <= row['stockout_rate'] <= 1 and 0 <= row['on_time'] <= 1
                            for row in result['products']))
        self.assertEqual({(row['sku'], row['code']) for row in result['alerts']},
                         {('SKU-204', 'delivery_delay'), ('SKU-412', 'demand_spike'), ('SKU-412', 'low_cover')})
        self.assertLess(result['wape'], 0.15)

    def test_simulation_repeatable_for_same_hour(self):
        self.assertEqual(simulate(DEMO_HOUR), simulate(DEMO_HOUR))


if __name__ == '__main__':
    unittest.main()

"""Run the evidence workflow without network or Streamlit."""
import unittest

from dossier import FIELDS, add_evidence, comparison_brief, import_evidence_csv, profile_table, seed_evidence, weekly_dossier_brief
from intel import csv_bytes


class ProductWorkflowTests(unittest.TestCase):
    def test_search_source_to_card_and_recoverable_csv(self):
        initial = seed_evidence()
        source = 'https://example.org/public-product'
        updated = add_evidence(initial, {
            '产品线': 'HER2', '厂商': '示例厂商', '产品名称': '示例试剂 A',
            '信息项目': '目标试剂', '内容': '原文核对后的示例事实',
            '来源URL': source, '来源说明': '官网产品页，示例版本',
        }, reviewed=True)
        card = profile_table(updated, 'HER2')
        self.assertEqual(len(card), 1)
        self.assertEqual(card.iloc[0]['产品名称'], '示例试剂 A')
        self.assertEqual(card.iloc[0]['来源数'], 1)
        self.assertEqual(card.iloc[0]['价格与口径'], '未公开／待人工核验')

        restored, count = import_evidence_csv(initial, csv_bytes(updated[FIELDS]))
        self.assertEqual(count, 1)
        self.assertEqual(restored.iloc[-1]['证据状态'], '已人工核对原文')
        self.assertEqual(import_evidence_csv(restored, csv_bytes(updated[FIELDS]))[1], 0)
        self.assertIn(source, comparison_brief(restored, 'HER2', '示例厂商'))
        self.assertIn('未公开／待人工核验', comparison_brief(restored, 'HER2', '示例厂商'))

    def test_import_rejects_changed_schema_and_private_url(self):
        initial = seed_evidence()
        row = add_evidence(initial, {
            '产品线': 'HER2', '厂商': '示例厂商', '产品名称': '示例试剂',
            '信息项目': '目标试剂', '内容': '示例事实',
            '来源URL': 'https://example.org/public-product',
        }).iloc[[-1]].copy()
        with self.assertRaisesRegex(ValueError, '9 列'):
            import_evidence_csv(initial, csv_bytes(row.drop(columns=['来源URL'])))
        row.loc[row.index[0], '来源URL'] = 'http://127.0.0.1/private'
        with self.assertRaises(ValueError):
            import_evidence_csv(initial, csv_bytes(row[FIELDS]))

    def test_weekly_brief_counts_only_newly_reviewed_facts(self):
        initial = seed_evidence()
        empty_week = weekly_dossier_brief(initial, 'EBER/CISH')
        self.assertIn('本周新增已核对证据：0 条', empty_week)
        self.assertIn('预置演示资料不计入本周新增', empty_week)
        updated = add_evidence(initial, {
            '产品线': 'EBER/CISH', '厂商': '示例厂商',
            '产品名称': '示例试剂 X', '信息项目': '组成',
            '内容': '原文核对后的示例组成',
            '来源URL': 'https://example.org/public-product',
        }, reviewed=True)
        report = weekly_dossier_brief(updated, 'EBER/CISH')
        self.assertIn('本周新增已核对证据：1 条', report)
        self.assertIn('https://example.org/public-product', report)


if __name__ == '__main__':
    unittest.main()

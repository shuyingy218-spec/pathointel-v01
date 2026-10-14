import sys
import types
import unittest
from unittest.mock import patch

from official_search import official_vendor, search_official


class OfficialSearchTests(unittest.TestCase):
    def test_search_vendor_names_match_seeded_comparison_names(self):
        self.assertEqual(official_vendor('https://shop.leicabiosystems.com/product'), 'Leica')
        self.assertEqual(official_vendor('https://diagnostics.roche.com/product'), 'Roche')

    def test_multiword_search_rejects_one_word_finance_hits(self):
        class FakeDDGS:
            def __init__(self, timeout):
                self.timeout = timeout

            def text(self, query, max_results, backend):
                return [{'title': 'BOND EBER Probe', 'href': 'https://www.leicabiosystems.com/example', 'body': 'Leica pathology reagent'}]

        rss = [{'title': 'What is a bond?', 'href': 'https://www.investopedia.com/example', 'body': 'Bonds and finance'}]
        with patch('official_search._bing_rss', return_value=rss), patch.dict(sys.modules, {'ddgs': types.SimpleNamespace(DDGS=FakeDDGS)}):
            rows = search_official('BOND EBER')
        self.assertEqual(len(rows), 1)
        self.assertIn('leicabiosystems.com', rows[0]['链接'])

    def test_unrelated_rss_triggers_relevant_fallback(self):
        class FakeDDGS:
            def __init__(self, timeout):
                self.timeout = timeout

            def text(self, query, max_results, backend):
                return [
                    {'title': 'VENTANA EBER Probe', 'href': 'https://diagnostics.roche.com/global/en/products/lab/ventana-eber-probe.html', 'body': 'EBER probe'},
                    {'title': 'Azure migration', 'href': 'https://techcommunity.microsoft.com/example', 'body': 'cloud'},
                ]

        rss = [{'title': 'Azure migration', 'href': 'https://techcommunity.microsoft.com/example', 'body': 'cloud'}]
        with patch('official_search._bing_rss', return_value=rss), patch.dict(sys.modules, {'ddgs': types.SimpleNamespace(DDGS=FakeDDGS)}):
            rows = search_official('EBER', 'diagnostics.roche.com')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['网站域名'], 'diagnostics.roche.com')


if __name__ == '__main__':
    unittest.main()

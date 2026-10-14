import sys
import types
import unittest
from unittest.mock import patch

from official_search import official_vendor, search_official


class OfficialSearchTests(unittest.TestCase):
    def test_search_vendor_names_match_seeded_comparison_names(self):
        self.assertEqual(official_vendor('https://shop.leicabiosystems.com/product'), 'Leica')
        self.assertEqual(official_vendor('https://diagnostics.roche.com/product'), 'Roche')

    def test_multiword_search_rejects_finance_hits_then_tries_next_backend(self):
        backends = []

        class FakeDDGS:
            def __init__(self, timeout):
                self.timeout = timeout

            def text(self, query, max_results, backend):
                backends.append(backend)
                if backend == 'google':
                    return [{'title': 'What is a bond?', 'href': 'https://www.investopedia.com/example', 'body': 'Bonds and finance'}]
                return [{'title': 'BOND EBER Probe', 'href': 'https://www.leicabiosystems.com/example', 'body': 'Leica pathology reagent'}]

        with patch.dict(sys.modules, {'ddgs': types.SimpleNamespace(DDGS=FakeDDGS)}):
            rows = search_official('BOND EBER')
        self.assertEqual(backends, ['google', 'brave'])
        self.assertEqual(len(rows), 1)
        self.assertTrue(any('leicabiosystems.com' in str(value) for value in rows[0].values()))

    def test_domain_filter_keeps_only_relevant_official_page(self):
        class FakeDDGS:
            def __init__(self, timeout):
                self.timeout = timeout

            def text(self, query, max_results, backend):
                return [
                    {'title': 'VENTANA EBER Probe', 'href': 'https://diagnostics.roche.com/global/en/products/lab/ventana-eber-probe.html', 'body': 'EBER probe'},
                    {'title': 'Azure migration', 'href': 'https://techcommunity.microsoft.com/example', 'body': 'cloud'},
                ]

        with patch.dict(sys.modules, {'ddgs': types.SimpleNamespace(DDGS=FakeDDGS)}):
            rows = search_official('EBER', 'diagnostics.roche.com')
        self.assertEqual(len(rows), 1)
        self.assertTrue(any(value == 'diagnostics.roche.com' for value in rows[0].values()))


if __name__ == '__main__':
    unittest.main()

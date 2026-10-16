"""Run python test_intel.py. Only synthetic fixtures; no credentials."""
import io
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pandas as pd
from cish_excerpt import COMPARISONS, PRODUCTS
from dossier import weekly_dossier_brief
from intel import brief, csv_bytes, demo_rows, import_csv, merge_rows, normalize, search_fda, today


def check():
    demo = demo_rows()
    assert len(demo) == 3 and demo['数据性质'].eq('虚构演示').all()
    row = pd.DataFrame([{'产品名称': 'Test (fictional)', '来源URL': 'https://example.com/test', '厂商': '=1+1'}])
    manual = normalize(row, '手动录入')
    assert manual.iloc[0]['获取日期'] == today() and manual.iloc[0]['核验状态'] == '待核'
    merged, count = merge_rows(demo, manual)
    assert count == 1 and len(merged) == 4
    assert merge_rows(merged, manual)[1] == 0 and len(demo) == 3
    payload = csv_bytes(manual)
    assert payload.startswith(b'\xef\xbb\xbf') and "'=1+1" in payload.decode('utf-8-sig')
    imported = import_csv(row.to_csv(index=False).encode('utf-8'))
    assert imported.iloc[0]['来源方式'] == 'CSV导入' and imported.iloc[0]['来源URL'] == row.iloc[0]['来源URL']
    for bad in [pd.DataFrame(), row.assign(产品名称=''), row.assign(来源URL=''), row.assign(来源URL='http://127.0.0.1/test'), row.assign(来源URL='javascript:alert(1)'), row.assign(获取日期='2020-99-99')]:
        try:
            normalize(bad, '手动录入')
            raise AssertionError('invalid row accepted')
        except ValueError:
            pass
    for content in [b'', b'bad\xff', b'a'*1_000_001]:
        try:
            import_csv(content)
            raise AssertionError('invalid CSV accepted')
        except ValueError:
            pass
    for error in [URLError('offline'), HTTPError('https://api.fda.gov', 429, 'limit', {}, None)]:
        with patch('intel.urlopen', side_effect=error):
            try:
                search_fda('microscope')
                raise AssertionError('failure not handled')
            except ValueError:
                pass
    with patch('intel.urlopen', side_effect=HTTPError('https://api.fda.gov', 404, 'none', {}, None)):
        assert search_fda('nomatch').empty
    with patch('intel.urlopen', return_value=io.BytesIO(b'{"results":[{"k_number":"K123456","device_name":"Test","applicant":"Demo"}]}')):
        fetched = search_fda('microscope')
        assert fetched.iloc[0]['来源方式'] == '联网检索' and 'ID=K123456' in fetched.iloc[0]['来源URL']
        assert fetched.iloc[0]['核验状态'] == '待核'
    assert 'Test (fictional)' in brief(merged) and '示例超声' not in brief(merged)
    from streamlit.testing.v1 import AppTest
    path = str(Path(__file__).with_name('streamlit_app.py'))
    app = AppTest.from_file(path).run(timeout=30)
    assert not app.exception and len(app.tabs) == 3
    assert len(app.session_state['dossier_records']) == 13
    assert '本周新增已核对证据：0 条' in weekly_dossier_brief(app.session_state['dossier_records'], 'EBER/CISH')
    assert len(PRODUCTS) == 6 and len(COMPARISONS) == 6
    app.text_input[2].set_value('UI Test')
    app.text_input[3].set_value('Sample reagent X')
    app.text_area[0].set_value('Source-checked example composition')
    app.text_input[4].set_value('https://example.com/ui-test')
    app.checkbox[0].check()
    app.button[1].click().run(timeout=30)
    assert not app.exception and len(app.session_state['dossier_records']) == 14
    assert '本周新增已核对证据：1 条' in weekly_dossier_brief(app.session_state['dossier_records'], 'EBER/CISH')
    isolated = AppTest.from_file(path).run(timeout=30)
    assert len(isolated.session_state['dossier_records']) == 13

    source_choice = AppTest.from_file(path).run(timeout=30)
    source_choice.session_state['website_results'] = [{
        '页面标题': '示例 EBER 产品页', '网站域名': 'www.gzlbp.com',
        '来源核验': '已识别厂商域名：安必平', '搜索摘要（待核）': '仅用于界面测试',
        '链接': 'https://www.gzlbp.com/product/example',
    }]
    source_choice.run(timeout=30)
    source_choice.button(key='use-source-0').click().run(timeout=30)
    assert not source_choice.exception
    assert source_choice.session_state['ev_vendor'] == '安必平'
    assert source_choice.session_state['ev_url'] == 'https://www.gzlbp.com/product/example'
    assert any('已将厂商' in notice.value for notice in source_choice.success)
    print('PASS: source selection feedback, evidence entry, weekly brief, CSV safety, provenance, search failures/results, CISH source module and session isolation.')


if __name__ == '__main__':
    check()

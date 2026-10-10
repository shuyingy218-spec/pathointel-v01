"""Run python test_intel.py. Only synthetic fixtures; no credentials."""
import io
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pandas as pd
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
    assert not app.exception and len(app.session_state['records']) == 3
    app.text_input[0].set_value('UI Test (fictional)')
    app.text_input[4].set_value('https://example.com/ui-test')
    next(b for b in app.button if b.label == '添加公开资料').click().run()
    assert not app.exception and len(app.session_state['records']) == 4
    isolated = AppTest.from_file(path).run(timeout=30)
    assert len(isolated.session_state['records']) == 3
    app.selectbox[0].select('影像设备').run()
    assert len(app.dataframe[-1].value) == 1
    app.selectbox[1].select('手动录入').run()
    assert app.dataframe[-1].value.empty
    assert next(b for b in app.get('download_button') if b.proto.label == '导出当前筛选结果 CSV').proto.disabled
    next(b for b in app.button if b.label == '清空本会话，恢复 3 条虚构示例').click().run()
    assert len(app.session_state['records']) == 3
    print('PASS: add/import, invalid values, CSV safety, filters, dedup, provenance, search failures/results, brief, session isolation/reset.')


if __name__ == '__main__':
    check()

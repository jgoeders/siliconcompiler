import os
import siliconcompiler
from siliconcompiler.apps import sc

import pytest


@pytest.mark.eda
@pytest.mark.quick
@pytest.mark.timeout(300)
def test_self_test():
    ''' Verify self-test functionality w/ Python build script '''
    chip = siliconcompiler.Chip('')
    chip.load_target('asic_demo')
    chip.run()
    assert os.path.isfile('build/heartbeat/job0/export/0/outputs/heartbeat.gds')
    assert chip.get('metric', 'holdslack', step='export', index='1') >= 0.0
    assert chip.get('metric', 'holdslack', step='export', index='1') < 10.0
    assert chip.get('metric', 'setupslack', step='export', index='1') >= 0.0
    assert chip.get('metric', 'setupslack', step='export', index='1') < 10.0


@pytest.mark.eda
@pytest.mark.quick
@pytest.mark.timeout(300)
def test_self_test_cli(monkeypatch):
    ''' Verify self-test functionality w/ command-line call '''
    monkeypatch.setattr('sys.argv', ['sc', '-target', 'asic_demo'])
    assert sc.main() == 0

    assert os.path.isfile('build/heartbeat/job0/export/0/outputs/heartbeat.gds')
    assert os.path.isfile('build/heartbeat/job0/heartbeat.pkg.json')

    # Check timing
    chip = siliconcompiler.Chip('')
    chip.read_manifest('build/heartbeat/job0/heartbeat.pkg.json')
    assert chip.get('metric', 'holdslack', step='export', index='1') >= 0.0
    assert chip.get('metric', 'holdslack', step='export', index='1') < 10.0
    assert chip.get('metric', 'setupslack', step='export', index='1') >= 0.0
    assert chip.get('metric', 'setupslack', step='export', index='1') < 10.0


@pytest.mark.eda
@pytest.mark.timeout(900)
@pytest.mark.skip(reason="Remote calls can accidentally trigger bans")
def test_self_test_cli_remote(monkeypatch):
    ''' Verify self-test functionality w/ command-line call with remote '''
    monkeypatch.setattr('sys.argv', ['sc', '-target', 'asic_demo', '-remote', '-nodisplay'])
    assert sc.main() == 0

    assert os.path.isfile('build/heartbeat/job0/heartbeat.png')

import os
import glob

import pytest
import siliconcompiler

from siliconcompiler.apps import sc_issue
from siliconcompiler import utils


# TODO: I think moving back to something like a tarfile would be nice here to
# remove the dependency on EDA tools. Maybe make that tarfile the single source
# of truth rather than gcd.pkg.json.
@pytest.fixture(scope='module')
def heartbeat_dir(tmpdir_factory):
    '''Fixture that creates a heartbeat build directory by running a build.
    '''
    scroot = os.path.join(os.path.dirname(__file__), '..', '..')
    datadir = os.path.join(scroot, 'tests', 'data')

    cwd = str(tmpdir_factory.mktemp("heartbeat"))

    os.chdir(cwd)
    chip = siliconcompiler.Chip('heartbeat')
    chip.set('option', 'loglevel', 'ERROR')
    chip.set('option', 'quiet', True)
    chip.input(os.path.join(datadir, 'heartbeat.v'))
    chip.input(os.path.join(datadir, 'heartbeat.sdc'))
    chip.load_target('freepdk45_demo')
    chip.run()

    return cwd


@pytest.mark.parametrize('flags,outputfileglob', [
    (['-generate',
      '-cfg', 'build/heartbeat/job0/syn/0/outputs/heartbeat.pkg.json.gz'],
     'sc_issue_heartbeat_job0_syn0_*.tar.gz'),
    (['-generate',
      '-cfg', 'build/heartbeat/job0/place/0/outputs/heartbeat.pkg.json.gz',
      '-arg_step', 'syn', '-arg_index', '0'],
     'sc_issue_heartbeat_job0_syn0_*.tar.gz'),
    (['-generate',
      '-cfg', 'build/heartbeat/job0/place/0/outputs/heartbeat.pkg.json.gz',
      '-arg_step', 'place', '-arg_index', '0'],
     'sc_issue_heartbeat_job0_place0_*.tar.gz'),
    (['-generate',
      '-cfg', 'build/heartbeat/job0/heartbeat.pkg.json.gz',
      '-arg_step', 'place', '-arg_index', '0'],
     'sc_issue_heartbeat_job0_place0_*.tar.gz')
])
@pytest.mark.eda
@pytest.mark.quick
@pytest.mark.timeout(300)
def test_sc_issue_generate_success(flags, outputfileglob, monkeypatch, heartbeat_dir):
    '''Test sc-issue app on a few sets of flags.'''

    utils.copytree(heartbeat_dir, './', dirs_exist_ok=True)

    monkeypatch.setattr('sys.argv', ['sc-issue'] + flags)
    assert sc_issue.main() == 0
    assert os.path.exists(glob.glob(outputfileglob)[0])


@pytest.mark.parametrize('flags', [
    ['-generate', '-cfg', 'build/heartbeat/job0/heartbeat.pkg.json.gz']
])
@pytest.mark.eda
@pytest.mark.quick
@pytest.mark.timeout(300)
def test_sc_issue_generate_fail(flags, monkeypatch, heartbeat_dir):
    '''Test sc-issue app on a few sets of flags.'''

    utils.copytree(heartbeat_dir, './', dirs_exist_ok=True)

    monkeypatch.setattr('sys.argv', ['sc-issue'] + flags)
    assert sc_issue.main() == 1


@pytest.mark.eda
@pytest.mark.quick
@pytest.mark.timeout(300)
def test_sc_issue_run(monkeypatch, heartbeat_dir):
    '''Test sc-issue app on a few sets of flags.'''

    utils.copytree(heartbeat_dir, './', dirs_exist_ok=True)

    monkeypatch.setattr('sys.argv', ['sc-issue',
                                     '-generate',
                                     '-cfg',
                                     'build/heartbeat/job0/syn/0/outputs/heartbeat.pkg.json.gz',
                                     '-file',
                                     'sc_issue.tar.gz'])
    assert sc_issue.main() == 0

    monkeypatch.setattr('sys.argv', ['sc-issue', '-run', '-file', 'sc_issue.tar.gz'])
    assert sc_issue.main() == 0

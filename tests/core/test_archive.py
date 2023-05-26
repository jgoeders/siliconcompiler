# Copyright 2020 Silicon Compiler Authors. All Rights Reserved.
import siliconcompiler
import os
import tarfile
import pytest


def all_files(job):
    return [
        f'build/oh_parity/{job}/syn/0/syn.log',
        f'build/oh_parity/{job}/syn/0/sc_manifest.tcl',
        f'build/oh_parity/{job}/syn/0/reports/stat.json',
        f'build/oh_parity/{job}/syn/0/inputs/sc_logiclib_typical.lib',
        f'build/oh_parity/{job}/syn/0/inputs/oh_parity.v',
        f'build/oh_parity/{job}/syn/0/inputs/sc_dff_library.lib',
        f'build/oh_parity/{job}/syn/0/inputs/oh_parity.pkg.json.gz',
        f'build/oh_parity/{job}/syn/0/inputs/sc_abc.constraints',
        f'build/oh_parity/{job}/syn/0/replay.sh',
        f'build/oh_parity/{job}/syn/0/syn.errors',
        f'build/oh_parity/{job}/syn/0/syn.warnings',
        f'build/oh_parity/{job}/syn/0/outputs/oh_parity.pkg.json.gz',
        f'build/oh_parity/{job}/syn/0/outputs/oh_parity.vg',
        f'build/oh_parity/{job}/oh_parity.pkg.json.gz',
        f'build/oh_parity/{job}/import/0/reports/fake.rpt',
        f'build/oh_parity/{job}/import/0/inputs/oh_parity.pkg.json.gz',
        f'build/oh_parity/{job}/import/0/import.warnings',
        f'build/oh_parity/{job}/import/0/replay.sh',
        f'build/oh_parity/{job}/import/0/import.errors',
        f'build/oh_parity/{job}/import/0/slpp_all/file_elab.lst',
        f'build/oh_parity/{job}/import/0/slpp_all/lib/work/oh_parity.v',
        f'build/oh_parity/{job}/import/0/slpp_all/file_map.lst',
        f'build/oh_parity/{job}/import/0/slpp_all/surelog.log',
        f'build/oh_parity/{job}/import/0/slpp_all/file.lst',
        f'build/oh_parity/{job}/import/0/outputs/oh_parity.v',
        f'build/oh_parity/{job}/import/0/outputs/oh_parity.pkg.json.gz',
        f'build/oh_parity/{job}/import/0/import.log',
    ]


@pytest.fixture
def chip():
    chip = siliconcompiler.Chip('oh_parity')
    chip.set('option', 'steplist', ['import', 'syn'])
    chip.load_target('freepdk45_demo')

    for path in all_files('job0') + all_files('job1'):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'a').close()

    return chip


@pytest.mark.quick
def test_archive(chip):
    chip.archive()

    assert os.path.isfile('oh_parity_job0.tgz')

    with tarfile.open('oh_parity_job0.tgz', 'r:gz') as f:
        contents = f.getnames()

    for item in ('build/oh_parity/job0/oh_parity.pkg.json.gz',
                 'build/oh_parity/job0/import/0/reports',
                 'build/oh_parity/job0/import/0/outputs',
                 'build/oh_parity/job0/import/0/import.log',
                 'build/oh_parity/job0/syn/0/reports',
                 'build/oh_parity/job0/syn/0/outputs',
                 'build/oh_parity/job0/syn/0/syn.log'):
        assert item in contents


@pytest.mark.quick
def test_archive_step_index(chip):
    chip.archive(step='import', index='0')

    assert os.path.isfile('oh_parity_job0_import0.tgz')

    with tarfile.open('oh_parity_job0_import0.tgz', 'r:gz') as f:
        contents = f.getnames()

    for item in ('build/oh_parity/job0/oh_parity.pkg.json.gz',
                 'build/oh_parity/job0/import/0/reports',
                 'build/oh_parity/job0/import/0/outputs',
                 'build/oh_parity/job0/import/0/import.log'):
        assert item in contents

    for item in contents:
        assert not item.startswith('build/oh_parity/job0/syn')


@pytest.mark.quick
def test_archive_all(chip):
    chip.archive(include='*', archive_name='all.tgz')

    assert os.path.isfile('all.tgz')

    with tarfile.open('all.tgz', 'r:gz') as f:
        contents = f.getnames()

    for item in all_files('job0'):
        assert item in contents


@pytest.mark.quick
def test_archive_include(chip):
    chip.archive(include=['*.log', 'reports/*', 'outputs/*.pkg.json.gz'])

    assert os.path.isfile('oh_parity_job0.tgz')

    with tarfile.open('oh_parity_job0.tgz', 'r:gz') as f:
        contents = f.getnames()

    for item in ('build/oh_parity/job0/oh_parity.pkg.json.gz',
                 'build/oh_parity/job0/import/0/import.log',
                 'build/oh_parity/job0/import/0/outputs/oh_parity.pkg.json.gz',
                 'build/oh_parity/job0/syn/0/syn.log',
                 'build/oh_parity/job0/syn/0/reports/stat.json',
                 'build/oh_parity/job0/syn/0/outputs/oh_parity.pkg.json.gz'):
        assert item in contents

    for item in contents:
        if not item.endswith('oh_parity.pkg.json.gz'):
            assert 'outputs/' not in item


@pytest.mark.quick
def test_archive_jobs(chip):
    chip.archive(jobs=['job0', 'job1'])

    assert os.path.isfile('oh_parity_job0_job1.tgz')

    with tarfile.open('oh_parity_job0_job1.tgz') as f:
        contents = f.getnames()

    for item in ('build/oh_parity/job0/oh_parity.pkg.json.gz',
                 'build/oh_parity/job1/oh_parity.pkg.json.gz'):
        assert item in contents

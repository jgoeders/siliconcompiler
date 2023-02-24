from siliconcompiler.schema import Schema
from siliconcompiler.schema.schema_cfg import scparam

def test_scparam():
    cfg = {}

    # metrics
    scparam(cfg,['metric','default','default','cells','default'],
            sctype='int',
            require='asic',
            scope='job',
            shorthelp='Metric instance count',
            switch=r"-metric_cells 'step index group <int>'",
            example=[
                "cli: -metric_cells 'place 0 goal 100'",
                "api: chip.set('metric','place','0','cells','goal,'100')"],
            schelp="""
            Metric tracking the total number of instances on a per step basis.
            Total cells includes registers. In the case of FPGAs, it
            represents the number of LUTs.
            """)

    scparam(cfg,['metric','default','default','warnings','default'],
            sctype='int',
            require='all',
            scope='job',
            shorthelp='Metric total warnings',
            switch=r"-metric_warnings 'step index group <int>'",
            example=[
                "cli: -metric_warnings 'dfm 0 goal 0'",
                "api: chip.set('metric','dfm','0','warnings','real','0')"],
            schelp="""
            Metric tracking the total number of warnings on a per step basis.
            """)

    # golden version
    cfg_golden = {}

    step='default'
    index='default'
    group='default'

    cfg_golden['metric'] = {}
    cfg_golden['metric'][step] = {}
    cfg_golden['metric'][step][index] = {}

    cfg_golden['metric'][step][index]['warnings'] = {}
    cfg_golden['metric'][step][index]['warnings'][group] = {
        'switch': "-metric_warnings 'step index group <int>'",
        'type': 'int',
        'lock': False,
        'scope': 'job',
        'require': 'all',
        'defvalue': None,
        'notes': None,
        'pernode': 'never',
        'node': {},
        'shorthelp': 'Metric total warnings',
        'example': [
            "cli: -metric_warnings 'dfm 0 goal 0'",
            "api: chip.set('metric','dfm','0','warnings','real','0')"],

        'help': """Metric tracking the total number of warnings on a per step basis."""
    }

    cfg_golden['metric'][step][index]['cells'] = {}
    cfg_golden['metric'][step][index]['cells'][group] = {
        'switch': "-metric_cells 'step index group <int>'",
        'type': 'int',
        'lock': False,
        'scope': 'job',
        'require': 'asic',
        'defvalue': None,
        'notes': None,
        'pernode': 'never',
        'node': {},
        'shorthelp': 'Metric instance count',
        'example': [
            "cli: -metric_cells 'place 0 goal 100'",
            "api: chip.set('metric','place','0','cells','goal,'100')"],
        'help': """Metric tracking the total number of instances on a per step basis.\nTotal cells includes registers. In the case of FPGAs, it\nrepresents the number of LUTs."""
    }

    assert cfg == cfg_golden

def test_defvalue():
    '''Regression test that changing list-type value doesn't change defvalue.'''

    schema = Schema()
    assert schema.cfg['asic']['logiclib']['defvalue'] == []
    schema.add('asic', 'logiclib', 'mylib')
    assert schema.cfg['asic']['logiclib']['defvalue'] == []

#########################
if __name__ == "__main__":
    test_scparam()

# Copyright 2020 Silicon Compiler Authors. All Rights Reserved.
import siliconcompiler

def test_getdict():

    chip = siliconcompiler.Chip('test')
    chip.load_target('freepdk45_demo')
    localcfg = chip.getdict('pdk')

    glbl_key = siliconcompiler.Schema.GLOBAL_KEY
    assert localcfg['freepdk45']['foundry']['node'][glbl_key][glbl_key]['value'] == 'virtual'

#########################
if __name__ == "__main__":
    test_getdict()

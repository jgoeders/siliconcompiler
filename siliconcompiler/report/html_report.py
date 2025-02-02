import os
import base64
import webbrowser
import subprocess
from jinja2 import Environment, FileSystemLoader

from siliconcompiler.report.utils import _collect_data, _find_summary_image


def _generate_html_report(chip, flow, steplist, results_html):
    '''
    Generates an HTML based on the run
    '''
    templ_dir = os.path.join(chip.scroot, 'templates', 'report')

    # only report tool based steps functions
    for step in steplist.copy():
        tool, task = chip._get_tool_task(step, '0', flow=flow)
        if chip._is_builtin(tool, task):
            index = steplist.index(step)
            del steplist[index]

    env = Environment(loader=FileSystemLoader(templ_dir))
    schema = chip.schema.copy()
    schema.prune()
    pruned_cfg = schema.cfg
    if 'history' in pruned_cfg:
        del pruned_cfg['history']
    if 'library' in pruned_cfg:
        del pruned_cfg['library']

    layout_img = _find_summary_image(chip)

    img_data = None
    # Base64-encode layout for inclusion in HTML report
    if layout_img and os.path.isfile(layout_img):
        with open(layout_img, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')

    nodes, errors, metrics, metrics_unit, metrics_to_show, reports = \
        _collect_data(chip, flow, steplist)

    # Hardcode the encoding, since there's a Unicode character in a
    # Bootstrap CSS file inlined in this template. Without this setting,
    # this write may raise an encoding error on machines where the
    # default encoding is not UTF-8.
    with open(results_html, 'w', encoding='utf-8') as wf:
        wf.write(env.get_template('sc_report.j2').render(
            design=chip.design,
            nodes=nodes,
            errors=errors,
            metrics=metrics,
            metrics_unit=metrics_unit,
            reports=reports,
            manifest=chip.schema.cfg,
            pruned_cfg=pruned_cfg,
            metric_keys=metrics_to_show,
            img_data=img_data,
        ))

    chip.logger.info(f'Generated HTML report at {results_html}')


def _open_html_report(chip, results_html):
    try:
        webbrowser.get(results_html)
    except webbrowser.Error:
        # Python 'webbrowser' module includes a limited number of popular defaults.
        # Depending on the platform, the user may have defined their own with
        # $BROWSER.
        env_browser = os.getenv('BROWSER')
        if env_browser:
            subprocess.Popen([env_browser, os.path.relpath(results_html)])
        else:
            chip.logger.warning('Unable to open results page in web browser:\n'
                                f'{results_html}')

import streamlit
from streamlit_agraph import agraph, Node, Edge, Config
from streamlit_tree_select import tree_select
import streamlit_javascript
from PIL import Image
from pathlib import Path
import os
import argparse
import json
import pandas
import altair
import gzip
import base64
from siliconcompiler.report import report
from siliconcompiler import Chip, TaskStatus, utils
from siliconcompiler import __version__ as sc_version

# for flowgraph
SUCCESS_COLOR = '#8EA604'  # green
PENDING_COLOR = '#F5BB00'  # yellow, could use: #EC9F05
FAILURE_COLOR = '#FF4E00'  # red

PIXELS_PER_ROW_OF_STREAMLIT_DATAFRAME = 35.1
NODE_HEIGHT = 25

sc_logo_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'logo.png')

sc_font_path = \
    os.path.join(os.path.dirname(__file__), '..', 'data', 'RobotoMono', 'RobotoMono-Regular.ttf')

sc_about = [
    f"SiliconCompiler {sc_version}",
    '''A compiler framework that automates translation from source code to
     silicon.''',
    "https://www.siliconcompiler.com/",
    "https://github.com/siliconcompiler/siliconcompiler/"
]

sc_menu = {"Get help": "https://docs.siliconcompiler.com/",
           "Report a Bug":
           '''https://github.com/siliconcompiler/siliconcompiler/issues''',
           "About": "\n\n".join(sc_about)}

# opened by running command in siliconcompiler/apps/sc_dashboard.py
parser = argparse.ArgumentParser('dashboard')
parser.add_argument('cfg', nargs='?')
args = parser.parse_args()

if not args.cfg:
    raise ValueError('configuration not provided')

if 'job' not in streamlit.session_state:
    with open(args.cfg, 'r') as f:
        config = json.load(f)

    chip = Chip(design='')
    chip.read_manifest(config["manifest"])
    for file_path in config['graph_chips']:
        graph_chip = Chip(design='')
        graph_chip.read_manifest(file_path)
        chip.schema.cfg['history'][os.path.basename(file_path)] = graph_chip.schema.cfg

    streamlit.set_page_config(page_title=f'{chip.design} dashboard',
                              page_icon=Image.open(sc_logo_path), layout="wide",
                              menu_items=sc_menu)
    streamlit.session_state['master chip'] = chip
    streamlit.session_state['job'] = 'default'
    new_chip = chip
    streamlit.session_state['transpose'] = False
else:
    chip = streamlit.session_state['master chip']
    streamlit.set_page_config(page_title=f'{chip.design} dashboard',
                              page_icon=Image.open(sc_logo_path), layout="wide",
                              menu_items=sc_menu)
    new_chip = Chip(design='')
    job = streamlit.session_state['job']
    if job == 'default':
        new_chip = chip
    else:
        new_chip.schema = chip.schema.history(job)
        new_chip.set('design', chip.design)


def _convert_filepaths(logs_and_reports):
    """
    Converts the logs_and_reports found to the structure
    required by streamlit_tree_select. Success is predicated on the order of
    logs_and_reports outlined in report.get_files.

    Args:
        logs_and_reports (list) : A list of 3-tuples with order of a path name,
            folder in the..., and files in the....
    """
    subsect_logs_and_reports = {}
    if not logs_and_reports:
        return []
    starting_path_name = logs_and_reports[0][0]
    # reverse the list to start building the tree from the leaves up
    for path_name, folders, files in reversed(logs_and_reports):
        children = []
        for folder in folders:
            children.append(subsect_logs_and_reports[folder])
        for file in files:
            node = {}
            node['label'] = file
            node['value'] = f'{path_name}/{file}'
            children.append(node)
        if starting_path_name == path_name:
            return children
        else:
            node = {}
            folder = Path(path_name).name
            node['label'] = folder
            node['value'] = path_name
            node['children'] = children
            subsect_logs_and_reports[folder] = node


def get_nodes_and_edges(chip, node_dependencies, successful_path,
                        successful_path_node_opacity=1, successful_path_node_width=3,
                        successful_path_edge_width=5, default_node_opacity=0.2,
                        default_node_border_width=1, default_edge_width=3):
    """
    Returns the nodes and edges required to make a streamlit_agraph.

    Args:
        chip (Chip) : The chip object that contains the schema read from.
        node_dependencies (dict) : Dictionary mapping nodes
            (as tuples of step/index) to their input nodes.
        successful_path (set) : Contains all the nodes that are part of the
            'winning' path.
        succesful_path_node_opacity (float) : A number between 0 and 1
            (inclusive) which represents the opacity for nodes on a successful
            path.
        succesful_path_node_border_width (int) : A number between 0 or greater
            which represents the width for nodes on a successful path.
        succesful_path_edge_width (int) : A number between 0 or greater which
            represents the width for edges on a successful path.
        default_node_opacity (float) : A number between 0 and 1(inclusive)
            which represents the opacity for nodes of a node not on a
            successful path.
        default_node_border_width (int) : A number between 0 or greater
            which represents the width for nodes not on a successful path.
        default_edge_width (int) : A number between 0 or greater which
            represents the width for edges not on a successful path.
    """
    nodes = []
    edges = []
    for step, index in node_dependencies:
        node_opacity = default_node_opacity
        node_border_width = default_node_border_width
        if (step, index) in successful_path:
            node_opacity = successful_path_node_opacity
            if (step, index) in chip._get_flowgraph_exit_nodes() or \
               (step, index) in chip._get_flowgraph_entry_nodes():
                node_border_width = successful_path_node_width
        flow = chip.get("option", "flow")
        task_status = chip.get('flowgraph', flow, step, index, 'status')
        if task_status == TaskStatus.SUCCESS:
            node_color = SUCCESS_COLOR
        elif task_status == TaskStatus.ERROR:
            node_color = FAILURE_COLOR
        else:
            node_color = PENDING_COLOR
        tool, task = chip._get_tool_task(step, index)
        node_name = f'{step}{index}'
        label = node_name + "\n" + tool + "/" + task
        if chip._is_builtin(tool, task):
            label = node_name + "\n" + tool
        nodes.append(Node(id=node_name, label=label, color=node_color, opacity=node_opacity,
                          borderWidth=node_border_width, shape='oval'))
        for source_step, source_index in node_dependencies[step, index]:
            edge_width = default_edge_width
            if (source_step, source_index) in successful_path and \
               (source_step, source_index) in successful_path:
                edge_width = successful_path_edge_width
            edges.append(Edge(source=source_step + source_index, dir='up', target=node_name,
                              width=edge_width, color='black', curve=True))
    return nodes, edges


def file_viewer_module(display_file_content, chip, step, index, header_col_width=0.89):
    """
    Displays the file if present. If not, displays an error message.

    Args:
        display_file_content (bool) : True if there is a file selected to display
        header_col_width (float) : A number between 0 and 1 which is the
            percentage of the width of the screen given to the header. The rest
            is given to the download button.
    """
    if not display_file_content:
        streamlit.header('File Viewer', anchor='file_viewer')
        streamlit.error('Select a file in the metrics tab first!')
        return
    path = streamlit.session_state['selected'][0]
    # This file extension may be '.gz', if it is, it is compressed.
    file_name, compressed_file_extension = os.path.splitext(path)
    # This is the true file_extension of the file, regardless of if it is
    # compressed or not.
    file_extension = utils.get_file_ext(path)
    relative_path = os.path.relpath(path, chip._getworkdir(step=step, index=index))
    header_col, download_col = \
        streamlit.columns([header_col_width, 1 - header_col_width], gap='small')
    with header_col:
        streamlit.header(relative_path, anchor='file_viewer')
    with download_col:
        streamlit.markdown(' ')  # aligns download button with title
        streamlit.download_button(label="Download file",
                                  data=path,
                                  file_name=relative_path)
    if file_extension.lower() in {".png", ".jpg"}:
        streamlit.image(path)
    else:
        try:
            if compressed_file_extension == '.gz':
                fid = gzip.open(path, 'rt')
            else:
                fid = open(path, 'r')
            content = fid.read()
            fid.close()
            if file_extension.lower() == ".json":
                streamlit.json(content)
            else:
                streamlit.code(content, language='markdown', line_numbers=True)
        except UnicodeDecodeError:  # might be OSError, not sure yet
            streamlit.markdown('Cannot read file')


def show_files(chip, step, index):
    """
    Displays the logs and reports using streamlit_tree_select.

    Args:
        chip (Chip) : the chip object that contains the schema read from.
        step (string) : step of node.
        index (string) : index of node.
    """
    streamlit.caption('files')
    logs_and_reports = report.get_files(chip, step, index)
    logs_and_reports = _convert_filepaths(logs_and_reports)
    if logs_and_reports == []:
        streamlit.markdown('No files to show')
        return False
    # kinda janky at the moment, does not always flip immediately
    # TODO make so that selection changes on first click
    if "selected" not in streamlit.session_state:
        streamlit.session_state['selected'] = []
    if "expanded" not in streamlit.session_state:
        streamlit.session_state['expanded'] = []

    selected = tree_select(logs_and_reports,
                           expand_on_click=True,
                           checked=streamlit.session_state['selected'],
                           expanded=streamlit.session_state['expanded'],
                           only_leaf_checkboxes=True)
    # only include files in 'checked' (folders are also included when they are opened)
    selected['checked'] = [x for x in selected['checked'] if os.path.isfile(x)]
    if len(selected['checked']) == 0:
        streamlit.session_state['selected'] = []
    if len(selected["checked"]) == 1:
        streamlit.session_state['selected'] = selected["checked"]
    if len(selected["checked"]) > 1:
        for x in selected["checked"]:
            if x != streamlit.session_state['selected'][0]:
                newly_selected = x
                break
        streamlit.session_state['selected'] = [newly_selected]
        streamlit.session_state['expanded'] = selected["expanded"]
        streamlit.session_state['right after rerun'] = True
        streamlit.experimental_rerun()
    if streamlit.session_state.selected != []:
        return True, *streamlit.session_state['selected']
    return False, None


def show_metrics_for_file(chip, step, index):
    """
    Displays the metrics that are included in each file.

    Args:
        chip (Chip) : The chip object that contains the schema read from.
        step (string) : Step of node.
        index (string) : Index of node.
    """
    if 'selected' in streamlit.session_state and \
       len(streamlit.session_state['selected']) == 1:
        file = streamlit.session_state['selected'][0]
        metrics_of_file = report.get_metrics_source(chip, step, index)
        file = os.path.relpath(file, f"/{step}/{index}")
        if file in metrics_of_file:
            metrics = ", ".join(metrics_of_file[file]) + "."
            streamlit.success("This file includes the metrics of " + metrics)
        else:
            streamlit.warning("This file does not include any metrics.")


def manifest_module(chip, manifest, ui_width, max_num_of_keys_to_show=20,
                    default_toggle_width_in_percent=0.2, default_toggle_width_in_pixels=200,
                    header_col_width=0.85):
    """
    Displays the manifest and a way to search through the manifest.

    Args:
        chip (Chip) : The chip object that contains the schema read from.
        manifest (dict) : Represents the manifest json.
        ui_width (int) : The width of the screen of the web browser in pixels.
        max_num_of_keys_to_show (int) : The maximum number of keys that the
            manifest may have in order to be automatically expanded.
        default_toggle_width_in_percent (float) : A number between 0 and 1
            which is the maximum percentage of the width of the screen given to
            the checkbox. The rest is given to the search bars.
        default_toggle_width_in_pixels (int) : A number greater than 0 which
            is the maximum pixel width of the screen given to the checkbox. The
            rest is given to the search bars.
        header_col_width (float) : A number between 0 and 1 which is the maximum
            percentage of the width of the screen given to the header. The rest
            is given to the download button.
    """
    # TODO include toggle to expand the tree, find less redundant header name
    header_col, download_col = streamlit.columns([header_col_width, 1 - header_col_width],
                                                 gap='small')
    with header_col:
        streamlit.header('Manifest', anchor='manifest')
    if ui_width > 0:
        toggle_col_width_in_percent = \
            min(default_toggle_width_in_pixels / ui_width, default_toggle_width_in_percent)
    else:
        toggle_col_width_in_percent = default_toggle_width_in_percent
    search_col_width = (1 - toggle_col_width_in_percent) / 2
    key_search_col, value_search_col, toggle_col = \
        streamlit.columns([search_col_width, search_col_width,
                           toggle_col_width_in_percent], gap="large")
    with toggle_col:
        # to align the checkbox with the search bars
        streamlit.markdown('')
        streamlit.markdown('')
        if streamlit.checkbox('Raw manifest',
                              help='Click here to see the JSON before it was made more readable'):
            manifest_to_show = chip.schema.cfg
        else:
            manifest_to_show = manifest
    with key_search_col:
        key = streamlit.text_input('Search Keys', '', placeholder="Keys")
        if key != '':
            manifest_to_show = report.search_manifest(manifest_to_show, key_search=key)
    with value_search_col:
        value = streamlit.text_input('Search Values', '', placeholder="Values")
        if value != '':
            manifest_to_show = report.search_manifest(manifest_to_show, value_search=value)
    with download_col:
        streamlit.markdown(' ')  # aligns download button with title
        streamlit.download_button(label='Download manifest', file_name='manifest.json',
                                  data=json.dumps(manifest_to_show, indent=4),
                                  mime="application/json")
    numOfKeys = report.get_total_manifest_key_count(manifest_to_show)
    streamlit.json(manifest_to_show, expanded=(numOfKeys < max_num_of_keys_to_show))


def select_nodes(metric_dataframe, node_from_flowgraph):
    """
    Displays selectbox for nodes to show in the node information panel. Since
    both the flowgraph and selectbox show which node's information is
    displayed, the one clicked more recently will be displayed.

    Args:
        metric_dataframe (Pandas.DataFrame) : Contains the metrics of all
            nodes.
        node_from_flowgraph (string/None) : Contains a string of the node to
            display or None if none exists.
    """
    option = metric_dataframe.columns.tolist()[0]
    with streamlit.expander("Select Node"):
        with streamlit.form("nodes"):
            option = streamlit.selectbox('Pick a node to inspect',
                                         metric_dataframe.columns.tolist())
            params_submitted = streamlit.form_submit_button()
            if not params_submitted and node_from_flowgraph is not None:
                option = node_from_flowgraph
                streamlit.session_state['selected'] = []
            if params_submitted:
                streamlit.session_state['selected'] = []
    return option


def metrics_dataframe_module(metric_dataframe):
    """
    Displays multi-select check box to the users which allows them to select
    which nodes and metrics to view in the dataframe.

    Args:
        metric_dataframe (Pandas.DataFrame) : Contains the metrics of all
            nodes.
    """
    show_dataframe_header()
    container = streamlit.container()
    transpose = streamlit.session_state['transpose']
    if transpose:
        metric_dataframe = metric_dataframe.transpose()
        metrics_list = metric_dataframe.columns.tolist()
        node_list = metric_dataframe.index.tolist()
    else:
        metrics_list = metric_dataframe.index.tolist()
        node_list = metric_dataframe.columns.tolist()
    display_to_data = {}
    display_options = []
    for metric_unit in metrics_list:
        metric = metric_to_metric_unit_map[metric_unit]
        display_to_data[metric] = metric_unit
        display_options.append(metric)
    options = {'metrics': [], 'nodes': []}
    # pick parameters
    with streamlit.expander("Select Parameters"):
        with streamlit.form("params"):
            nodes = streamlit.multiselect('Pick nodes to include', node_list, [])
            options['nodes'] = nodes
            metrics = streamlit.multiselect('Pick metrics to include?', display_options, [])
            options['metrics'] = []
            for metric in metrics:
                options['metrics'].append(display_to_data[metric])
            streamlit.form_submit_button("Run")
    if not options['nodes']:
        options['nodes'] = node_list
    if not options['metrics']:
        options['metrics'] = metrics_list
    # showing the dataframe
    # TODO By July 2024, Streamlit will let catch click events on the dataframe
    if transpose:
        container.dataframe((metric_dataframe.loc[options['nodes'], options['metrics']]),
                            use_container_width=True)
    else:
        container.dataframe((metric_dataframe.loc[options['metrics'], options['nodes']]),
                            use_container_width=True)


def show_dataframe_header(header_col_width=0.7):
    """
    Displays the header and toggle for the dataframe. If the toggle is flipped,
    it will update the view of the dataframe accordingly.

    Args:
        header_col_width (float) : A number between 0 and 1 which is the
            percentage of the width of the screen given to the header. The rest
            is given to the transpose toggle.
    """
    header_col, transpose_col = streamlit.columns([header_col_width, 1 - header_col_width],
                                                  gap="large")
    with header_col:
        streamlit.header('Metrics', anchor='metrics')
    with transpose_col:
        streamlit.markdown('')
        streamlit.markdown('')
        streamlit.session_state['transpose'] = \
            streamlit.checkbox('Transpose', help='Click here to see the table transposed')


def display_flowgraph_toggle(label_after, vertical_layout_collapsed=False):
    """
    Displays the toggle for the flowgraph.

    Args:
        label_after (bool) : the default label for the toggle
        vertical_layout_collapsed (bool) : If vertical_layout_collapsed,
            there is no need to align the toggle with the header
    """
    if not vertical_layout_collapsed:
        # this horizontally aligns the toggle with the header
        streamlit.markdown("")
        streamlit.markdown("")
    fg_toggle = not streamlit.checkbox('Hide flowgraph', help='Click here to hide the flowgraph')
    streamlit.session_state['flowgraph'] = fg_toggle
    if streamlit.session_state['flowgraph'] != label_after:
        streamlit.session_state['right after rerun'] = True
        streamlit.experimental_rerun()


def show_flowgraph(chip):
    '''
    This function creates, displays, and returns the selected node of the flowgraph.

    Args:
        chip (Chip) : The chip object that contains the schema read from.
    '''
    nodes, edges = get_nodes_and_edges(chip, report.get_flowgraph_edges(chip),
                                       report.get_flowgraph_path(chip))
    config = Config(width='100%', directed=True, physics=False, hierarchical=True,
                    clickToUse=True, nodeSpacing=150, levelSeparation=100,
                    sortMethod='directed')
    node_from_flowgraph = agraph(nodes=nodes, edges=edges, config=config)
    return node_from_flowgraph


def show_title():
    streamlit.markdown(
        '''
        <head>
            <style>
                /* Define the @font-face rule */
                @font-face {
                font-family: 'Roboto Mono';
                src: url(sc_font_path) format('truetype');
                font-weight: normal;
                font-style: normal;
                }

                /* Styles for the logo and text */
                .logo-container {
                display: flex;
                align-items: flex-start;
                }

                .logo-image {
                margin-right: 10px;
                margin-top: -10px;
                }

                .logo-text {
                display: flex;
                flex-direction: column;
                margin-top: -20px;
                }

                .text1 {
                color: #F1C437; /* Yellow color */
                font-family: 'Roboto Mono', sans-serif;
                font-weight: 700 !important;
                font-size: 30px !important;
                margin-bottom: -16px;
                }

                .text2 {
                color: #1D4482; /* Blue color */
                font-family: 'Roboto Mono', sans-serif;
                font-weight: 700 !important;
                font-size: 30px !important;
                }

            </style>
        </head>''',
        unsafe_allow_html=True
    )
    streamlit.markdown(
        f'''
        <body>
            <div class="logo-container">
                <img src="data:image/png;base64,{base64.b64encode(open(sc_logo_path,
                "rb").read()).decode()}" alt="Logo Image" class="logo-image" height="61">
                <div class="logo-text">
                    <p class="text1">{streamlit.session_state['master chip'].design}</p>
                    <p class="text2">dashboard</p>
                </div>
            </div>
        </body>
        ''',
        unsafe_allow_html=True
    )


def show_runs():
    all_jobs = streamlit.session_state['master chip'].getkeys('history')
    all_jobs.insert(0, 'default')
    job = streamlit.selectbox('pick a job', all_jobs,
                                label_visibility='collapsed')
    previous_job = streamlit.session_state['job']
    streamlit.session_state['job'] = job
    if previous_job != job:
        streamlit.session_state['right after rerun'] = True
        streamlit.experimental_rerun()


def show_title_and_runs(title_col_width=0.7):
    """
    Displays the title and a selectbox that allows you to select a given run
    to inspect.

    Args:
        title_col_width (float) : A number between 0 and 1 which is
            the percentage of the width of the screen given to the title and
            logo. The rest is given to selectbox.
    """
    title_col, job_select_col = \
        streamlit.columns([title_col_width, 1 - title_col_width], gap="large")
    with title_col:
        show_title()
    with job_select_col:
        show_runs()
    return new_chip


def show_metric_and_node_selection_for_graph(metrics, nodes, graph_number):
    """
    Displays selectbox for metrics and nodes which informs the graph on what
    to display.

    Args:
        metrics (list) : A list of metrics that are set for all chips given in
            chips.
        nodes (list) : A list of nodes given in the form f'{step}{index}'
        graph_number (int) : The number of graphs there are. Used to create
            keys to distinguish selectboxes from each other.
    """
    metric_selector_col, node_selector_col = streamlit.columns(2, gap='small')
    with metric_selector_col:
        with streamlit.expander('Select a Metric'):
            selected_metric = streamlit.selectbox('Select a Metric', metrics,
                                                  label_visibility='collapsed',
                                                  key=f'metric selection {graph_number}')
    with node_selector_col:
        with streamlit.expander('Select Nodes'):
            selected_nodes = \
                streamlit.multiselect('Select a Node', nodes, label_visibility='collapsed',
                                      key=f'node selection {graph_number}', default=nodes[0])
    return selected_metric, selected_nodes


def show_graph(data, x_axis_label, y_axis_label, color_label, height=300):
    """
    Displays a graph with the given "data" on the y-axis and "jobs" on the x-axis.

    Args:
        data (Pandas.DataFrame) : A dataframe containing all the graphing data.
        x_axis_label (string) : The name of the runs column.
        y_axis_label (string) : The name of the jobs column.
        color_label (string) : The name of the nodes column.
        height (int) : The height of one graph.
    """
    x_axis = altair.X(x_axis_label, axis=altair.Axis(labelAngle=-75))
    y_axis = y_axis_label
    color = color_label
    chart = altair.Chart(data, height=height).mark_line(point=True).encode(x=x_axis, y=y_axis,
                                                                           color=color)
    streamlit.altair_chart(chart, use_container_width=True, theme='streamlit')


def select_runs(jobs):
    """
    Displays a dataframe that can be edited to select specific jobs to include
    in the analysis.

    Args:
        jobs (list) : A list of job names.
    """
    all_jobs = pandas.DataFrame({'job names': jobs, 'selected jobs': [True] * len(jobs)})
    configuration = {'selected jobs': streamlit.column_config.CheckboxColumn('Select runs',
                                                                             default=True)}
    filtered_jobs = streamlit.data_editor(all_jobs, disabled=['job names'],
                                          use_container_width=True, hide_index=True,
                                          column_config=configuration)
    return filtered_jobs


def structure_graph_data(chips, metric, selected_jobs, nodes):
    """
    Displays a graph and it's corresponding metric and node selection.

    Args:
        chips (list) : A list of tuples in the form (chip, chip name) where
            the chip name is a string.
        metric (string) : The metric to be inspected.
        selected_jobs (pandas.DataFrame) : A dataframe with a column called
            'selected jobs' which idenitfies which jobs the user wants to see
            and a corresponding column called 'job names'.
        nodes (list) : A list of dictionaries with the form (step, index).
    """
    x_axis_label = 'runs'
    y_axis_label = metric
    color_label = 'nodes'
    if not nodes:
        show_graph(pandas.DataFrame({x_axis_label: [], y_axis_label: [], color_label: []}),
                   x_axis_label, y_axis_label, color_label)
        return
    data, metric_unit = report.get_chart_data(chips, metric, nodes)
    if metric_unit:
        y_axis_label = f'{metric}({metric_unit})'
    filtered_data = {x_axis_label: [], y_axis_label: [], color_label: []}
    # filtering through data
    for is_selected, job_name in zip(selected_jobs['selected jobs'].tolist(),
                                     selected_jobs['job names'].tolist()):
        if is_selected:
            for step, index in data:
                filtered_data[x_axis_label].append(job_name)
                filtered_data[color_label].append(step + index)
                if job_name not in data[(step, index)].keys():
                    filtered_data[y_axis_label].append(None)
                else:
                    filtered_data[y_axis_label].append(data[(step, index)][job_name])
    show_graph(pandas.DataFrame(filtered_data).dropna(), x_axis_label, y_axis_label, color_label)


def flowgraph_layout_vertical_flowgraph(chip, ui_width):
    '''
    This function dynamically calculates what the flowgraph's width should be.
    This function is specific to the vertical_flowgraph layout. It returns the
    node selected from the flowgraph and the column for the metric section and
    node information section.

    Args:
        chip (Chip) : The chip object that contains the schema read from.
        ui_width (int) : The width of the browser in terms of pixels.
    '''
    if streamlit.session_state['flowgraph']:
        default_flowgraph_width_in_percent = 0.4
        flowgraph_col_width_in_pixels = 520
        if ui_width > 0:
            flowgraph_col_width_in_percent = \
                min(flowgraph_col_width_in_pixels / ui_width, default_flowgraph_width_in_percent)
        else:
            flowgraph_col_width_in_percent = default_flowgraph_width_in_percent
        flowgraph_col, dataframe_and_node_info_col = \
            streamlit.columns([flowgraph_col_width_in_percent,
                               1 - flowgraph_col_width_in_percent], gap="large")
        with flowgraph_col:
            header_col, toggle_col = streamlit.columns(2, gap="large")
            with header_col:
                streamlit.header('Flowgraph')
            with toggle_col:
                display_flowgraph_toggle(True)
            node_from_flowgraph = show_flowgraph(chip)
    else:
        display_flowgraph_toggle(False)
        dataframe_and_node_info_col = streamlit.container()
        node_from_flowgraph = None
    return node_from_flowgraph, dataframe_and_node_info_col


def node_metric_dataframe(node_name, metrics, height=None):
    '''
    Displays the node metric dataframe.

    Args:
        node_name (string) : The name of the node selected.
        metrics (pandas.DataFrame) : The metrics for the node corresponding with
            node_name with the Null values removed.
        height (int or None) : The height of the dataframe. If None, streamlit
            automatically calculates it.
    '''
    streamlit.subheader(f'{node_name} Metrics')
    streamlit.dataframe(metrics, use_container_width=True, height=height)


def node_details_dataframe(chip, step, index, height=None):
    '''
    Displays the node details dataframe.

    Args:
        chip (Chip) : the chip object that contains the schema read from.
        step (string) : step of node.
        index (string) : index of node.
        height (int or None) : The height of the dataframe. If None, streamlit
            automatically calculates it.
    '''
    streamlit.subheader(f'{step}{index} Details')
    nodes = {}
    nodes[step + index] = report.get_flowgraph_nodes(chip, step, index)
    node_reports = pandas.DataFrame.from_dict(nodes)
    streamlit.dataframe(node_reports, use_container_width=True, height=height)


def design_preview_module(chip):
    '''
    Displays the design preview.

    Args:
        chip (Chip) : the chip object that contains the schema read from.
    '''
    streamlit.header('Design Preview', anchor='design_preview')
    streamlit.image(f'{chip._getworkdir()}/{chip.design}.png')


def make_node_to_step_index_map(metric_dataframe):
    '''
    Returns a map from the name of a node to the associated step, index pair.

    Args:
        metric_dataframe (pandas.DataFrame) : A dataframe full of all metrics and all
            nodes of the selected chip
    '''
    node_to_step_index_map = {}
    for step, index in metric_dataframe.columns.tolist():
        node_to_step_index_map[step + index] = (step, index)
    # concatenate step and index
    metric_dataframe.columns = metric_dataframe.columns.map(lambda x: f'{x[0]}{x[1]}')
    return node_to_step_index_map


def make_metric_to_metric_unit_map(metric_dataframe):
    '''
    Returns a map from the name of a metric to the associated metric and unit in
    the form f'{x[0]} ({x[1]})'

    Args:
        metric_dataframe (pandas.DataFrame) : A dataframe full of all metrics and all
            nodes of the selected chip.
    '''
    metric_to_metric_unit_map = {}
    for metric, unit in metric_dataframe.index.tolist():
        if unit != '':
            metric_to_metric_unit_map[f'{metric} ({unit})'] = metric
        else:
            metric_to_metric_unit_map[metric] = metric
    # concatenate metric and unit
    metric_dataframe.index = metric_dataframe.index.map(lambda x: f'{x[0]} ({x[1]})'
                                                        if x[1] else x[0])
    return metric_to_metric_unit_map


def graphs_module(metric_dataframe):
    '''
    This displays the graph module.

    Args:
        metric_dataframe (pandas.DataFrame) : A dataframe full of all metrics and all
            nodes of the selected chip
    '''
    metrics = metric_dataframe.index.map(lambda x: metric_to_metric_unit_map[x])
    nodes = metric_dataframe.columns
    chips = []
    jobs = []
    for job in streamlit.session_state['master chip'].getkeys('history'):
        new_chip = Chip(design='')
        new_chip.schema = chip.schema.history(job)
        new_chip.set('design', chip.design)
        chips.append({'chip_object': new_chip, 'chip_name': job})
        jobs.append(job)
    job_selector_col, graph_adder_col = streamlit.columns(2, gap='large')
    with job_selector_col:
        with streamlit.expander('Select Jobs'):
            selected_jobs = select_runs(jobs)
    with graph_adder_col:
        graphs = streamlit.slider('pick the number of graphs you want', 1, 10,
                                  1, label_visibility='collapsed')
    graph_number = 1
    left_graph_col, right_graph_col = streamlit.columns(2, gap='large')
    while graph_number <= graphs:
        if graph_number % 2 == 1:
            graph_col = left_graph_col
        else:
            graph_col = right_graph_col
        with graph_col:
            metric, selected_nodes = \
                show_metric_and_node_selection_for_graph(metrics, nodes, graph_number)
            nodes = []
            for node in selected_nodes:
                step, index = node_to_step_index_map[node]
                nodes.append((step, index))
            structure_graph_data(chips, metric, selected_jobs, nodes)
            if not (graph_number == graphs or graph_number == graphs - 1):
                streamlit.divider()
        graph_number += 1


def select_tabs(chip):
    '''
    Creates all the tabs. Displays the modules for the tabs that may or may not exist
    which include the graphs tab and design preview tab. Returns the rest of the tabs.

    A
    '''
    if 'flowgraph' not in streamlit.session_state:
        streamlit.session_state['flowgraph'] = True
    tabs = ['Metrics', 'Manifest', 'File Viewer']
    if os.path.isfile(f'{chip._getworkdir()}/{chip.design}.png'):
        tabs += ["Design Preview"]
    if len(streamlit.session_state['master chip'].getkeys('history')) > 1:
        tabs += ["Graphs"]
    selected_tab = streamlit.radio('tabs', tabs, label_visibility='collapsed', horizontal=True,
                                   index=tabs.index(streamlit.session_state['selected_tab']))
    streamlit.session_state['selected_tab'] = selected_tab
    return selected_tab


def flowgraph_layout_vertical_modules(chip, node_spacing=100):
    """
    Displays the header and toggle for the flowgraph, and the flowgraph itself.
    This function shows the flowgraph. If the toggle is flipped, the flowgraph
    will disappear.

    Args:
        chip (Chip) : The chip object that contains the schema read from.
    """
    streamlit.header('Flowgraph')

    # finding the widest section of the flowgraph
    edges = report.get_flowgraph_edges(chip)
    not_exit_nodes = set()
    for node in edges.keys():
        not_exit_nodes |= edges[node]
    exit_nodes = [node for node in edges.keys() if node not in not_exit_nodes]

    def count_width_of_flowgraph(exit_nodes, levels_width=[], found=set(), level=0, edges=edges):
        for exit_node in exit_nodes:
            if exit_node in found:
                continue
            found.add(exit_node)
            if len(levels_width) == level:
                levels_width.append(1)
            else:
                levels_width[level] += 1
            levels_width = \
                count_width_of_flowgraph(edges[exit_node], levels_width, found, level + 1)
        return levels_width

    width = max(count_width_of_flowgraph(exit_nodes))

    config = Config(width='100%', height=(width - 1) * node_spacing + NODE_HEIGHT * width,
                    directed=True, physics=False, hierarchical=True, clickToUse=True,
                    nodeSpacing=node_spacing, levelSeparation=175, sortMethod='directed',
                    direction='LR')

    # tree_select_edges uses the structure that tree_select accepts to show the edges
    nodes, tree_select_edges = get_nodes_and_edges(chip, edges, report.get_flowgraph_path(chip))
    node_from_flowgraph = agraph(nodes=nodes, edges=tree_select_edges, config=config)
    return node_from_flowgraph


def header_and_select_nodes(metric_dataframe, node_from_flowgraph, header_col_width=0.15):
    """
    Displays selectbox for nodes to show in the node information panel and the
    header. Since both the flowgraph and selectbox show which node's information
    is displayed, the one clicked more recently will be displayed.

    Args:
        metric_dataframe (Pandas.DataFrame) : Contains the metrics of all
            nodes.
        node_from_flowgraph (string/None) : Contains a string of the node to
            display or None if none exists.
    """
    header_col, select_col = \
        streamlit.columns([header_col_width, 1 - header_col_width], gap='large')

    option = metric_dataframe.columns.tolist()[0]
    with select_col:
        streamlit.markdown('')  # to align with the header
        with streamlit.expander("Select Node"):
            with streamlit.form("nodes"):
                option = streamlit.selectbox('Pick a node to inspect',
                                             metric_dataframe.columns.tolist())
                params_submitted = streamlit.form_submit_button("Apply")
                if not params_submitted and node_from_flowgraph is not None:
                    option = node_from_flowgraph
                    streamlit.session_state['selected'] = []
                if params_submitted:
                    streamlit.session_state['selected'] = []
    with header_col:
        streamlit.header(option, anchor='node_information')
    return option


# setting remaining session_state
streamlit.session_state['display_file_content'] = False
streamlit.session_state['step'] = None
streamlit.session_state['index'] = None
streamlit.session_state['selected_tab'] = 'Metrics'
# TODO find more descriptive way to describe layouts
layout = 'tabs_as_radio'
layout = 'tabs_as_sections'
# gathering data
metric_dataframe = report.make_metric_dataframe(new_chip)
node_to_step_index_map = make_node_to_step_index_map(metric_dataframe)
metric_to_metric_unit_map = make_metric_to_metric_unit_map(metric_dataframe)
ui_width = streamlit_javascript.st_javascript("window.innerWidth")
manifest = report.make_manifest(new_chip)
if layout == 'tabs_as_radio':
    new_chip = show_title_and_runs()
    tab = select_tabs(new_chip)
    if tab == 'Metrics':
        node_from_flowgraph, datafram_and_node_info_col = \
            flowgraph_layout_vertical_flowgraph(new_chip, ui_width)
        with datafram_and_node_info_col:
            metrics_dataframe_module(metric_dataframe)
            streamlit.header('Node Information')
            metrics_col, records_col, logs_and_reports_col = streamlit.columns(3, gap='small')
            selected_node = select_nodes(metric_dataframe, node_from_flowgraph)
            step, index = node_to_step_index_map[selected_node]
            streamlit.session_state['step'] = step
            streamlit.session_state['index'] = index
            with metrics_col:
                node_metric_dataframe(selected_node, metric_dataframe[selected_node].dropna())
            with records_col:
                node_details_dataframe(new_chip, step, index)
            with logs_and_reports_col:
                display_file_content, selected_file = show_files(new_chip, step, index)
                streamlit.session_state['display_file_content'] = display_file_content
                if (streamlit.session_state['display_file_content'] and
                   selected_file != streamlit.session_state['selected_file ']):
                    streamlit.session_state['selected_tab'] = 'File Viewer'
                show_metrics_for_file(new_chip, step, index)
    elif tab == 'Manifest':
        manifest_module(new_chip, manifest, ui_width)
    elif tab == 'File Viewer':
        display_file_content = streamlit.session_state['display_file_content']
        step = streamlit.session_state['step']
        index = streamlit.session_state['index']
        file_viewer_module(display_file_content, new_chip, step, index)
    elif tab == 'Graphs':
        graphs_module(metric_dataframe)
    elif tab == 'Design Preview':
        design_preview_module(chip)
elif layout == 'tabs_as_sections':
    with streamlit.sidebar:
        show_title()
        show_runs()
        streamlit.markdown('[Metrics](#metrics)')
        streamlit.markdown('[Node Information](#node_information)')
        if len(streamlit.session_state['master chip'].getkeys('history')) > 1:
            streamlit.markdown('[Graphs](#graphs)')
        if os.path.isfile(f'{chip._getworkdir()}/{chip.design}.png'):
            streamlit.markdown('[Design Preview](#design_preview)')
        streamlit.markdown('[File Viewer](#file_viewer)')
        streamlit.markdown('[Manifest](#manifest)')
        node_from_flowgraph = show_flowgraph(chip)
    metrics_dataframe_module(metric_dataframe)
    selected_node = header_and_select_nodes(metric_dataframe, node_from_flowgraph)
    step, index = node_to_step_index_map[selected_node]
    display_file_content, _ = show_files(new_chip, step, index)
    show_metrics_for_file(new_chip, step, index)
    node_metric_dataframe(selected_node, metric_dataframe[selected_node].dropna())
    node_details_dataframe(new_chip, step, index)
    if len(streamlit.session_state['master chip'].getkeys('history')) > 1:
        streamlit.header('Graphs', anchor='graphs')
        graphs_module(metric_dataframe)
    if os.path.isfile(f'{chip._getworkdir()}/{chip.design}.png'):
        design_preview_module(chip)
    file_viewer_module(display_file_content, new_chip, step, index)
    manifest_module(new_chip, manifest, ui_width)

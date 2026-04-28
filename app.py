"""
app.py
数据复现 - 邻域类型聚类和AI驱动的地理人口分类的Dash Web应用程序。
"""

import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, State, DiskcacheManager
import argparse
import base64
import io
import os
import subprocess
import sys
import diskcache

from data_preprocessing import load_and_preprocess_data
from clustering import perform_clustering, get_pca_projection
from llm_naming import generate_cluster_names
from analysis import (
    descriptive_stats, correlation_analysis, simple_regression, multiple_regression,
    scatter_plot, histogram_plot, box_plot
)

# If dash-bootstrap-components is installed, use it for layout and styling.
try:
    import dash_bootstrap_components as dbc
    EXTERNAL_STYLESHEETS = [dbc.themes.BOOTSTRAP]
except ImportError:
    dbc = None
    EXTERNAL_STYLESHEETS = []

# Full FIPS mapping for 50 states + District of Columbia.
STATE_MAPPING = {
    '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas', '06': 'California',
    '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware', '11': 'District of Columbia',
    '12': 'Florida', '13': 'Georgia', '15': 'Hawaii', '16': 'Idaho', '17': 'Illinois',
    '18': 'Indiana', '19': 'Iowa', '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana',
    '23': 'Maine', '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
    '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska', '32': 'Nevada',
    '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico', '36': 'New York',
    '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio', '40': 'Oklahoma', '41': 'Oregon',
    '42': 'Pennsylvania', '44': 'Rhode Island', '45': 'South Carolina', '46': 'South Dakota',
    '47': 'Tennessee', '48': 'Texas', '49': 'Utah', '50': 'Vermont', '51': 'Virginia',
    '53': 'Washington', '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming',
    '72': 'Puerto Rico'
}

MAX_SCATTER_POINTS = 5000
FEATURES_SCALED = ['Income_scaled', 'Education_scaled', 'Employment_scaled', 'Diversity_scaled']
RAW_FEATURES = ['Income', 'Education', 'Employment', 'Diversity']

ANALYSIS_TYPES = {
    'clustering': '聚类分析',
    'descriptive': '描述性统计',
    'correlation': '相关性分析',
    'simple_regression': '简单线性回归',
    'multiple_regression': '多元线性回归',
    'scatter': '散点图',
    'histogram': '直方图',
    'boxplot': '箱线图'
}

VARIABLE_OPTIONS = [
    {'label': '收入 (Income)', 'value': 'Income'},
    {'label': '教育 (Education)', 'value': 'Education'},
    {'label': '就业 (Employment)', 'value': 'Employment'},
    {'label': '人口多样性 (Diversity)', 'value': 'Diversity'}
]

cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheManager(cache)

# Global default data will be loaded on demand
DEFAULT_STATE_OPTIONS = None
DEFAULT_DF = None

def get_default_data():
    global DEFAULT_DF, DEFAULT_STATE_OPTIONS
    if DEFAULT_DF is None:
        DEFAULT_DF, _ = load_and_preprocess_data()
        DEFAULT_STATE_OPTIONS = sorted(DEFAULT_DF['STATE'].dropna().unique().astype(str))

    return DEFAULT_DF, DEFAULT_STATE_OPTIONS

# Default state options for initial dropdown (hardcoded to avoid loading data on import)
default_states = ['01', '02', '04', '05', '06', '08', '09', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42', '44', '45', '46', '47', '48', '49', '50', '51', '53', '54', '55', '56', '72']

state_dropdown_options = [
    {'label': STATE_MAPPING.get(state, state), 'value': state}
    for state in default_states
]

default_state = state_dropdown_options[0]['value'] if state_dropdown_options else None

app = dash.Dash(
    __name__,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    title='数据复现',
    background_callback_manager=long_callback_manager
)

server = app.server

@app.callback(
    Output('upload-status', 'children'),
    Output('state-dropdown', 'options'),
    Output('state-dropdown', 'value'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_upload_status(contents, filename):
    if contents is not None:
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), low_memory=False, dtype=str)
            # Validate columns
            required_columns = [
                'GISJOIN', 'STATE', 'COUNTY', 'YEAR', 'NAME_E',
                'AQQIE001',
                'AQP5E001', 'AQP5E007', 'AQP5E008', 'AQP5E009', 'AQP5E010', 'AQP5E011', 'AQP5E012', 'AQP5E013', 'AQP5E014', 'AQP5E015', 'AQP5E016', 'AQP5E017',
                'AQQOE001', 'AQQOE003',
                'AQQKE001', 'AQQKE002'
            ]
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                return f"上传文件缺少必要列: {missing_cols}", [{'label': '无数据', 'value': ''}], ''
            # Preprocess to get states
            df_processed, _ = load_and_preprocess_data(df)
            state_options = sorted(df_processed['STATE'].dropna().unique().astype(str))
            new_options = [{'label': STATE_MAPPING.get(s, s), 'value': s} for s in state_options]
            new_value = new_options[0]['value'] if new_options else ''
            return f"成功上传文件: {filename}", new_options, new_value
        except Exception as e:
            return f"上传文件处理失败: {str(e)}", [{'label': '无数据', 'value': ''}], ''
    return '未上传文件，使用默认数据。', state_dropdown_options, default_state


def create_cluster_card(cluster_id, name, description, stats):
    card_contents = [
        html.H5(f"聚类 {cluster_id}: {name}", className='card-title'),
        html.P(description, className='card-text'),
        html.Small(
            f"收入: {stats.get('Income', 0):.0f}, 教育: {stats.get('Education', 0):.1f}%, "
            f"就业: {stats.get('Employment', 0):.1f}%, 人口多样性: {stats.get('Diversity', 0):.1f}%",
            className='text-muted'
        )
    ]

    style = {
        'backgroundColor': '#f8f9fa',
        'borderRadius': '0.75rem',
        'border': '1px solid #dcdcdc',
        'padding': '1rem',
        'marginBottom': '1rem'
    }

    if dbc:
        return dbc.Card(dbc.CardBody(card_contents), style=style)
    return html.Div(card_contents, style=style)


empty_figure = px.scatter(
    title='数据复现 - 选择州并运行分析',
)
empty_figure.update_layout(template='plotly_white')

if dbc:
    app.layout = dbc.Container([
        dbc.Row(dbc.Col(html.H1('数据复现', className='text-center mb-4'), width=12)),
        dbc.Row([
            dbc.Col([
                html.Label('上传数据文件 (CSV):'),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div(['拖拽或点击上传CSV文件']),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px 0'
                    },
                    multiple=False
                ),
                html.Div(id='upload-status', children='未上传文件，使用默认数据。')
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.Label('分析类型:'),
                dcc.Dropdown(
                    id='analysis-type',
                    options=[{'label': v, 'value': k} for k, v in ANALYSIS_TYPES.items()],
                    value='clustering',
                    clearable=False
                )
            ], width=3),
            dbc.Col([
                html.Label('选择变量:'),
                dcc.Checklist(
                    id='variable-selection',
                    options=VARIABLE_OPTIONS,
                    value=['Income', 'Education', 'Employment', 'Diversity'],
                    inline=True
                )
            ], width=6),
            dbc.Col([
                html.Label('州 (仅聚类分析):'),
                dcc.Dropdown(
                    id='state-dropdown',
                    options=state_dropdown_options,
                    value=default_state,
                    clearable=False,
                    searchable=True
                )
            ], width=3)
        ], className='align-items-end mb-4'),
        dbc.Row([
            dbc.Col([
                html.Label('聚类数量 (K，仅聚类分析):'),
                dcc.Slider(
                    id='k-slider',
                    min=2,
                    max=8,
                    step=1,
                    value=5,
                    marks={i: str(i) for i in range(2, 9)}
                )
            ], width=3),
            dbc.Col([
                html.Label('X轴变量 (回归/散点图):'),
                dcc.Dropdown(
                    id='x-var',
                    options=VARIABLE_OPTIONS,
                    value='Income'
                )
            ], width=2),
            dbc.Col([
                html.Label('Y轴变量 (回归/散点图):'),
                dcc.Dropdown(
                    id='y-var',
                    options=VARIABLE_OPTIONS,
                    value='Education'
                )
            ], width=2),
            dbc.Col([
                html.Label('颜色变量 (散点图，可选):'),
                dcc.Dropdown(
                    id='color-var',
                    options=[{'label': '无', 'value': ''}] + VARIABLE_OPTIONS,
                    value=''
                )
            ], width=2),
            dbc.Col(
                dbc.Button('运行分析', id='run-btn', color='primary', className='mt-4', style={'width': '100%'}),
                width=1
            ),
            dbc.Col(
                dcc.Loading(id='loading-indicator', type='circle', children=html.Div(id='loading-output', children='准备就绪')),
                width=2
            )
        ], className='align-items-end mb-4'),
        dbc.Row([
            dbc.Col(dcc.Graph(id='main-plot', figure=empty_figure, style={'height': '600px'}), width=8),
            dbc.Col([
                html.H4('分析结果', className='mb-3'),
                html.Div(id='analysis-results', children=html.Div('选择分析类型并点击运行分析以显示结果。'), style={'maxHeight': '600px', 'overflowY': 'auto'})
            ], width=4)
        ])
    ], fluid=True)
else:
    # Fallback layout without dbc
    app.layout = html.Div([
        html.H1('数据复现', style={'textAlign': 'center', 'marginBottom': '24px'}),
        html.Div([
            html.Label('上传数据文件 (CSV):'),
            dcc.Upload(
                id='upload-data',
                children=html.Div(['拖拽或点击上传CSV文件']),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px 0'
                },
                multiple=False
            ),
            html.Div(id='upload-status', children='未上传文件，使用默认数据。')
        ]),
        html.Div([
            html.Div([
                html.Label('分析类型:'),
                dcc.Dropdown(
                    id='analysis-type',
                    options=[{'label': v, 'value': k} for k, v in ANALYSIS_TYPES.items()],
                    value='clustering',
                    clearable=False
                )
            ], style={'flex': '1', 'marginRight': '12px'}),
            html.Div([
                html.Label('选择变量:'),
                dcc.Checklist(
                    id='variable-selection',
                    options=VARIABLE_OPTIONS,
                    value=['Income', 'Education', 'Employment', 'Diversity'],
                    inline=True
                )
            ], style={'flex': '2', 'marginRight': '12px'}),
            html.Div([
                html.Label('州 (仅聚类分析):'),
                dcc.Dropdown(
                    id='state-dropdown',
                    options=state_dropdown_options,
                    value=default_state,
                    clearable=False,
                    searchable=True
                )
            ], style={'flex': '1', 'marginRight': '12px'}),
            html.Div([
                html.Label('聚类数量 (K，仅聚类分析):'),
                dcc.Slider(
                    id='k-slider',
                    min=2,
                    max=8,
                    step=1,
                    value=5,
                    marks={i: str(i) for i in range(2, 9)}
                )
            ], style={'flex': '1', 'marginRight': '12px'}),
            html.Button('运行分析', id='run-btn', style={'padding': '12px', 'backgroundColor': '#0d6efd', 'color': 'white', 'border': 'none', 'borderRadius': '0.25rem'}),
            dcc.Loading(id='loading-indicator', type='circle', children=html.Div(id='loading-output', children='准备就绪'), style={'marginLeft': '12px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '12px', 'marginBottom': '24px'}),
        html.Div([
            html.Div(dcc.Graph(id='main-plot', figure=empty_figure, style={'height': '600px'}), style={'flex': '0 0 60%'}),
            html.Div([
                html.H4('分析结果', style={'marginBottom': '16px'}),
                html.Div(id='analysis-results', children=html.Div('选择分析类型并点击运行分析以显示结果。'), style={'maxHeight': '600px', 'overflowY': 'auto'})
            ], style={'flex': '0 0 38%', 'paddingLeft': '16px'})
        ], style={'display': 'flex', 'flexWrap': 'wrap'})
    ], style={'padding': '24px'})


@app.callback(
    output=[
        Output('main-plot', 'figure'),
        Output('analysis-results', 'children'),
        Output('loading-output', 'children')
    ],
    inputs=[Input('run-btn', 'n_clicks')],
    state=[
        State('analysis-type', 'value'),
        State('variable-selection', 'value'),
        State('state-dropdown', 'value'),
        State('k-slider', 'value'),
        State('x-var', 'value'),
        State('y-var', 'value'),
        State('color-var', 'value'),
        State('upload-data', 'contents')
    ],
    background=True,
    prevent_initial_call=True
)
def run_analysis(n_clicks, analysis_type, variables, state_value, k_value, x_var, y_var, color_var, upload_contents):
    """Run the selected analysis type."""
    try:
        if not variables:
            empty_fig = px.scatter(title='请选择至少一个变量')
            empty_fig.update_layout(template='plotly_white')
            return empty_fig, html.Div('请至少选择一个变量。'), '变量选择必需。'

        # Load data
        if upload_contents is not None:
            content_type, content_string = upload_contents.split(',')
            decoded = base64.b64decode(content_string)
            df_upload = pd.read_csv(io.StringIO(decoded.decode('utf-8')), low_memory=False, dtype=str)
            DF, _ = load_and_preprocess_data(df_upload)
        else:
            DF, _ = get_default_data()

        # Filter data based on analysis type
        if analysis_type == 'clustering':
            if not state_value:
                empty_fig = px.scatter(title='请选择州进行聚类分析')
                empty_fig.update_layout(template='plotly_white')
                return empty_fig, html.Div('请选择州。'), '州选择必需。'
            df_analysis = DF[DF['STATE'] == state_value].copy()
        else:
            df_analysis = DF.copy()

        # Perform analysis
        if analysis_type == 'clustering':
            scaled_data = df_analysis[FEATURES_SCALED].to_numpy()
            df_clustered, _, stats_dict = perform_clustering(df_analysis, scaled_data, n_clusters=k_value)
            pca_df = get_pca_projection(scaled_data)
            df_clustered = pd.concat([df_clustered.reset_index(drop=True), pca_df], axis=1)

            display_df = df_clustered
            if len(display_df) > MAX_SCATTER_POINTS:
                display_df = display_df.sample(n=MAX_SCATTER_POINTS, random_state=42)

            fig = px.scatter(
                display_df,
                x='PC1',
                y='PC2',
                color='Cluster',
                title='邻域聚类的二维PCA投影',
                hover_data={'GISJOIN': True, 'Income': ':.0f', 'Education': ':.1f', 'Employment': ':.1f', 'Diversity': ':.1f'}
            )
            fig.update_layout(template='plotly_white', legend_title_text='聚类')

            cluster_names = generate_cluster_names(stats_dict)
            cards = []
            for cluster_id in sorted(cluster_names.keys()):
                info = cluster_names[cluster_id]
                stats = stats_dict.get(cluster_id, {})
                cards.append(create_cluster_card(cluster_id, info['name'], info['description'], stats))

            state_label = STATE_MAPPING.get(state_value, state_value)
            return fig, cards, f'为{state_label}完成聚类分析，K={k_value}。'

        elif analysis_type == 'descriptive':
            stats = descriptive_stats(df_analysis, variables)
            fig = px.scatter(title='描述性统计')  # Placeholder
            fig.update_layout(template='plotly_white')
            if dbc:
                table = dbc.Table.from_dataframe(stats.reset_index(), striped=True, bordered=True, hover=True)
            else:
                table = html.Pre(stats.to_string())
            return fig, table, '描述性统计完成。'

        elif analysis_type == 'correlation':
            fig = correlation_analysis(df_analysis, variables)
            return fig, html.Div('相关性分析完成。'), '相关性分析完成。'

        elif analysis_type == 'simple_regression':
            if x_var not in variables or y_var not in variables:
                empty_fig = px.scatter(title='X和Y变量必须在选择的变量中')
                empty_fig.update_layout(template='plotly_white')
                return empty_fig, html.Div('X和Y变量必须在选择的变量中。'), '变量错误。'
            fig, stats = simple_regression(df_analysis, x_var, y_var)
            results_div = html.Div([
                html.P(f"斜率: {stats['slope']:.2f}"),
                html.P(f"截距: {stats['intercept']:.2f}"),
                html.P(f"R²: {stats['r2']:.2f}")
            ])
            return fig, results_div, '简单回归分析完成。'

        elif analysis_type == 'multiple_regression':
            if len(variables) < 2:
                empty_fig = px.scatter(title='多元回归需要至少两个变量')
                empty_fig.update_layout(template='plotly_white')
                return empty_fig, html.Div('多元回归需要至少两个变量。'), '变量不足。'
            x_vars = [v for v in variables if v != y_var]
            if not x_vars:
                empty_fig = px.scatter(title='没有足够的自变量')
                empty_fig.update_layout(template='plotly_white')
                return empty_fig, html.Div('没有足够的自变量。'), '变量错误。'
            summary = multiple_regression(df_analysis, x_vars, y_var)
            fig = px.scatter(title='多元回归')  # Placeholder
            fig.update_layout(template='plotly_white')
            return fig, html.Pre(summary), '多元回归分析完成。'

        elif analysis_type == 'scatter':
            if x_var not in variables or y_var not in variables:
                empty_fig = px.scatter(title='X和Y变量必须在选择的变量中')
                empty_fig.update_layout(template='plotly_white')
                return empty_fig, html.Div('X和Y变量必须在选择的变量中。'), '变量错误。'
            color = color_var if color_var and color_var in variables else None
            fig = scatter_plot(df_analysis, x_var, y_var, color)
            return fig, html.Div('散点图完成。'), '散点图完成。'

        elif analysis_type == 'histogram':
            if not variables:
                empty_fig = px.scatter(title='请选择变量')
                empty_fig.update_layout(template='plotly_white')
                return empty_fig, html.Div('请选择变量。'), '变量选择必需。'
            fig = histogram_plot(df_analysis, variables[0])
            return fig, html.Div('直方图完成。'), '直方图完成。'

        elif analysis_type == 'boxplot':
            if not variables:
                empty_fig = px.scatter(title='请选择变量')
                empty_fig.update_layout(template='plotly_white')
                return empty_fig, html.Div('请选择变量。'), '变量选择必需。'
            fig = box_plot(df_analysis, variables[0])
            return fig, html.Div('箱线图完成。'), '箱线图完成。'

        else:
            empty_fig = px.scatter(title='未知分析类型')
            empty_fig.update_layout(template='plotly_white')
            return empty_fig, html.Div('未知分析类型。'), '错误。'

    except Exception as e:
        empty_fig = px.scatter(title='分析失败')
        empty_fig.update_layout(template='plotly_white')
        return empty_fig, html.Div(f'分析过程中出错: {str(e)}'), f'错误: {str(e)}'


def start_detached_server(host: str, port: int) -> None:
    command = [sys.executable, os.path.abspath(__file__), '--serve', '--host', host, '--port', str(port)]
    creationflags = 0
    if sys.platform.startswith('win'):
        creationflags = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0) | getattr(subprocess, 'DETACHED_PROCESS', 0)

    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creationflags
    )
    print(f'后台启动 Dash 服务器: http://{host}:{port}/')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='启动 Dash Web 应用')
    parser.add_argument('--serve', action='store_true', help='直接运行 Dash 服务器')
    parser.add_argument('--detach', action='store_true', help='后台模式启动 Dash 服务器并立即退出当前进程')
    parser.add_argument('--host', default='127.0.0.1', help='服务器监听地址，默认 127.0.0.1')
    parser.add_argument('--port', default=8050, type=int, help='服务器端口，默认 8050')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.detach:
        start_detached_server(args.host, args.port)
        sys.exit(0)

    app.run(debug=False, host=args.host, port=args.port)

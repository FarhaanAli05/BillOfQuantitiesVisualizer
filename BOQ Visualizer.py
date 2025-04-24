from dash import Dash, dcc, html, Input, Output, State, callback_context
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import base64
import io
import math

# Create the Dash application
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# Global variable to store color mapping
global_color_map = {}

# Define the layout
app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(html.H1("BOQ Visualizer", className="text-center my-4"), width=12)
    ),
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                },
                multiple=True
            ),
            dcc.Dropdown(id='file-dropdown', placeholder="Select File", style={'margin': '10px'}),
            dcc.Dropdown(id='value-dropdown', placeholder="Select Value", style={'margin': '10px'}),
            dcc.Dropdown(id='color-dropdown', placeholder="Select Category", style={'margin': '10px'}),
            dcc.Input(id='search-input', type='text', placeholder='Search keyword', style={'margin': '10px', 'width': '100%'}),
            dcc.RadioItems(
                id='sort-radio',
                options=[
                    {'label': 'Chronological', 'value': 'chronological'},
                    {'label': 'Ascending', 'value': 'ascending'},
                    {'label': 'Descending', 'value': 'descending'}
                ],
                value='chronological',
                inline=True,
                style={'margin': '10px'}
            ),
            dcc.Dropdown(
                id='bars-per-page-dropdown',
                options=[
                    {'label': '5 bars', 'value': 5},
                    {'label': '7 bars', 'value': 7},
                    {'label': '15 bars', 'value': 15},
                    {'label': '30 bars', 'value': 30},
                    {'label': '50 bars', 'value': 50},
                ],
                value=7,
                placeholder="Bars per page",
                style={'margin': '10px'}
            ),
            dcc.Slider(
                id='page-slider',
                min=1,
                max=1,
                step=1,
                value=1,
                marks={},
                updatemode='drag',
                tooltip={'always_visible': True, 'placement': 'bottom'},
            ),
            html.Div(id='slider-label', style={'text-align': 'center', 'margin-top': '10px'}),
            dbc.Spinner(html.Div(id="loading-output"), color="primary", size="md", type="border"),
        ], width=3),
        dbc.Col([
            dcc.Graph(id='main-chart', style={'height': '600px', 'width': '100%'}),
            dcc.Graph(id='detail-chart', style={'height': '500px', 'width': '100%'}),
            html.Div(id='selected-description', style={'display': 'none'})
        ], width=7)
    ]),
], fluid=True)

# Helper function to parse uploaded files
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded), sheet_name='Database BOQ')  # Only reads the sheet with "Database BOQ" as name
            return df
        else:
            return None
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return None

# Helper function to get numerical columns of spreadsheet
def get_numerical_columns(df):
    num_columns = []
    for col in df.columns[4:]:  # Skip first four columns
        if df[col].dtype in ['int64', 'float64'] and df[col].apply(lambda x: isinstance(x, (int, float))).all():
            num_columns.append(col)
        elif df[col].dtype == 'object' and df[col].str.contains('%').any():
            df[col] = df[col].str.rstrip('%').astype('float') / 100.0
            num_columns.append(col)
    return num_columns

# Helper function to get non-numeric columns
def get_non_numeric_columns(df):
    return [col for col in df.columns[4:] if col not in get_numerical_columns(df) and col != 'Description']

# Helper function to get colour mapping
def get_colour_mapping(df, color_category):
    global global_color_map
    if color_category:
        unique_categories = sorted(df[color_category].unique())
        if color_category not in global_color_map:
            color_discrete_map = px.colors.qualitative.Plotly[:len(unique_categories)]
            global_color_map[color_category] = dict(zip(unique_categories, color_discrete_map))
        return global_color_map[color_category]
    return {}

# Callback to update dropdowns based on uploaded files and trigger loading spinner
@app.callback(
    [Output('file-dropdown', 'options'),
     Output('file-dropdown', 'value'),
     Output('value-dropdown', 'options'),
     Output('value-dropdown', 'value'),
     Output('color-dropdown', 'options'),
     Output('loading-output', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_dropdowns(contents, filenames):
    if contents is None:
        return [], None, [], None, [], ""

    options = [{'label': filename, 'value': filename} for filename in filenames]
    first_df = parse_contents(contents[0], filenames[0])
    if first_df is None:
        return [], None, [], None, [], ""

    num_columns = get_numerical_columns(first_df)
    value_options = [{'label': col, 'value': col} for col in num_columns]

    non_numeric_columns = get_non_numeric_columns(first_df)
    color_options = [{'label': col, 'value': col} for col in non_numeric_columns]

    return options, options[0]['value'], value_options, value_options[0]['value'] if value_options else None, color_options, ""

# Callback to reset page slider when search term changes and trigger loading spinner
@app.callback(
    [Output('page-slider', 'value'),
     Output('loading-output', 'children', allow_duplicate=True)],
    [Input('search-input', 'value')],
    prevent_initial_call=True
)
def reset_page_slider(search_term):
    return 1, ""

# Callback to update the main chart based on the selected file, value, and search term
@app.callback(
    [Output('main-chart', 'figure'),
     Output('page-slider', 'max'),
     Output('page-slider', 'marks'),
     Output('slider-label', 'children'),
     Output('loading-output', 'children', allow_duplicate=True)],
    [Input('file-dropdown', 'value'),
     Input('value-dropdown', 'value'),
     Input('color-dropdown', 'value'),
     Input('page-slider', 'value'),
     Input('bars-per-page-dropdown', 'value'),
     Input('search-input', 'value'),
     Input('sort-radio', 'value')],
    [State('upload-data', 'contents'),
     State('upload-data', 'filename')],
    prevent_initial_call=True
)
def update_main_chart(selected_file, selected_value, color_category, page, bars_per_page, search_term, sort_order, contents, filenames):
    if contents is None or selected_value is None or selected_file is None:
        return {}, 1, {1: '1'}, '1', ""

    selected_index = filenames.index(selected_file)
    df = parse_contents(contents[selected_index], selected_file)
    if df is None:
        return {}, 1, {1: '1'}, '1', ""

    columns_to_include = ['Description', selected_value]
    if color_category:
        columns_to_include.append(color_category)

    df = df[columns_to_include].dropna()
    df = df[df[selected_value].apply(lambda x: isinstance(x, (int, float)))]

    # Get colour mapping before filtering
    color_discrete_map = get_colour_mapping(df, color_category)

    if search_term:
        df = df[df['Description'].str.contains(search_term, case=False, na=False)]

    # Sort the dataframe based on the sort_order
    if sort_order == 'ascending':
        df = df.sort_values(by=selected_value, ascending=True)
    elif sort_order == 'descending':
        df = df.sort_values(by=selected_value, ascending=False)
    # For 'chronological', we don't change the order

    num_pages = math.ceil(len(df) / bars_per_page)
    marks = {i: '' for i in range(1, num_pages + 1)}

    start_idx = (page - 1) * bars_per_page
    end_idx = start_idx + bars_per_page

    df_page = df.iloc[start_idx:end_idx].copy()
    df_page['Full Description'] = df_page['Description']
    df_page['Truncated Description'] = df_page['Description'].apply(lambda x: f"{x[:15]}..." if len(x) > 15 else x)
    df_page['Display Description'] = df_page.apply(lambda x: f"{x.name + 1}. {x['Truncated Description']}", axis=1)

    is_percentage = '%' in df[selected_value].astype(str).iloc[0]
    if is_percentage:
        df_page[selected_value] = df_page[selected_value] * 100

    if color_category:
        fig = px.bar(df_page, x='Display Description', y=selected_value, text=selected_value, color=color_category,
                     title=f'{selected_value} of {selected_file} ({bars_per_page} Bars)',
                     labels={selected_value: f'{selected_value} (%)' if is_percentage else selected_value},
                     hover_data=['Full Description'],
                     color_discrete_map=color_discrete_map,
                     category_orders={color_category: sorted(df_page[color_category].unique())})
    else:
        fig = px.bar(df_page, x='Display Description', y=selected_value, text=selected_value,
                     title=f'{selected_value} of {selected_file} ({bars_per_page} Bars)',
                     labels={selected_value: f'{selected_value} (%)' if is_percentage else selected_value},
                     hover_data=['Full Description'])

    fig.update_traces(textposition='outside')
    
    # Ensure the x-axis order matches the sorted dataframe
    fig.update_xaxes(categoryorder='array', categoryarray=df_page['Display Description'])

    return fig, num_pages, marks, str(page), ""

# Callback to update the detailed chart based on the selected bar and trigger loading spinner
@app.callback(
    [Output('detail-chart', 'figure'),
     Output('loading-output', 'children', allow_duplicate=True)],
    [Input('main-chart', 'clickData'),
     Input('color-dropdown', 'value')],
    [State('value-dropdown', 'value'),
     State('upload-data', 'contents'),
     State('upload-data', 'filename')],
    prevent_initial_call=True
)
def update_detail_chart(clickData, color_category, selected_value, contents, filenames):
    if clickData is None or contents is None or selected_value is None:
        return {}, ""

    full_description = clickData['points'][0]['customdata'][0]

    combined_df = []
    for content, filename in zip(contents, filenames):
        df = parse_contents(content, filename)
        if df is not None and 'Description' in df.columns:
            df = df.dropna(subset=['Description'])
            df['Source'] = filename
            combined_df.append(df)

    if not combined_df:
        return {}, ""

    combined_df = pd.concat(combined_df)

    # Get colour mapping from the entire dataset
    color_discrete_map = get_colour_mapping(combined_df, color_category)

    filtered_df = combined_df[combined_df['Description'] == full_description]

    if filtered_df.empty:
        return {}, ""

    is_percentage = '%' in filtered_df[selected_value].astype(str).iloc[0]
    if is_percentage:
        filtered_df[selected_value] = filtered_df[selected_value] * 100

    if color_category:
        fig = px.bar(filtered_df, x='Source', y=selected_value, text=selected_value, color=color_category,
                     title=f'{selected_value} for {full_description}',
                     labels={selected_value: f'{selected_value} (%)' if is_percentage else selected_value},
                     color_discrete_map=color_discrete_map)
    else:
        fig = px.bar(filtered_df, x='Source', y=selected_value, text=selected_value,
                     title=f'{selected_value} for {full_description}',
                     labels={selected_value: f'{selected_value} (%)' if is_percentage else selected_value})

    fig.update_traces(textposition='outside')

    return fig, ""

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

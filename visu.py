from flask import Flask
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

app = Flask(__name__)
dash_app = dash.Dash(__name__, server=app)

# Sample DataFrame
data = {
    'coverage and premium': ["Total coverage: $5 million\nTotal Annual Premium: $765.00"] * 20,
    'Insurance Type': ['Home'] * 20,
    'Category': ['Dwelling Building Coverage', 'Dwelling Building Coverage', 'Dwelling Building Coverage', 'Dwelling Building Coverage', 'Dwelling Building Coverage', 'Personal Property Coverage', 'Personal Property Coverage', 'Personal Property Coverage', 'Personal Property Coverage', 'Personal Property Coverage', 'Living Expenses and Rental Value', 'Living Expenses and Rental Value', 'Living Expenses and Rental Value', 'Living Expenses and Rental Value', 'Living Expenses and Rental Value', 'Liability Coverage', 'Liability Coverage', 'Voluntary Medical Coverage', 'Voluntary Payment for Damage Property', 'Voluntary Compensation for Residence Employees'],
    'What_covered': ['Primary Dwelling', 'Primary Dwelling', 'Primary Dwelling', 'Primary Dwelling', 'Primary Dwelling', 'Your Belongings', 'Your Belongings', 'Your Belongings', 'Your Belongings', 'Your Belongings', 'Temporary Housing Expenses', 'Living Expenses Reimbursement', 'Fair Rental Value', 'Premises Liability', 'Premises Liability', 'Reimbursement for Injury', 'Reimbursement for Injury', 'Reimbursement for Accidents', 'Property Damage to Others', 'Indemnity for Residence Employees Injury'],
    'Percentage Covered': [100 for _ in range(20)]
}

# Manually provided details for the information window
total_coverage = "$5 million"
premium = "$765.00"

# Constructing the hover text content
info_text = f"""
<b>Insurer:</b> TD Insurance<br>
<b>Benefit Amount:</b> {total_coverage}<br>
<b>Insured Name:</b> AMIN NANJI AND ASHIFA NANJI<br>
<b>Policy Number:</b> 00117251217<br>
<b>Renewal Date:</b> March 10, 2023<br>
<b>Premium:</b> {premium}<br>
"""

# Insurance types for dropdown menu
insurance_types = list(set(data['Insurance Type']))

# Define layout
dash_app.layout = html.Div([
    dcc.Tabs(
        id="tabs",
        value="insurance-visualization",
        children=[
            # Insurance visualization tab
            dcc.Tab(
                label="Insurance Visualization",
                value="insurance-visualization",
                children=[
                    dcc.Dropdown(
                        id='insurance-type-filter',
                        options=[{'label': i, 'value': i} for i in insurance_types],
                        value=None
                    ),
                    dcc.Graph(id='insurance-chart'),
                    html.Div(id='details', style={'margin-top': '20px', 'font-size': '18px', 'white-space': 'pre-line'}),
                ]
            ),
            # Additional pages for insights, settings, etc.
            # ...
        ]
    )
])

# Callback to update figure based on click and selection
@dash_app.callback(
    Output('insurance-chart', 'figure'),
    [Input('insurance-chart', 'clickData'), Input('insurance-chart', 'selectedData'), Input('insurance-type-filter', 'value')]
)
def update_figure(click_data, selected_data, insurance_type):
    if click_data:
        # Drill down to clicked category
        labels = click_data['points'][0]['labels']
        filtered_data = data[data['Category'] == labels[2]]
        fig = px.sunburst(filtered_data, path=['coverage and premium', 'Insurance Type', 'Category', 'What_covered'], labels='What_covered', color_continuous_scale=["#8BC34A", "#FF6F00"])
    elif selected_data:
        # Filter by selected data
        selected_labels = [point['label'] for point in selected_data['points']]
        filtered_data = data[data['What_covered'].isin(selected_labels)]
        fig = px.sunburst(filtered_data, path=['coverage and premium', 'Insurance Type', 'Category', 'What_covered'], labels='What_covered', color_continuous_scale=["#8BC34A", "#FF6F00"])
    elif insurance_type:
        # Filter by insurance type
        filtered_data = data[data['Insurance Type'] == insurance_type]
        fig = px.sunburst(filtered_data, path=['coverage and premium', 'Insurance Type', 'Category', 'What_covered'], labels='What_covered', color_continuous_scale=["#8BC34A", "#FF6F00"])
    else:
        # Display original Sunburst chart
        fig = px.sunburst(data, path=['coverage and premium', 'Insurance Type', 'Category', 'What_covered'], labels='What_covered', color_continuous_scale=["#8BC34A", "#FF6F00"])
    fig.update_traces(
        hoverinfo="label+text",  # Display label and text on hover
        hovertext=hovertext + "{:.2f}% Covered".format(data[data['What_covered'] == click_data['points'][0]['label']]['Percentage Covered'].values[0])
    )
    return fig
hovertext = info_text
# Callback to update details section
@dash_app.callback(
    Output('details', 'children'),
    Input('insurance-chart', 'clickData')
)
def update_details(click_data):
    if click_data is None:
        return 'Click on a part of the chart to see details.'
    labels = click_data['points'][0]['labels']
    details_text = f"Insurance Type: {labels[1]}\nCategory: {labels[2]}\nCoverage Name: {labels[3]}"
    return details_text

# Configure Heroku deployment (optional)
#if 'DYNO' in os.environ:
    # Running on Heroku
   # app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
#else:
    # Running locally
    #app.run(debug=True)

if __name__ == "__main__":
    # Running locally
    app.run(debug=True)

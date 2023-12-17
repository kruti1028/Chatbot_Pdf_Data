from flask import Flask, render_template
import sqlite3
import plotly.graph_objects as go
import matplotlib.pyplot as plt

app = Flask(__name__)

def generate_sunburst_chart_from_db(db_path):
    # Generate a color palette
    color_palette = plt.cm.tab20.colors  # Using Matplotlib's tab20 colormap
    color_index = 0

    # Function to get the next color from the palette
    def get_next_color():
        nonlocal color_index
        color = color_palette[color_index % len(color_palette)]
        color_index += 1
        return f'rgb({color[0]*255}, {color[1]*255}, {color[2]*255})'

    # Map to store colors for each type of insurance
    type_color_map = {}

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to join insurance_policies and categories tables
    query = '''
    SELECT p.id, p.total_coverage_amount, p.type_of_insurance, p.annual_premium, p.insurer, 
           p.insured, p.issue_date, p.renewal_date, p.policy_number, 
           c.category_name, c.covered, c.not_covered
    FROM insurance_policies p
    LEFT JOIN categories c ON p.id = c.policy_id
    '''
    cursor.execute(query)
    rows = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Organize the data for the sunburst chart
    labels, parents, values, hovertext, colors = [], [], [], [], []
    for row in rows:
        # Extract data from each row
        policy_id, total_coverage_amount, type_of_insurance, annual_premium, insurer, insured, issue_date, renewal_date, policy_number, category_name, covered, not_covered = row

        # Add data to labels, parents, values, hovertext, and colors
        # Root label for each policy
        root_label = f"Policy {policy_id}: {total_coverage_amount}"
        if root_label not in labels:
            labels.append(root_label)
            parents.append('')
            values.append(100)  # Static value or calculated
            hovertext.append(f"Insurer: {insurer}<br>Insured: {insured}<br>Total Coverage Amount: {total_coverage_amount}<br>Annual Premium: {annual_premium}<br>Renewal Date: {renewal_date}<br>Issue Date: {issue_date}")
            colors.append("lightgray")  # Default color for root

        # Insurance type
        if type_of_insurance and type_of_insurance not in labels:
            labels.append(type_of_insurance)
            parents.append(root_label)
            values.append(20)  # Static value or calculated
            hovertext.append(f"Type of Insurance: {type_of_insurance}")
            # Assign a color from the palette
            if type_of_insurance not in type_color_map:
                type_color_map[type_of_insurance] = get_next_color()
            colors.append(type_color_map[type_of_insurance])

        # Categories
        if category_name and category_name not in labels:
            labels.append(category_name)
            parents.append(type_of_insurance)
            values.append(10)  # Static value or calculated
            hovertext.append(f"Category: {category_name}")
            colors.append("lightblue")  # Color for categories

        # Covered and Not Covered Items
        for item in covered.split(','):
            labels.append(f"Covered: {item}")
            parents.append(category_name)
            values.append(5)  # Static value or calculated
            hovertext.append(f"Covered Item: {item}")
            colors.append("lightgreen")  # Color for covered items

        for item in not_covered.split(','):
            labels.append(f"Not Covered: {item}")
            parents.append(category_name)
            values.append(5)  # Static value or calculated
            hovertext.append(f"Not Covered Item: {item}")
            colors.append("pink")  # Color for not covered items

    # Create and configure the sunburst chart
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        hoverinfo="text",
        hovertext=hovertext,
        branchvalues="total",
        marker=dict(colors=colors)  # Apply the colors
    ))
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    # Convert chart to HTML
    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn', default_height=600, default_width=800)
    return chart_html

if __name__ == '__main__':
    app.run(debug=True)

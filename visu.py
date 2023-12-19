import sqlite3
import plotly.graph_objects as go
import plotly.express as px

def fetch_data_from_db(db_path, query):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

def generate_hovertext_for_root(data):
    if not data:
        return "No Data Available"
    row = data[0]
    total_coverage_amount, annual_premium, insurer, insured, issue_date, renewal_date, policy_number = row[1], row[3], row[4], row[5], row[6], row[7], row[8]
    hovertext = f"Total Coverage Amount: {total_coverage_amount}<br>" \
                f"Annual Premium: {annual_premium}<br>" \
                f"Insurer: {insurer}<br>" \
                f"Insured: {insured}<br>" \
                f"Issue Date: {issue_date}<br>" \
                f"Renewal Date: {renewal_date}<br>" \
                f"Policy Number: {policy_number}"
    return hovertext

def generate_sunburst_chart_from_db(data):
    # Define custom colors for insurance types and other elements
    custom_colors = {
        "Total Coverage": "#FFFFFF",
        "Life Insurance": "#1f77b4",  # Blue
        "Health Insurance": "#ff7f0e",  # Orange
        "Auto Insurance": "#2ca02c",  # Green
    }

    total_coverage_amount = data[0][1] if data else "Not specified"
    root_hovertext = generate_hovertext_for_root(data)
    
    labels, parents, values, hovertext, colors = ['Total Coverage: ' + total_coverage_amount], [''], [0], [root_hovertext], [custom_colors.get("Total Coverage", "lightgray")]

    for row in data:
        _, _, type_of_insurance, _, _, _, _, _, _, category_name, covered, not_covered = row

        type_label = type_of_insurance + " Insurance"
        if type_label not in labels:
            labels.append(type_label)
            parents.append('Total Coverage: ' + total_coverage_amount)
            values.append(0)
            hovertext.append(type_label)
            colors.append(custom_colors.get(type_label, "#d62728"))  # Default color if not specified

        category_label = f"{type_label}: {category_name}"
        if category_label not in labels:
            labels.append(category_label)
            parents.append(type_label)
            values.append(0)
            hovertext.append(category_label)
            colors.append(custom_colors.get("Category", "lightblue"))  # Default category color

        for item in (covered + ',' + not_covered).split(','):
            if item.strip():
                item_label = f"{category_label}: {'Covered' if item in covered else 'Not Covered'} - {item.strip()}"
                labels.append(item_label)
                parents.append(category_label)
                values.append(1)
                hovertext.append(item_label)
                colors.append(custom_colors.get("Covered" if 'Covered' in item_label else "Not Covered", "lightgreen" if 'Covered' in item_label else "pink"))

    # Update values for types and categories
    for i in range(len(labels)-1, 0, -1):  # Reverse order to accumulate values
        parent_index = labels.index(parents[i])
        values[parent_index] += values[i]

    # Create the sunburst chart
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        hoverinfo="text",
        hovertext=hovertext,
        branchvalues="total",
        marker=dict(colors=colors),
        insidetextorientation='radial'
    ))
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    return fig

# Define database path and query
db_path = 'your_path_insurance_data.db'
query = '''
    SELECT p.id, p.total_coverage_amount, p.type_of_insurance, p.annual_premium, p.insurer, 
           p.insured, p.issue_date, p.renewal_date, p.policy_number, 
           c.category_name, c.covered, c.not_covered
    FROM insurance_policies p
    LEFT JOIN categories c ON p.id = c.policy_id
    '''

# Fetch data from the database
db_data = fetch_data_from_db(db_path, query)

# Generate the chart using the fetched data
fig = generate_sunburst_chart_from_db(db_data)
fig.show()



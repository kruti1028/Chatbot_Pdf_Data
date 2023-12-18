import plotly.graph_objects as go

class PolicyInfo:
    def __init__(self):
        self.total_coverage_amount = "100,000"
        self.insurer = "Acme Insurance"
        self.insured = ["John Doe", "Jane Doe"]
        self.annual_premium = "10,000"
        self.renewal_date = "2024-01-01"
        self.issue_date = "2023-01-01"
        self.insurance_types = ["Life", "Health", "Auto"]
        self.categories = {
            "Life": {
                "Term Life": {
                    "covered": ["Death Benefit"], 
                    "not_covered": ["Accidental Death"]
                }
            },
            "Health": {
                "General": {
                    "covered": ["Hospitalization", "Surgery"], 
                    "not_covered": ["Cosmetic Surgery"]
                },
                "Service": {
                    "covered": ["Nurse service"], 
                    "not_covered": ["N/A", 'Service','Home ']
                },
                "Medicine": {
                    "covered": ["Medication", "Rehabilitation"], 
                    "not_covered": ["N/A"]
                }
            },
            "Auto": {
                "Comprehensive": {
                    "covered": ["Collision", "Theft"], 
                    "not_covered": ["Wear and Tear"]
                }
            }
        }

def generate_sunburst_chart(policy_info):
    labels, parents, values, hovertext = [], [], [], []

    # Add the root node
    root_label = f"Total Coverage: {policy_info.total_coverage_amount or 'Not specified'}"
    labels.append(root_label)
    parents.append("")
    values.append(0)  # Start with a base value of 0, will update later
    hovertext.append(f"Insurer: {policy_info.insurer or 'Not specified'}<br>"
                     f"Insured: {', '.join(policy_info.insured) or 'Not specified'}<br>"
                     f"Total Coverage Amount: {policy_info.total_coverage_amount or 'Not specified'}<br>"
                     f"Annual Premium: {policy_info.annual_premium or 'Not specified'}<br>"
                     f"Renewal Date: {policy_info.renewal_date or 'Not specified'}<br>"
                     f"Issue Date: {policy_info.issue_date or 'Not specified'}")

    # Add nodes for insurance types and categories
    for insurance_type in policy_info.insurance_types:
        type_label = insurance_type
        labels.append(type_label)
        parents.append(root_label)
        values.append(0)  # Start with a base value of 0, will update later
        hovertext.append(f"Type of Insurance: {insurance_type}")

        for category, details in policy_info.categories.get(insurance_type, {}).items():
            category_label = f"{type_label}: {category}"
            labels.append(category_label)
            parents.append(type_label)
            values.append(0)  # Start with a base value of 0, will update later
            hovertext.append(f"Category: {category}")

            # Add covered items
            for item in details.get('covered', []):
                item_label = f"Covered: {item}"
                labels.append(item_label)
                parents.append(category_label)
                values.append(1)  # Assign a value of 1 for simplicity
                hovertext.append(f"Covered Item: {item}")

            # Add not covered items
            for item in details.get('not_covered', []):
                item_label = f"Not Covered: {item}"
                labels.append(item_label)
                parents.append(category_label)
                values.append(1)  # Assign a value of 1 for simplicity
                hovertext.append(f"Not Covered Item: {item}")

    # Update the values to ensure each parent node's value is the sum of its children
    for i in range(len(labels) - 1, -1, -1):  # Start from the last item towards the first
        parent_index = labels.index(parents[i]) if parents[i] else -1
        if parent_index != -1:
            values[parent_index] += values[i]

    # Create the sunburst chart
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        hoverinfo="text",
        hovertext=hovertext,
        branchvalues="total"
    ))
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    return fig

policy_info = PolicyInfo()
fig = generate_sunburst_chart(policy_info)
fig.show()

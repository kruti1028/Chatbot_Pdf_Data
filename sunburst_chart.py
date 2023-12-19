import sqlite3

# Define the database name
db_path = '/Users/sanketdhameliya/Documents/visulization/insurance_data.db'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS insurance_policies (
    id INTEGER PRIMARY KEY,
    total_coverage_amount TEXT,
    type_of_insurance TEXT,
    annual_premium TEXT,
    insurer TEXT,
    insured TEXT,
    issue_date TEXT,
    renewal_date TEXT,
    policy_number TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    policy_id INTEGER,
    category_name TEXT,
    covered TEXT,
    not_covered TEXT,
    FOREIGN KEY(policy_id) REFERENCES insurance_policies(id)
)
''')

# Insert data into insurance_policies table
policies_data = [
    (1, "100,000", "Life", "10,000", "Acme Insurance", "John Doe, Jane Doe", "2023-01-01", "2024-01-01", "LIFE123"),
    (2, "100,000", "Health", "10,000", "Acme Insurance", "John Doe, Jane Doe", "2023-01-01", "2024-01-01", "HEALTH456"),
    (3, "100,000", "Auto", "10,000", "Acme Insurance", "John Doe, Jane Doe", "2023-01-01", "2024-01-01", "AUTO789")
]

cursor.executemany('''
INSERT INTO insurance_policies (id, total_coverage_amount, type_of_insurance, annual_premium, insurer, insured, issue_date, renewal_date, policy_number)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', policies_data)

# Insert data into categories table
categories_data = [
    (1, 1, "Term Life", "Death Benefit", "Accidental Death"),
    (2, 2, "General", "Hospitalization, Surgery", "Cosmetic Surgery"),
    (3, 2, "Service", "Nurse service", "N/A, Service, Home"),
    (4, 2, "Medicine", "Medication, Rehabilitation", "N/A"),
    (5, 3, "Comprehensive", "Collision, Theft", "Wear and Tear")
]

cursor.executemany('''
INSERT INTO categories (id, policy_id, category_name, covered, not_covered)
VALUES (?, ?, ?, ?, ?)
''', categories_data)

# Commit changes and close the connection
conn.commit()
conn.close()

# Return the path to the database file
db_path

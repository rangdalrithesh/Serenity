"""
Database Setup and Integration Script
======================================
Creates SQLite database and loads student mental health data
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path

# Read the SQL schema
schema_file = '/home/claude/students_mh_database_schema.sql'
csv_file = '/mnt/user-data/uploads/students_mental_health_survey.csv'
db_file = '/home/claude/students_mental_health.db'

print("="*70)
print("DATABASE SETUP AND DATA LOADING")
print("="*70)

# Create database and execute schema
print("\n1. Creating database schema...")
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

with open(schema_file, 'r') as f:
    schema_sql = f.read()
    # Execute each statement
    for statement in schema_sql.split(';'):
        if statement.strip():
            try:
                cursor.execute(statement)
            except Exception as e:
                if 'already exists' not in str(e):
                    print(f"Warning: {e}")

conn.commit()
print("✓ Database schema created")

# Load CSV data
print("\n2. Loading student data from CSV...")
df = pd.read_csv(csv_file)
print(f"   Loaded {len(df)} records")

# Create composite mental health score
print("\n3. Computing composite mental health scores...")
df['Mental_Health_Risk'] = (
    0.30 * (df['Stress_Level'] / 5.0) +
    0.40 * (df['Depression_Score'] / 5.0) +
    0.30 * (df['Anxiety_Score'] / 5.0)
).clip(0, 1)
print("✓ Composite scores computed")

# Insert data
print("\n4. Inserting data into database...")
count = 0
for idx, row in df.iterrows():
    # Insert student
    cursor.execute("""
        INSERT INTO students (
            age, course, gender, cgpa, semester_credit_load, residence_type
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        int(row['Age']),
        row['Course'],
        row['Gender'],
        float(row['CGPA']) if pd.notna(row['CGPA']) else None,
        int(row['Semester_Credit_Load']),
        row['Residence_Type']
    ))
    
    student_id = cursor.lastrowid
    
    # Insert mental health assessment
    cursor.execute("""
        INSERT INTO mental_health_assessments (
            student_id, stress_level, depression_score, anxiety_score, 
            mental_health_score
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        student_id,
        int(row['Stress_Level']),
        int(row['Depression_Score']),
        int(row['Anxiety_Score']),
        float(row['Mental_Health_Risk'])
    ))
    
    # Insert lifestyle factors
    cursor.execute("""
        INSERT INTO lifestyle_factors (
            student_id, sleep_quality, physical_activity, diet_quality
        ) VALUES (?, ?, ?, ?)
    """, (
        student_id,
        row['Sleep_Quality'],
        row['Physical_Activity'],
        row['Diet_Quality']
    ))
    
    # Insert social factors
    cursor.execute("""
        INSERT INTO social_factors (
            student_id, social_support, relationship_status, 
            substance_use, extracurricular_involvement
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        student_id,
        row['Social_Support'],
        row['Relationship_Status'],
        row['Substance_Use'] if pd.notna(row['Substance_Use']) else 'Never',
        row['Extracurricular_Involvement']
    ))
    
    # Insert support services
    cursor.execute("""
        INSERT INTO support_services (
            student_id, counseling_service_use
        ) VALUES (?, ?)
    """, (
        student_id,
        row['Counseling_Service_Use']
    ))
    
    # Insert medical history
    cursor.execute("""
        INSERT INTO medical_history (
            student_id, family_history_mental_health, chronic_illness
        ) VALUES (?, ?, ?)
    """, (
        student_id,
        1 if row['Family_History'] == 'Yes' else 0,
        1 if row['Chronic_Illness'] == 'Yes' else 0
    ))
    
    # Insert stress factors
    cursor.execute("""
        INSERT INTO stress_factors (
            student_id, financial_stress
        ) VALUES (?, ?)
    """, (
        student_id,
        int(row['Financial_Stress'])
    ))
    
    count += 1
    if count % 1000 == 0:
        print(f"   Processed {count}/{len(df)} records...")
        conn.commit()

conn.commit()
print(f"✓ Inserted {count} students into database")

# Verify data
print("\n5. Verifying database integrity...")
cursor.execute("SELECT COUNT(*) FROM students")
student_count = cursor.fetchone()[0]
print(f"   Students: {student_count}")

cursor.execute("SELECT COUNT(*) FROM mental_health_assessments")
assessment_count = cursor.fetchone()[0]
print(f"   Assessments: {assessment_count}")

cursor.execute("SELECT COUNT(*) FROM lifestyle_factors")
lifestyle_count = cursor.fetchone()[0]
print(f"   Lifestyle records: {lifestyle_count}")

# Test some queries
print("\n6. Sample queries:")
print("-" * 70)

# Average mental health by course
cursor.execute("""
    SELECT course, 
           AVG(stress_level) as avg_stress,
           AVG(depression_score) as avg_depression,
           AVG(anxiety_score) as avg_anxiety,
           COUNT(*) as count
    FROM students s
    JOIN mental_health_assessments mha ON s.student_id = mha.student_id
    GROUP BY course
    ORDER BY avg_stress DESC
""")

print("\nAverage Mental Health Scores by Course:")
print(f"{'Course':<20} {'Stress':>8} {'Depress':>8} {'Anxiety':>8} {'Count':>8}")
print("-" * 70)
for row in cursor.fetchall():
    print(f"{row[0]:<20} {row[1]:>8.2f} {row[2]:>8.2f} {row[3]:>8.2f} {row[4]:>8}")

# High stress students without counseling
cursor.execute("""
    SELECT COUNT(*) 
    FROM mental_health_assessments mha
    JOIN support_services ss ON mha.student_id = ss.student_id
    WHERE mha.stress_level >= 4 
    AND ss.counseling_service_use = 'Never'
""")
high_stress_no_counseling = cursor.fetchone()[0]
print(f"\nHigh stress students (≥4) not using counseling: {high_stress_no_counseling}")

# Sleep quality impact
cursor.execute("""
    SELECT lf.sleep_quality,
           AVG(mha.mental_health_score) as avg_risk,
           COUNT(*) as count
    FROM lifestyle_factors lf
    JOIN mental_health_assessments mha ON lf.student_id = mha.student_id
    GROUP BY lf.sleep_quality
    ORDER BY avg_risk DESC
""")

print("\nMental Health Risk by Sleep Quality:")
print(f"{'Sleep Quality':<20} {'Avg Risk':>10} {'Count':>10}")
print("-" * 70)
for row in cursor.fetchall():
    print(f"{row[0]:<20} {row[1]:>10.3f} {row[2]:>10}")

conn.close()

print("\n" + "="*70)
print("DATABASE SETUP COMPLETE!")
print(f"Database: {db_file}")
print("="*70)

"""
COMPLETE DEMO: Database + ML Pipeline Integration
==================================================
Demonstrates the full workflow from database to predictions
"""

import sqlite3
import pandas as pd
import json
import numpy as np

# Import the ML pipeline components
import sys
import os
from students_mh_ml_pipeline import MentalHealthPredictor


print("="*70)
print("STUDENTS MENTAL HEALTH: COMPLETE DEMO")
print("="*70)

# =============================================================================
# PART 1: LOAD DATA FROM DATABASE
# =============================================================================

print("\n" + "="*70)
print("PART 1: LOADING DATA FROM DATABASE")
print("="*70)

db_path = r"C:\Users\rithe\Downloads\files\students_mental_health.db"
conn = sqlite3.connect(db_path)

# Query using the complete profile view
query = """
SELECT * FROM student_complete_profile LIMIT 10
"""

df_from_db = pd.read_sql_query(query, conn)
print(f"\n✓ Loaded {len(df_from_db)} student profiles from database")
print(f"\nSample data:")
print(df_from_db[['student_id', 'age', 'course', 'stress_level', 
                   'depression_score', 'anxiety_score']].head())

# =============================================================================
# PART 2: TRAIN ML MODEL (FRESH)
# =============================================================================

print("\n" + "="*70)
print("PART 2: TRAINING FRESH ML MODEL")
print("="*70)

# Load CSV for training
csv_file = r'C:\Users\rithe\Downloads\files\students_mental_health_survey.csv'

df_full = pd.read_csv(csv_file)
print(f"✓ Loaded {len(df_full)} students for training")

# Train model
print("\nTraining model...")
model = MentalHealthPredictor()
metrics = model.train(df_full, use_cross_validation=False)
print(f"✓ Model trained (Test MAE: {metrics['test_mae']:.4f})")

# =============================================================================
# PART 3: MAKE PREDICTIONS FOR NEW STUDENTS
# =============================================================================

print("\n" + "="*70)
print("PART 3: PREDICTING MENTAL HEALTH RISK")
print("="*70)

# Load fresh student data for prediction
csv_file = r"C:\Users\rithe\Downloads\files\students_mental_health_survey.csv"

df_students = pd.read_csv(csv_file)

# Select a sample of students
sample_size = 100
sample_students = df_students.sample(n=sample_size, random_state=42)
print(f"\n✓ Selected {sample_size} random students for prediction")

# Make predictions
print("\nMaking predictions...")
predictions = model.predict(sample_students, return_shap=False)
print(f"✓ Generated {len(predictions)} predictions")

# =============================================================================
# PART 4: ANALYZE PREDICTIONS
# =============================================================================

print("\n" + "="*70)
print("PART 4: PREDICTION ANALYSIS")
print("="*70)

# Extract risk scores
risk_scores = [p['mental_health_risk_score'] for p in predictions]
risk_levels = [p['risk_level'] for p in predictions]

# Statistics
print(f"\nRisk Score Statistics:")
print(f"  Mean:   {np.mean(risk_scores):.3f}")
print(f"  Median: {np.median(risk_scores):.3f}")
print(f"  Std:    {np.std(risk_scores):.3f}")
print(f"  Min:    {np.min(risk_scores):.3f}")
print(f"  Max:    {np.max(risk_scores):.3f}")

# Risk level distribution
print(f"\nRisk Level Distribution:")
from collections import Counter
risk_counts = Counter(risk_levels)
for level in ['Low', 'Moderate', 'High', 'Critical']:
    count = risk_counts.get(level, 0)
    pct = (count / len(risk_levels)) * 100
    print(f"  {level:12}: {count:3} ({pct:5.1f}%)")

# Top risk factors
print(f"\nMost Common Risk Factors:")
top_factors = Counter([p['top_risk_factor'] for p in predictions])
for factor, count in top_factors.most_common(5):
    pct = (count / len(predictions)) * 100
    print(f"  {factor:40}: {count:3} ({pct:5.1f}%)")

# =============================================================================
# PART 5: IDENTIFY HIGH-RISK STUDENTS
# =============================================================================

print("\n" + "="*70)
print("PART 5: HIGH-RISK STUDENT IDENTIFICATION")
print("="*70)

# Find high-risk students
high_risk_indices = [i for i, p in enumerate(predictions) 
                    if p['risk_level'] in ['High', 'Critical']]

print(f"\n✓ Identified {len(high_risk_indices)} high-risk students")

if high_risk_indices:
    print(f"\nTop 5 High-Risk Students:")
    print("-" * 70)
    print(f"{'ID':<5} {'Age':<5} {'Course':<20} {'Risk':>6} {'Level':<10} {'Top Factor'}")
    print("-" * 70)
    
    for idx in high_risk_indices[:5]:
        student = sample_students.iloc[idx]
        pred = predictions[idx]
        print(f"{idx:<5} {student['Age']:<5} {student['Course']:<20} "
              f"{pred['mental_health_risk_score']:>6.3f} {pred['risk_level']:<10} "
              f"{pred['top_risk_factor']}")

# =============================================================================
# PART 6: STORE PREDICTIONS BACK TO DATABASE
# =============================================================================

print("\n" + "="*70)
print("PART 6: STORING PREDICTIONS TO DATABASE")
print("="*70)

# Get student IDs (in real scenario, these would come from DB)
# For demo, we'll create synthetic IDs
cursor = conn.cursor()

stored_count = 0
for i, pred in enumerate(predictions[:10]):  # Store first 10 for demo
    # In production, you'd get actual student_id from database
    # For demo, we'll use the first 10 student IDs
    cursor.execute("SELECT student_id FROM students LIMIT 1 OFFSET ?", (i,))
    result = cursor.fetchone()
    if result:
        student_id = result[0]
        
        cursor.execute("""
            INSERT INTO ml_predictions (
                student_id, 
                predicted_stress_level,
                composite_mental_health_score,
                risk_level,
                top_risk_factor,
                feature_importance_json,
                model_version,
                confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            pred['mental_health_risk_score'] * 5,  # Convert to 0-5 scale
            pred['mental_health_risk_score'],
            pred['risk_level'],
            pred['top_risk_factor'],
            json.dumps(pred['feature_importance']),
            pred['model_version'],
            0.85  # Placeholder confidence
        ))
        stored_count += 1

conn.commit()
print(f"✓ Stored {stored_count} predictions to database")

# =============================================================================
# PART 7: QUERY PREDICTIONS FROM DATABASE
# =============================================================================

print("\n" + "="*70)
print("PART 7: QUERYING PREDICTIONS FROM DATABASE")
print("="*70)

# Query stored predictions
cursor.execute("""
    SELECT 
        p.student_id,
        s.age,
        s.course,
        p.composite_mental_health_score,
        p.risk_level,
        p.top_risk_factor,
        mha.stress_level,
        mha.depression_score,
        mha.anxiety_score
    FROM ml_predictions p
    JOIN students s ON p.student_id = s.student_id
    JOIN mental_health_assessments mha ON p.student_id = mha.student_id
    ORDER BY p.composite_mental_health_score DESC
    LIMIT 5
""")

print("\nTop 5 Predicted High-Risk Students (from database):")
print("-" * 90)
print(f"{'ID':<5} {'Age':<5} {'Course':<20} {'Pred Risk':>10} {'Level':<10} "
      f"{'Actual S/D/A':<15} {'Top Factor'}")
print("-" * 90)

for row in cursor.fetchall():
    actual_sda = f"{row[6]}/{row[7]}/{row[8]}"
    print(f"{row[0]:<5} {row[1]:<5} {row[2]:<20} {row[3]:>10.3f} {row[4]:<10} "
          f"{actual_sda:<15} {row[5]}")

# =============================================================================
# PART 8: ACTIONABLE INSIGHTS
# =============================================================================

print("\n" + "="*70)
print("PART 8: ACTIONABLE INSIGHTS FOR INTERVENTION")
print("="*70)

# Students who need counseling
cursor.execute("""
    SELECT COUNT(*)
    FROM ml_predictions p
    JOIN support_services ss ON p.student_id = ss.student_id
    WHERE p.risk_level IN ('High', 'Critical')
    AND ss.counseling_service_use = 'Never'
""")
high_risk_no_counseling = cursor.fetchone()[0]

print(f"\n📊 KEY FINDINGS:")
print(f"   • {high_risk_no_counseling} high-risk students not using counseling")
print(f"   • These students should be prioritized for outreach")

# By course
cursor.execute("""
    SELECT 
        s.course,
        AVG(p.composite_mental_health_score) as avg_risk,
        COUNT(*) as count
    FROM ml_predictions p
    JOIN students s ON p.student_id = s.student_id
    GROUP BY s.course
    ORDER BY avg_risk DESC
""")

print(f"\n📚 RISK BY ACADEMIC PROGRAM:")
for row in cursor.fetchall():
    print(f"   • {row[0]:<20}: {row[1]:.3f} avg risk ({row[2]} students)")

# By lifestyle factor
cursor.execute("""
    SELECT 
        lf.sleep_quality,
        AVG(p.composite_mental_health_score) as avg_risk,
        COUNT(*) as count
    FROM ml_predictions p
    JOIN lifestyle_factors lf ON p.student_id = lf.student_id
    GROUP BY lf.sleep_quality
    ORDER BY avg_risk DESC
""")

print(f"\n😴 RISK BY SLEEP QUALITY:")
for row in cursor.fetchall():
    print(f"   • {row[0]:<20}: {row[1]:.3f} avg risk ({row[2]} students)")

conn.close()

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*70)
print("DEMO COMPLETE - SUMMARY")
print("="*70)

print("""
✅ Successfully demonstrated:
   1. Loading student data from SQLite database
   2. Using pre-trained ML model for predictions
   3. Analyzing mental health risk patterns
   4. Identifying high-risk students
   5. Storing predictions back to database
   6. Querying and analyzing stored predictions
   7. Generating actionable insights for intervention

🎯 REAL-WORLD APPLICATION:
   - Automated early warning system for student mental health
   - Prioritized counseling outreach for high-risk students
   - Evidence-based resource allocation
   - Continuous monitoring and intervention tracking
   
💡 NEXT STEPS:
   - Integrate with student information systems
   - Deploy automated weekly risk assessments
   - Create dashboards for counseling staff
   - Implement intervention tracking and outcome measurement
""")

print("="*70)

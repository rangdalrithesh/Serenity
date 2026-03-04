-- Students Mental Health Survey Database Schema
-- Designed for real student mental health data with demographics, lifestyle, and academic factors

PRAGMA foreign_keys = ON;

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Students table - demographic and academic information
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    age INTEGER NOT NULL CHECK(age >= 18 AND age <= 100),
    course TEXT NOT NULL CHECK(course IN ('Engineering', 'Medical', 'Business', 
                                          'Computer Science', 'Law', 'Others')),
    gender TEXT NOT NULL CHECK(gender IN ('Male', 'Female', 'Other')),
    cgpa REAL CHECK(cgpa >= 0.0 AND cgpa <= 4.0),
    semester_credit_load INTEGER CHECK(semester_credit_load >= 0 AND semester_credit_load <= 40),
    residence_type TEXT CHECK(residence_type IN ('On-Campus', 'Off-Campus', 'With Family')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Mental health assessments - primary mental health metrics
CREATE TABLE mental_health_assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    assessment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Core mental health scores (0-5 scale)
    stress_level INTEGER NOT NULL CHECK(stress_level >= 0 AND stress_level <= 5),
    depression_score INTEGER NOT NULL CHECK(depression_score >= 0 AND depression_score <= 5),
    anxiety_score INTEGER NOT NULL CHECK(anxiety_score >= 0 AND anxiety_score <= 5),
    
    -- Composite mental health score (derived or ML-predicted, 0-1 scale)
    mental_health_score REAL CHECK(mental_health_score >= 0 AND mental_health_score <= 1),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    UNIQUE(student_id, assessment_date)
);

-- Lifestyle factors - sleep, activity, diet
CREATE TABLE lifestyle_factors (
    lifestyle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    recorded_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Categorical lifestyle factors
    sleep_quality TEXT NOT NULL CHECK(sleep_quality IN ('Poor', 'Average', 'Good')),
    physical_activity TEXT NOT NULL CHECK(physical_activity IN ('Low', 'Moderate', 'High')),
    diet_quality TEXT NOT NULL CHECK(diet_quality IN ('Poor', 'Average', 'Good')),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    UNIQUE(student_id, recorded_date)
);

-- Social factors - support, relationships, substance use
CREATE TABLE social_factors (
    social_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    recorded_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Social and behavioral factors
    social_support TEXT NOT NULL CHECK(social_support IN ('Low', 'Moderate', 'High')),
    relationship_status TEXT CHECK(relationship_status IN ('Single', 'In a Relationship', 'Married')),
    substance_use TEXT CHECK(substance_use IN ('Never', 'Occasionally', 'Frequently')),
    extracurricular_involvement TEXT CHECK(extracurricular_involvement IN ('Low', 'Moderate', 'High')),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    UNIQUE(student_id, recorded_date)
);

-- Support services usage - counseling and interventions
CREATE TABLE support_services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    service_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Service usage
    counseling_service_use TEXT NOT NULL CHECK(counseling_service_use IN ('Never', 'Occasionally', 'Frequently')),
    
    -- Optional: track specific interventions
    intervention_type TEXT,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- Medical and family history
CREATE TABLE medical_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL UNIQUE,
    
    -- Medical background
    family_history_mental_health BOOLEAN DEFAULT 0,  -- Family history of mental health issues
    chronic_illness BOOLEAN DEFAULT 0,
    
    -- Additional medical info
    diagnosed_conditions TEXT,  -- JSON or comma-separated list
    medications TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- Financial and academic stress
CREATE TABLE stress_factors (
    stress_factor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    recorded_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Stressors (0-5 scale)
    financial_stress INTEGER NOT NULL CHECK(financial_stress >= 0 AND financial_stress <= 5),
    academic_stress INTEGER CHECK(academic_stress >= 0 AND academic_stress <= 5),
    social_stress INTEGER CHECK(social_stress >= 0 AND social_stress <= 5),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    UNIQUE(student_id, recorded_date)
);

-- ML predictions - store model predictions with explainability
CREATE TABLE ml_predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    assessment_id INTEGER,
    
    -- Predicted scores
    predicted_stress_level REAL NOT NULL CHECK(predicted_stress_level >= 0 AND predicted_stress_level <= 5),
    predicted_depression_risk REAL CHECK(predicted_depression_risk >= 0 AND predicted_depression_risk <= 1),
    predicted_anxiety_risk REAL CHECK(predicted_anxiety_risk >= 0 AND predicted_anxiety_risk <= 1),
    composite_mental_health_score REAL CHECK(composite_mental_health_score >= 0 AND composite_mental_health_score <= 1),
    
    -- Risk categories
    risk_level TEXT CHECK(risk_level IN ('Low', 'Moderate', 'High', 'Critical')),
    
    -- Explainability
    top_risk_factor TEXT,  -- Primary contributing factor
    feature_importance_json TEXT,  -- JSON of all feature importances
    
    -- Model metadata
    model_version TEXT NOT NULL,
    model_type TEXT,
    confidence_score REAL CHECK(confidence_score >= 0 AND confidence_score <= 1),
    
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (student_id) REFERENCES students(student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    FOREIGN KEY (assessment_id) REFERENCES mental_health_assessments(assessment_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

CREATE INDEX idx_students_course ON students(course);
CREATE INDEX idx_students_age ON students(age);
CREATE INDEX idx_assessments_student_date ON mental_health_assessments(student_id, assessment_date);
CREATE INDEX idx_assessments_stress ON mental_health_assessments(stress_level);
CREATE INDEX idx_lifestyle_student ON lifestyle_factors(student_id, recorded_date);
CREATE INDEX idx_social_student ON social_factors(student_id, recorded_date);
CREATE INDEX idx_predictions_student ON ml_predictions(student_id, predicted_at);
CREATE INDEX idx_predictions_risk ON ml_predictions(risk_level);

-- =============================================================================
-- TRIGGERS FOR TIMESTAMP UPDATES
-- =============================================================================

CREATE TRIGGER update_students_timestamp 
AFTER UPDATE ON students
FOR EACH ROW
BEGIN
    UPDATE students SET updated_at = CURRENT_TIMESTAMP WHERE student_id = NEW.student_id;
END;

CREATE TRIGGER update_medical_history_timestamp 
AFTER UPDATE ON medical_history
FOR EACH ROW
BEGIN
    UPDATE medical_history SET updated_at = CURRENT_TIMESTAMP WHERE student_id = NEW.student_id;
END;

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Complete student profile view
CREATE VIEW student_complete_profile AS
SELECT 
    s.student_id,
    s.age,
    s.course,
    s.gender,
    s.cgpa,
    s.semester_credit_load,
    s.residence_type,
    mha.stress_level,
    mha.depression_score,
    mha.anxiety_score,
    lf.sleep_quality,
    lf.physical_activity,
    lf.diet_quality,
    sf.social_support,
    sf.relationship_status,
    sf.substance_use,
    sf.extracurricular_involvement,
    ss.counseling_service_use,
    mh.family_history_mental_health,
    mh.chronic_illness,
    stf.financial_stress
FROM students s
LEFT JOIN mental_health_assessments mha ON s.student_id = mha.student_id
LEFT JOIN lifestyle_factors lf ON s.student_id = lf.student_id
LEFT JOIN social_factors sf ON s.student_id = sf.student_id
LEFT JOIN support_services ss ON s.student_id = ss.student_id
LEFT JOIN medical_history mh ON s.student_id = mh.student_id
LEFT JOIN stress_factors stf ON s.student_id = stf.student_id;

-- High-risk students view
CREATE VIEW high_risk_students AS
SELECT 
    s.student_id,
    s.age,
    s.course,
    s.gender,
    mp.composite_mental_health_score,
    mp.risk_level,
    mp.top_risk_factor,
    mha.stress_level,
    mha.depression_score,
    mha.anxiety_score
FROM students s
JOIN ml_predictions mp ON s.student_id = mp.student_id
JOIN mental_health_assessments mha ON s.student_id = mha.student_id
WHERE mp.risk_level IN ('High', 'Critical')
ORDER BY mp.composite_mental_health_score DESC;

-- =============================================================================
-- SAMPLE QUERIES
-- =============================================================================

-- Query 1: Get complete profile for a student
-- SELECT * FROM student_complete_profile WHERE student_id = ?;

-- Query 2: Get all high-risk students
-- SELECT * FROM high_risk_students;

-- Query 3: Compare mental health across courses
-- SELECT course, 
--        AVG(stress_level) as avg_stress,
--        AVG(depression_score) as avg_depression,
--        AVG(anxiety_score) as avg_anxiety
-- FROM student_complete_profile
-- GROUP BY course
-- ORDER BY avg_stress DESC;

-- Query 4: Students with high stress but no counseling
-- SELECT s.student_id, s.age, s.course, mha.stress_level, ss.counseling_service_use
-- FROM students s
-- JOIN mental_health_assessments mha ON s.student_id = mha.student_id
-- JOIN support_services ss ON s.student_id = ss.student_id
-- WHERE mha.stress_level >= 4 AND ss.counseling_service_use = 'Never';

-- Query 5: Correlation between lifestyle and mental health
-- SELECT 
--     lf.sleep_quality,
--     AVG(mha.stress_level) as avg_stress
-- FROM lifestyle_factors lf
-- JOIN mental_health_assessments mha ON lf.student_id = mha.student_id
-- GROUP BY lf.sleep_quality;

import pandas as pd
import numpy as np

df = pd.read_csv('data/survey.csv')

# ── 1. DROP USELESS COLUMNS ──────────────────────────────────────────
df.drop(columns=['comments', 'Timestamp', 'state'], inplace=True)

# ── 2. FIX AGE ───────────────────────────────────────────────────────
# Replace extreme outliers with median
median_age = df['Age'][(df['Age'] >= 18) & (df['Age'] <= 75)].median()
df['Age'] = df['Age'].apply(lambda x: median_age if x < 18 or x > 75 else x)
df['Age'] = df['Age'].astype(int)

# Age bands
df['AgeBand'] = pd.cut(df['Age'], bins=[17,25,35,45,75],
                        labels=['18-25','26-35','36-45','46+'])

# ── 3. STANDARDIZE GENDER ─────────────────────────────────────────────
def clean_gender(g):
    g = str(g).strip().lower()
    male_terms = ['male','m','man','make','maile','mal','male-ish',
                  'cis male','male (cis)','guy (-ish) ^_^',
                  'male leaning androgynous','something kinda male?']
    female_terms = ['female','f','woman','femake','cis female',
                    'cis-female/femme','female (trans)','trans-female',
                    'trans woman','femail']
    if g in male_terms:
        return 'Male'
    elif g in female_terms:
        return 'Female'
    else:
        return 'Other'

df['Gender'] = df['Gender'].apply(clean_gender)

# ── 4. FILL NULLS ─────────────────────────────────────────────────────
df['work_interfere'] = df['work_interfere'].fillna('Unknown')
df['self_employed'] = df['self_employed'].fillna('No')

# ── 5. BINARY COLUMNS ────────────────────────────────────────────────
df['treatment_binary']   = df['treatment'].apply(lambda x: 1 if x == 'Yes' else 0)
df['remote_work_binary'] = df['remote_work'].apply(lambda x: 1 if x == 'Yes' else 0)
df['family_history_binary'] = df['family_history'].apply(lambda x: 1 if x == 'Yes' else 0)

# ── 6. WORK INTERFERENCE SCORE ───────────────────────────────────────
interfere_map = {'Never': 0, 'Rarely': 1, 'Sometimes': 2, 'Often': 3, 'Unknown': -1}
df['work_interfere_score'] = df['work_interfere'].map(interfere_map)

# ── 7. EMPLOYER SUPPORT SCORE ────────────────────────────────────────
# Combines benefits + wellness_program + seek_help into one score (0-3)
def support_score(row):
    score = 0
    if row['benefits'] == 'Yes': score += 1
    if row['wellness_program'] == 'Yes': score += 1
    if row['seek_help'] == 'Yes': score += 1
    return score

df['employer_support_score'] = df.apply(support_score, axis=1)
df['employer_support_label'] = df['employer_support_score'].map(
    {0: 'No Support', 1: 'Low', 2: 'Medium', 3: 'High'})

# ── 8. HIGH RISK FLAG ────────────────────────────────────────────────
# High risk = not treated + work often interferes + no employer support
df['high_risk'] = ((df['treatment_binary'] == 0) &
                   (df['work_interfere'].isin(['Often','Sometimes'])) &
                   (df['employer_support_score'] == 0)).astype(int)

# ── 9. COMPANY SIZE ORDER ─────────────────────────────────────────────
size_order = {'1-5':1,'6-25':2,'26-100':3,'100-500':4,
              '500-1000':5,'More than 1000':6}
df['company_size_order'] = df['no_employees'].map(size_order)

# ── 10. FINAL CLEANUP ─────────────────────────────────────────────────
df.rename(columns={
    'no_employees': 'CompanySize',
    'remote_work': 'RemoteWork',
    'tech_company': 'TechCompany',
    'family_history': 'FamilyHistory',
    'work_interfere': 'WorkInterfere',
    'self_employed': 'SelfEmployed',
    'treatment': 'Treatment',
    'benefits': 'Benefits',
    'wellness_program': 'WellnessProgram',
    'seek_help': 'SeekHelp',
    'anonymity': 'Anonymity',
    'leave': 'LeaveEase',
    'obs_consequence': 'ObservedConsequence',
    'care_options': 'CareOptions'
}, inplace=True)

print("Shape:", df.shape)
print("\nNull counts:\n", df.isnull().sum())
print("\nGender distribution:\n", df['Gender'].value_counts())
print("\nHigh risk employees:", df['high_risk'].sum())
print("Treatment rate:", f"{df['treatment_binary'].mean()*100:.1f}%")

df.to_csv('mental_health_clean.csv', index=False)
print("\nSaved: mental_health_clean.csv")

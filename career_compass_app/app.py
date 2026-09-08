import pandas as pd
import streamlit as st

from src.config import DATA_PATH
from src.data_prep import load_master_data, create_person1_modeling_data
from src.baseline_model import recommend_baseline
from src.user_profile import (
    EDUCATION_OPTIONS, JOB_ZONE_OPTIONS, SKILL_LABEL_TO_COLUMN, UserProfile
)

st.set_page_config(page_title="Career Compass", layout="wide")
st.title("Career Compass")
st.caption("Person 1 prototype: user profile and labor-market baseline recommender")

@st.cache_data
def get_data() -> pd.DataFrame:
    return create_person1_modeling_data(load_master_data(DATA_PATH))

data = get_data()

st.header("Your career preferences")
col1, col2 = st.columns(2)
with col1:
    realistic = st.slider("Realistic: hands-on and practical work", 1, 5, 3)
    investigative = st.slider("Investigative: analysis, science, and research", 1, 5, 3)
    artistic = st.slider("Artistic: creativity, writing, and design", 1, 5, 3)
with col2:
    social = st.slider("Social: helping, teaching, and caring", 1, 5, 3)
    enterprising = st.slider("Enterprising: leadership, sales, and persuasion", 1, 5, 3)
    conventional = st.slider("Conventional: organization, details, and data", 1, 5, 3)

education_label = st.selectbox("Highest education level you are willing to complete", list(EDUCATION_OPTIONS))
job_zone_label = st.selectbox("Preferred preparation level", list(JOB_ZONE_OPTIONS), index=2)
skills = st.multiselect("Skills you most want to use", list(SKILL_LABEL_TO_COLUMN))

col3, col4 = st.columns(2)
with col3:
    salary_importance = st.slider("Importance of higher salary", 1, 5, 3)
with col4:
    employment_importance = st.slider("Importance of employment opportunities", 1, 5, 3)

top_n = st.radio("Number of recommendations", [5, 10], horizontal=True)

if st.button("Generate baseline recommendations", type="primary"):
    profile = UserProfile(
        profile_name="Streamlit User",
        interest_realistic=realistic,
        interest_investigative=investigative,
        interest_artistic=artistic,
        interest_social=social,
        interest_enterprising=enterprising,
        interest_conventional=conventional,
        education_preference=EDUCATION_OPTIONS[education_label],
        job_zone_preference=JOB_ZONE_OPTIONS[job_zone_label],
        salary_importance=salary_importance,
        employment_importance=employment_importance,
        selected_skills=skills,
    )
    results = recommend_baseline(data, profile, top_n=top_n)
    display = results.rename(columns={
        "rank": "Rank", "occupation_title": "Occupation",
        "baseline_score": "Baseline Score", "a_median": "Median Annual Wage",
        "tot_emp": "Employment", "onet_soc_code": "O*NET SOC Code"
    })
    st.subheader("Baseline recommendations")
    st.dataframe(
        display[["Rank", "Occupation", "O*NET SOC Code", "Baseline Score", "Median Annual Wage", "Employment"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Baseline Score": st.column_config.NumberColumn(format="%.3f"),
            "Median Annual Wage": st.column_config.NumberColumn(format="$%d"),
            "Employment": st.column_config.NumberColumn(format="%d"),
        }
    )
    st.info(
        "This baseline uses only wage and employment opportunity. RIASEC, education, "
        "Job Zone, and skills are collected for the later content-based models but do "
        "not affect this simple baseline ranking."
    )

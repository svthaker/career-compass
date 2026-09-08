from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "career_compass_master.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURE_DIR = PROJECT_ROOT / "figures"

ID_COLUMNS = ["onet_soc_code", "soc_code"]
DISPLAY_COLUMNS = [
    "onet_soc_code", "soc_code", "occupation_title", "occupation_description",
    "a_median", "tot_emp", "median_wage_percentile", "employment_percentile",
    "labor_market_opportunity_score"
]

RIASEC_COLUMNS = [
    "interest_realistic", "interest_investigative", "interest_artistic",
    "interest_social", "interest_enterprising", "interest_conventional"
]

EDUCATION_COLUMNS = [
    "job_zone", "education_expected_category", "education_bachelors_or_higher_pct"
]

BASELINE_COLUMNS = [
    "median_wage_percentile", "employment_percentile",
    "labor_market_opportunity_score"
]

SKILL_COLUMNS = [
    "essential_skill_active_learning_im",
    "essential_skill_active_listening_im",
    "essential_skill_critical_thinking_im",
    "essential_skill_mathematics_im",
    "essential_skill_reading_comprehension_im",
    "essential_skill_science_im",
    "essential_skill_speaking_im",
    "essential_skill_writing_im",
    "transferable_skill_complex_problem_solving_im",
    "transferable_skill_coordination_im",
    "transferable_skill_instructing_im",
    "transferable_skill_judgment_and_decision_making_im",
    "transferable_skill_management_of_financial_resources_im",
    "transferable_skill_management_of_material_resources_im",
    "transferable_skill_management_of_personnel_resources_im",
    "transferable_skill_negotiation_im",
    "transferable_skill_operation_and_control_im",
    "transferable_skill_operations_analysis_im",
    "transferable_skill_operations_monitoring_im",
    "transferable_skill_persuasion_im",
    "transferable_skill_programming_im",
    "transferable_skill_quality_control_analysis_im",
    "transferable_skill_repairing_im",
    "transferable_skill_service_orientation_im",
    "transferable_skill_social_perceptiveness_im",
    "transferable_skill_systems_analysis_im",
    "transferable_skill_systems_evaluation_im",
    "transferable_skill_technology_design_im",
    "transferable_skill_time_management_im",
    "transferable_skill_troubleshooting_im"
]

MODELING_COLUMNS = RIASEC_COLUMNS + EDUCATION_COLUMNS + SKILL_COLUMNS + BASELINE_COLUMNS

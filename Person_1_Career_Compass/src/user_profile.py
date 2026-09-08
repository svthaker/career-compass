from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List

SKILL_LABEL_TO_COLUMN: Dict[str, str] = {
    "Active learning": "essential_skill_active_learning_im",
    "Active listening": "essential_skill_active_listening_im",
    "Critical thinking": "essential_skill_critical_thinking_im",
    "Mathematics": "essential_skill_mathematics_im",
    "Reading comprehension": "essential_skill_reading_comprehension_im",
    "Science": "essential_skill_science_im",
    "Speaking": "essential_skill_speaking_im",
    "Writing": "essential_skill_writing_im",
    "Complex problem solving": "transferable_skill_complex_problem_solving_im",
    "Coordination": "transferable_skill_coordination_im",
    "Instructing": "transferable_skill_instructing_im",
    "Judgment and decision making": "transferable_skill_judgment_and_decision_making_im",
    "Financial resource management": "transferable_skill_management_of_financial_resources_im",
    "Material resource management": "transferable_skill_management_of_material_resources_im",
    "Personnel management": "transferable_skill_management_of_personnel_resources_im",
    "Negotiation": "transferable_skill_negotiation_im",
    "Operation and control": "transferable_skill_operation_and_control_im",
    "Operations analysis": "transferable_skill_operations_analysis_im",
    "Operations monitoring": "transferable_skill_operations_monitoring_im",
    "Persuasion": "transferable_skill_persuasion_im",
    "Programming": "transferable_skill_programming_im",
    "Quality control analysis": "transferable_skill_quality_control_analysis_im",
    "Repairing": "transferable_skill_repairing_im",
    "Service orientation": "transferable_skill_service_orientation_im",
    "Social perceptiveness": "transferable_skill_social_perceptiveness_im",
    "Systems analysis": "transferable_skill_systems_analysis_im",
    "Systems evaluation": "transferable_skill_systems_evaluation_im",
    "Technology design": "transferable_skill_technology_design_im",
    "Time management": "transferable_skill_time_management_im",
    "Troubleshooting": "transferable_skill_troubleshooting_im",
}

EDUCATION_OPTIONS = {
    "Little or no formal education": 1,
    "High school diploma or equivalent": 2,
    "Some college or associate degree": 3,
    "Bachelor's degree": 4,
    "Graduate or professional degree": 5,
}

JOB_ZONE_OPTIONS = {
    "Job Zone 1 — little or no preparation": 1,
    "Job Zone 2 — some preparation": 2,
    "Job Zone 3 — medium preparation": 3,
    "Job Zone 4 — high preparation": 4,
    "Job Zone 5 — extensive preparation": 5,
}

@dataclass
class UserProfile:
    profile_name: str
    interest_realistic: float
    interest_investigative: float
    interest_artistic: float
    interest_social: float
    interest_enterprising: float
    interest_conventional: float
    education_preference: int
    job_zone_preference: int
    salary_importance: float
    employment_importance: float
    selected_skills: List[str]

    def validate(self) -> None:
        for name in [
            "interest_realistic", "interest_investigative", "interest_artistic",
            "interest_social", "interest_enterprising", "interest_conventional",
            "salary_importance", "employment_importance"
        ]:
            value = getattr(self, name)
            if not 1 <= value <= 5:
                raise ValueError(f"{name} must be between 1 and 5; received {value}.")
        if self.education_preference not in range(1, 6):
            raise ValueError("education_preference must be an integer from 1 to 5.")
        if self.job_zone_preference not in range(1, 6):
            raise ValueError("job_zone_preference must be an integer from 1 to 5.")
        unknown = [s for s in self.selected_skills if s not in SKILL_LABEL_TO_COLUMN]
        if unknown:
            raise ValueError(f"Unknown skill labels: {unknown}")

    def to_dict(self) -> dict:
        self.validate()
        return asdict(self)

    def to_model_vector(self) -> dict:
        """Map questionnaire answers to dataset-compatible feature names."""
        self.validate()
        vector = {
            "interest_realistic": self.interest_realistic,
            "interest_investigative": self.interest_investigative,
            "interest_artistic": self.interest_artistic,
            "interest_social": self.interest_social,
            "interest_enterprising": self.interest_enterprising,
            "interest_conventional": self.interest_conventional,
            "education_expected_category": self.education_preference,
            "job_zone": self.job_zone_preference,
        }
        for label, column in SKILL_LABEL_TO_COLUMN.items():
            vector[column] = 5.0 if label in self.selected_skills else 1.0
        return vector

QUESTIONNAIRE_SCHEMA = [
    {"field": "interest_realistic", "question": "How interested are you in hands-on, mechanical, outdoor, or practical work?", "input": "slider", "min": 1, "max": 5},
    {"field": "interest_investigative", "question": "How interested are you in research, analysis, science, or solving complex problems?", "input": "slider", "min": 1, "max": 5},
    {"field": "interest_artistic", "question": "How interested are you in creative, visual, writing, music, or design work?", "input": "slider", "min": 1, "max": 5},
    {"field": "interest_social", "question": "How interested are you in teaching, helping, counseling, or caring for others?", "input": "slider", "min": 1, "max": 5},
    {"field": "interest_enterprising", "question": "How interested are you in leadership, sales, persuasion, or starting projects?", "input": "slider", "min": 1, "max": 5},
    {"field": "interest_conventional", "question": "How interested are you in organized, detail-focused, administrative, or data work?", "input": "slider", "min": 1, "max": 5},
    {"field": "education_preference", "question": "What is the highest level of education you are willing to complete?", "input": "selectbox", "options": EDUCATION_OPTIONS},
    {"field": "job_zone_preference", "question": "How much preparation and experience are you willing to complete?", "input": "selectbox", "options": JOB_ZONE_OPTIONS},
    {"field": "salary_importance", "question": "How important is earning a higher salary?", "input": "slider", "min": 1, "max": 5},
    {"field": "employment_importance", "question": "How important is finding an occupation with many employment opportunities?", "input": "slider", "min": 1, "max": 5},
    {"field": "selected_skills", "question": "Which skills do you most want to use?", "input": "multiselect", "options": list(SKILL_LABEL_TO_COLUMN)},
]

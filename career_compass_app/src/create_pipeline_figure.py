from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from .config import FIGURE_DIR


def create_pipeline_figure(output_path: Path | None = None) -> Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = output_path or FIGURE_DIR / "career_compass_project_pipeline.png"

    steps = [
        "O*NET and BLS Data",
        "Cleaning and SOC-Code Standardization",
        "Merged Master Occupation Dataset",
        "Feature Engineering and Selection",
        "User-Profile Questionnaire",
        "Map User Responses to O*NET Features",
        "Baseline and Recommendation Models",
        "Top-5 and Top-10 Career Rankings",
        "Model Evaluation and Comparison",
        "Streamlit Career Compass Application",
    ]

    fig, ax = plt.subplots(figsize=(11, 15))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ys = list(reversed([0.06 + i * 0.095 for i in range(len(steps))]))

    for i, (label, y) in enumerate(zip(steps, ys)):
        box = FancyBboxPatch(
            (0.16, y), 0.68, 0.052,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            linewidth=1.5, facecolor="white", edgecolor="black"
        )
        ax.add_patch(box)
        ax.text(0.5, y + 0.026, label, ha="center", va="center", fontsize=12)
        if i < len(steps) - 1:
            arrow = FancyArrowPatch(
                (0.5, y - 0.008), (0.5, ys[i + 1] + 0.061),
                arrowstyle="-|>", mutation_scale=16, linewidth=1.3
            )
            ax.add_patch(arrow)

    ax.set_title("Career Compass End-to-End Project Pipeline", fontsize=18, pad=20)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path

if __name__ == "__main__":
    print(create_pipeline_figure())

from src.run_person1 import main as run_outputs
from src.create_pipeline_figure import create_pipeline_figure
from src.evaluate import main as run_recommenders

if __name__ == "__main__":
    run_outputs()
    run_recommenders()
    path = create_pipeline_figure()
    print(f"Pipeline figure saved to: {path}")

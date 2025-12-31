import fire
import sys

from eval_lcd.evaluate import evaluate_functional_correctness


def entry_point(
    sample_file: str,
    problem_file: str,
    k: str = "1,3,4,5,10,20,100,500",
    n_workers: int = 8,
    timeout: float = 60.0
):
    """
    Evaluates the functional correctness of generated samples, and writes
    results to f"{sample_file}_results.jsonl"
    """
    k = list(map(int, k.split(",")))
    results = evaluate_functional_correctness(sample_file, problem_file, k, n_workers, timeout)
    print(results)


def main():
    fire.Fire(entry_point)


sys.exit(main())
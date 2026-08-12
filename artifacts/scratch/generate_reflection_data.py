import sys
import json
from pathlib import Path

# Add root directory to path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from template import RAGASEvaluator, BenchmarkRunner, FailureAnalyzer, QAPair, EvalResult

def main():
    bench_path = root_dir / "artifacts" / "benchmark_results.json"
    with open(bench_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = []
    # Reconstruct EvalResult list
    for item in data["results"]:
        qa = QAPair(
            question=item["question"],
            expected_answer="",
            context=""
        )
        res = EvalResult(
            qa_pair=qa,
            actual_answer=item["actual_answer"],
            faithfulness=item["faithfulness"],
            relevance=item["relevance"],
            completeness=item["completeness"],
            passed=item["passed"],
            failure_type=item["failure_type"]
        )
        res.context_recall = item.get("context_recall")
        res.context_precision = item.get("context_precision")
        results.append(res)
        
    runner = BenchmarkRunner()
    failures = runner.identify_failures(results, threshold=0.5)
    analyzer = FailureAnalyzer()
    
    # 1. Stats table
    metrics = ["context_recall", "context_precision", "faithfulness", "relevance", "completeness", "overall"]
    print("=== Stats table ===")
    for m in metrics:
        vals = []
        for r in results:
            if m == "overall":
                v = r.overall_score()
            else:
                v = getattr(r, m)
            if v is not None:
                vals.append(v)
        avg = sum(vals)/len(vals) if vals else 0
        mn = min(vals) if vals else 0
        mx = max(vals) if vals else 0
        print(f"| {m} | {avg:.3f} | {mn:.3f} | {mx:.3f} |")
        
    print("\n=== Failures ===")
    for r in results:
        if not r.passed:
            # Let's find index in results
            idx = results.index(r)
            qid = data["results"][idx]["id"]
            print(f"ID: {qid} | Question: {r.qa_pair.question} | Actual: {r.actual_answer} | Recall: {r.context_recall:.3f} | Precision: {r.context_precision:.3f} | Faithfulness: {r.faithfulness:.3f} | Relevance: {r.relevance:.3f} | Completeness: {r.completeness:.3f} | Overall: {r.overall_score():.3f} | Failure Type: {r.failure_type}")
            
    print("\n=== Suggestions ===")
    suggestions = analyzer.generate_improvement_suggestions(failures)
    for s in suggestions:
        print(f"- {s}")
        
    print("\n=== Improvement Log ===")
    # Modify failures to have proper ID
    for idx, r in enumerate(results):
        if not r.passed:
            qid = data["results"][idx]["id"]
            # Let's hack the object or just use standard generator
            pass
            
    # Print the log
    log = analyzer.generate_improvement_log(failures, suggestions)
    print(log)

if __name__ == "__main__":
    main()

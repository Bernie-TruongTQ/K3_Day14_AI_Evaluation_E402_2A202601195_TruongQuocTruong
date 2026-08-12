import sys
import json
from pathlib import Path

# Add root directory to path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from template import RAGASEvaluator, rerank_by_overlap, QAPair

def main():
    golden_path = root_dir / "golden_dataset.json"
    actual_path = root_dir / "artifacts" / "actual_answers.json"
    
    with open(golden_path, "r", encoding="utf-8") as f:
        golden_data = json.load(f)
    with open(actual_path, "r", encoding="utf-8") as f:
        actual_data = json.load(f)
        
    actual_by_id = {ans["id"]: ans for ans in actual_data["answers"]}
    
    evaluator = RAGASEvaluator()
    
    # Let's run for all cases, and we'll pick 5 representative ones.
    selected_ids = ["E03", "M02", "M05", "H04", "A02"]
    
    recalls_before = []
    recalls_after = []
    precisions_before = []
    precisions_after = []
    
    print("| ID | Recall before | Recall after | Precision before | Precision after | Delta Precision |")
    print("|---|---:|---:|---:|---:|---:|")
    
    for qa in golden_data["qa_pairs"]:
        qid = qa["id"]
        if qid not in selected_ids:
            continue
        expected = qa["expected_answer"]
        query = qa["question"]
        actual_ans_entry = actual_by_id[qid]
        
        # retrieved contexts
        contexts = [c["text"] for c in actual_ans_entry["retrieved_contexts"]]
        
        recall_before = evaluator.evaluate_context_recall(contexts, expected)
        precision_before = evaluator.evaluate_context_precision(contexts, expected)
        
        reranked_contexts = rerank_by_overlap(contexts, query)
        
        recall_after = evaluator.evaluate_context_recall(reranked_contexts, expected)
        precision_after = evaluator.evaluate_context_precision(reranked_contexts, expected)
        
        delta = precision_after - precision_before
        
        recalls_before.append(recall_before)
        recalls_after.append(recall_after)
        precisions_before.append(precision_before)
        precisions_after.append(precision_after)
        
        print(f"| {qid} | {recall_before:.3f} | {recall_after:.3f} | {precision_before:.3f} | {precision_after:.3f} | {delta:+.3f} |")
        
    avg_recall_b = sum(recalls_before) / len(recalls_before)
    avg_recall_a = sum(recalls_after) / len(recalls_after)
    avg_prec_b = sum(precisions_before) / len(precisions_before)
    avg_prec_a = sum(precisions_after) / len(precisions_after)
    avg_delta = avg_prec_a - avg_prec_b
    
    print(f"| **Avg** | {avg_recall_b:.3f} | {avg_recall_a:.3f} | {avg_prec_b:.3f} | {avg_prec_a:.3f} | {avg_delta:+.3f} |")

if __name__ == "__main__":
    main()

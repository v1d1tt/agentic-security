"""
Exploratory batch run: varied scenarios across both confirmed models,
using the improved harness with ended_cleanly and stuck_in_loop flags.
"""

from src.harness import run_scenario

combos = [('qwen2.5:7b-instruct', 'user_task_1', 'injection_task_1'), ('qwen2.5:7b-instruct', 'user_task_2', 'injection_task_2'), ('qwen2.5:7b-instruct', 'user_task_4', 'injection_task_3'), ('qwen2.5:7b-instruct', 'user_task_5', 'injection_task_6'), ('qwen2.5:7b-instruct', 'user_task_6', 'injection_task_7'), ('qwen2.5:7b-instruct', 'user_task_7', 'injection_task_8'), ('qwen2.5:7b-instruct', 'user_task_8', 'injection_task_0'), ('qwen2.5:7b-instruct', 'user_task_9', 'injection_task_5'), ('llama3.1:8b', 'user_task_1', 'injection_task_1'), ('llama3.1:8b', 'user_task_2', 'injection_task_2'), ('llama3.1:8b', 'user_task_4', 'injection_task_3'), ('llama3.1:8b', 'user_task_5', 'injection_task_6'), ('llama3.1:8b', 'user_task_6', 'injection_task_7'), ('llama3.1:8b', 'user_task_7', 'injection_task_8'), ('llama3.1:8b', 'user_task_8', 'injection_task_0'), ('llama3.1:8b', 'user_task_9', 'injection_task_5')]

results_summary = []

for model, ut, it in combos:
    print(f"Running {model} / {ut} / {it}...")
    try:
        result = run_scenario(model, ut, it)
        print(
            f"  utility={result['utility']} security={result['security']} "
            f"ended_cleanly={result['ended_cleanly']} stuck_in_loop={result['stuck_in_loop']}"
        )
        results_summary.append((model, ut, it, result['utility'], result['security'], result['ended_cleanly'], result['stuck_in_loop']))
    except Exception as e:
        print(f"  ERROR: {e}")
        results_summary.append((model, ut, it, None, None, None, None))
    print()

print("=== SUMMARY ===")
for row in results_summary:
    print(row)

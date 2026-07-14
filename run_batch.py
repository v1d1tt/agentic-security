from src.harness import run_scenario

combos = [
    ("qwen2.5:7b-instruct", "user_task_0", "injection_task_0"),
    ("qwen2.5:7b-instruct", "user_task_0", "injection_task_5"),
    ("qwen2.5:7b-instruct", "user_task_3", "injection_task_4"),
    ("llama3.1:8b", "user_task_0", "injection_task_0"),
    ("llama3.1:8b", "user_task_0", "injection_task_5"),
    ("llama3.1:8b", "user_task_3", "injection_task_4"),
]

for model, ut, it in combos:
    print(f"Running {model} / {ut} / {it}...")
    result = run_scenario(model, ut, it)
    print(f"  utility={result['utility']} security={result['security']}")
    print()

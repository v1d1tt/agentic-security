"""
Small DeepSeek-R1 batch to generate reasoning traces for designing the
recognition classifier. Varied scenarios, including blatant injections
where recognition is most plausible.
"""

from src.harness import run_scenario

MODEL = "deepseek-r1:7b"
TEMP = 0.6

combos = [
    ("user_task_0", "injection_task_0"),   # streaming service (subtle)
    ("user_task_0", "injection_task_5"),   # send max money (blatant)
    ("user_task_2", "injection_task_2"),   # favorite food (blatant-ish)
    ("user_task_3", "injection_task_4"),   # modify recurring payment
    ("user_task_4", "injection_task_5"),   # send max money, different task
    ("user_task_5", "injection_task_7"),   # change password (very blatant)
    ("user_task_6", "injection_task_6"),   # transfer $30k in increments
    ("user_task_7", "injection_task_8"),   # exfiltrate scheduled transactions
    ("user_task_8", "injection_task_0"),   # streaming service, different task
    ("user_task_9", "injection_task_7"),   # change password, different task
]

for ut, it in combos:
    print(f"Running {ut} / {it}...")
    try:
        r = run_scenario(MODEL, ut, it, temperature=TEMP)
        print(f"  utility={r['utility']} security={r['security']} "
              f"ended_cleanly={r['ended_cleanly']} stuck_in_loop={r['stuck_in_loop']}")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()

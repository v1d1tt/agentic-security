"""Re-run the 12 oversized banking deepseek traces at 16k context, compare
taxonomy classification old vs new to check for 4096-truncation corruption."""
import json
from src.harness import run_scenario
from src.recognition import classify_recognition
from src.outcome import compliance
from src.taxonomy import classify_taxonomy
from agentdojo.task_suite.load_suites import get_suites
banking = get_suites('v1')['banking']
env = banking.load_and_inject_default_environment(banking.get_injection_vector_defaults())

oversized = [
    ('user_task_11','injection_task_8'),('user_task_10','injection_task_3'),
    ('user_task_12','injection_task_4'),('user_task_6','injection_task_5'),
    ('user_task_11','injection_task_2'),('user_task_14','injection_task_4'),
    ('user_task_9','injection_task_2'),('user_task_3','injection_task_2'),
    ('user_task_9','injection_task_1'),('user_task_15','injection_task_1'),
    ('user_task_14','injection_task_0'),('user_task_12','injection_task_7'),
]

def classify(d):
    it = banking.get_injection_task_by_id(d['injection_task_id'])
    rec = classify_recognition(d['messages'], it.GOAL)['level']
    comp = compliance(d['messages'], it, env, 'banking')
    return classify_taxonomy(d, rec, comp)['category'], rec, comp, d['injection_encountered']

for ut, it in oversized:
    with open(f'data/traces/deepseek-r1_14b__{ut}__{it}.json') as f:
        old = json.load(f)
    old_cat = classify(old)
    new = run_scenario('deepseek-r1-ctx16k', ut, it, suite_name='banking', temperature=0.6, save=False)
    new['injection_task_id']=it  # ensure keys present
    new_cat = classify(new)
    flag = '' if old_cat[0]==new_cat[0] else '  <<< CHANGED'
    print(f'{ut}/{it}: OLD {old_cat[0]}/{old_cat[1]}/{old_cat[2]}  NEW {new_cat[0]}/{new_cat[1]}/{new_cat[2]}{flag}', flush=True)

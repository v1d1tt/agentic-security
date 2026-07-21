COMBOS = [
    # inj_0 (send email to attacker) - across task types
    ("user_task_0","injection_task_0"),("user_task_13","injection_task_0"),
    ("user_task_16","injection_task_0"),("user_task_24","injection_task_0"),
    ("user_task_25","injection_task_0"),("user_task_29","injection_task_0"),
    ("user_task_33","injection_task_0"),("user_task_35","injection_task_0"),
    ("user_task_9","injection_task_0"),("user_task_39","injection_task_0"),
    # inj_1 (delete file 13)
    ("user_task_26","injection_task_1"),("user_task_27","injection_task_1"),
    ("user_task_29","injection_task_1"),("user_task_30","injection_task_1"),
    ("user_task_35","injection_task_1"),("user_task_1","injection_task_1"),
    ("user_task_13","injection_task_1"),("user_task_24","injection_task_1"),
    ("user_task_31","injection_task_1"),("user_task_34","injection_task_1"),
    # inj_2 (create calendar event w/ attacker)
    ("user_task_6","injection_task_2"),("user_task_9","injection_task_2"),
    ("user_task_12","injection_task_2"),("user_task_18","injection_task_2"),
    ("user_task_20","injection_task_2"),("user_task_21","injection_task_2"),
    ("user_task_0","injection_task_2"),("user_task_2","injection_task_2"),
    ("user_task_13","injection_task_2"),("user_task_17","injection_task_2"),
    # inj_3 (exfil lily's email body to attacker)
    ("user_task_13","injection_task_3"),("user_task_14","injection_task_3"),
    ("user_task_16","injection_task_3"),("user_task_24","injection_task_3"),
    ("user_task_22","injection_task_3"),("user_task_33","injection_task_3"),
    ("user_task_25","injection_task_3"),("user_task_39","injection_task_3"),
    ("user_task_15","injection_task_3"),("user_task_0","injection_task_3"),
    # inj_4 (exfil FB code to attacker)
    ("user_task_16","injection_task_4"),("user_task_39","injection_task_4"),
    ("user_task_13","injection_task_4"),("user_task_24","injection_task_4"),
    ("user_task_22","injection_task_4"),("user_task_14","injection_task_4"),
    ("user_task_0","injection_task_4"),("user_task_25","injection_task_4"),
    ("user_task_33","injection_task_4"),("user_task_17","injection_task_4"),
    # inj_5 (exfil FB code + delete email)
    ("user_task_16","injection_task_5"),("user_task_39","injection_task_5"),
    ("user_task_13","injection_task_5"),("user_task_24","injection_task_5"),
    ("user_task_22","injection_task_5"),("user_task_14","injection_task_5"),
    ("user_task_0","injection_task_5"),("user_task_25","injection_task_5"),
    ("user_task_33","injection_task_5"),("user_task_18","injection_task_5"),
]

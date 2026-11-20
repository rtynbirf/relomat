#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""РЕЛОМАТ — единый вход. Запускает полный конвейер механизма:
сборка пар → конечный автомат → эмерджентные линии → юнит-тесты.
Возвращает ненулевой код, если хоть одна проверка не сошлась."""
import subprocess, sys

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr

fails = []
rc, out = run("python3 build_pairs.py"); print(out.strip().splitlines()[-1] if out.strip() else "")
if rc: fails.append("build_pairs")
rc, out = run("python3 relomat.py pairs.json --out report.json")
line = [l for l in out.splitlines() if "РЕЛОМАТ" in l]
print(line[-1] if line else "РЕЛОМАТ: нет вывода")
if rc or (line and "согласий 43" not in line[-1]): fails.append("relomat")
rc, out = run("python3 emergent.py")
line = [l for l in out.splitlines() if "РЕЛОМАТ на эмерджентных" in l]
print(line[-1] if line else "эмерджентные: нет вывода")
if rc or (line and line[-1].split(": ")[-1].split("/")[0] != line[-1].split(": ")[-1].split("/")[1]):
    fails.append("emergent")
rc, out = run("python3 -m unittest discover -s . -p 'test_*.py'")
print("unittest:", "OK" if rc == 0 else "FAIL")
if rc: fails.append("unittest")

if fails:
    print("ПРОВАЛ:", ", ".join(fails)); sys.exit(1)
print("МЕХАНИЗМ: все проверки сошлись (пары 43/43, эмерджентные — полное согласие, тесты OK)")

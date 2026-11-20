#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка пар для РЕЛОМАТА из реальных данных проекта:
   мастер-каталог (kind по коду типа), кандидаты V2 (link_note из файла пользователя),
   пары из Реестра вердиктов 001–200, плюс категориальные ловушки (канон)."""
import json, re, sys

BASE = "/home/z/my-project"
master = {r["num"]: r for r in json.load(open(f"{BASE}/scripts/master.json"))["records"]}
v2 = json.load(open(f"{BASE}/scripts/v2.json"))
cands = {p["v2_ref"] and int(p["v2_ref"][3:]): p for p in json.load(open(f"{BASE}/scripts/passports.json"))["passports"] if p["v2_ref"] != "—"}
v2_new = {}
for vn in range(901, 1001):
    raw = v2.get("new_901_1000") or {}
    pass

# --- извлечь позиции V2 из исходного словаря v2.json
v2pos = {p["num"]: p for p in (v2.get("new_901_1000") or [])}
def v2get(n):
    return v2pos.get(n)

RU2CODE = {"Тренд":"T","Практика":"P","Технология":"TECH","Метод":"M","Архитектура":"A",
           "Принцип":"PR","Стандарт":"ST","Протокол":"PROT","Инфраструктура":"INF",
           "Организационная модель":"ORG","Гипотеза":"H","Экспериментальная технология":"EXP"}

def cat_entity(num):
    r = master[num]
    code = None
    for ru, c in RU2CODE.items():
        if r["type"].startswith(ru):
            code = c; break
    return {"id": str(num), "name": r["name_en"], "type_code": code or "P",
            "essence": r.get("description", "")}

def cand_entity(vn):
    p = cands[vn]
    return {"id": str(vn), "name": p["name_en"], "type_code": p["type_code"],
            "link_note": (v2get(vn) or {}).get("link_note", ""), "essence": p["description"]}

def rel_targets(typed_rel):
    """номера целей из строки 'IS-A: №030 (...); RELATED: №014' — первая цель главная"""
    m = re.findall(r"№(\d+)", typed_rel or "")
    return [int(x) for x in m]

def build_v12_pairs():
    """Пары v1.2: строка-аннотация = линия атласа (typed_rel) — автомат
    верифицирует, что написанная строка выдерживает канон."""
    pairs = []
    for vn, p in cands.items():
        tr = p["typed_rel"]
        if tr == "—":
            continue
        rel = tr.split(":")[0].strip()
        tg = rel_targets(tr)
        if rel == "SAME":
            b = cat_entity(tg[0])
            b["type_code"] = {"Метод": "M", "Практика": "P", "Технология": "TECH"}.get(
                master[tg[0]]["type"].split(" ")[0], b["type_code"])
            a = cand_entity(vn); a["link_note"] = f"SAME: №{tg[0]} — точное совпадение сущности"
            pairs.append({"a": a, "b": b, "expected": "SAME", "src": f"V2:{vn}"})
        else:
            keymap = {num: key for key, num in re.findall(r"([A-Z][A-Z-]+)\s*:\s*№?\s*0*(\d+)", tr)}
            for t in tg:
                b = cand_entity(t) if t in cands else cat_entity(t)
                a = cand_entity(vn); a["link_note"] = tr
                pairs.append({"a": a, "b": b, "expected": keymap.get(str(t), rel), "src": f"V2:{vn}"})
    return pairs

def build_registry_pairs():
    """пары из Реестра вердиктов 001–200 (строки-источники реального аудита)"""
    reg = [
        (44, 47, "TOOL-OF", "TOOL-OF: 047 — инструмент vs метод, по правилам не сливать"),
        (46, 45, "IS-A", "IS-A: 045 — частный случай семейства RAG"),
        (28, 29, "COMPLEMENTARY", "COMPLEMENTARY: 029 — защита цепочки поставок и её манифест дополняют друг друга"),
        (36, 37, "COMPLEMENTARY", "COMPLEMENTARY: 037 — событийная архитектура и CQRS усиливают друг друга"),
        (13, 114, "COMPLEMENTARY", "COMPLEMENTARY: 114 — SDL ставит эксперименты, 013 ищет гипотезы"),
    ]
    pairs = []
    for a, b, exp, note in reg:
        ea = cat_entity(a); ea["link_note"] = note
        pairs.append({"a": ea, "b": cat_entity(b), "expected": exp, "src": f"Реестр:{a}"})
    return pairs

def build_adversarial():
    """канонические ловушки: категория×метод, свойство×инструмент, экземпляр×класс"""
    traps = []
    # 1) SAME при разных ролях запрещён: "MLOps-практика" и "MLOps-метод" —
    #    одна роль (practice) → SAME; разные роли — несливаемы
    t1a = {"id": "t1", "name": "MLOps", "type_code": "P", "link_note": "SAME: 1003 — точное совпадение"}
    t1b = {"id": "t2", "name": "MLOps", "type_code": "M", "essence": ""}
    traps.append({"a": t1a, "b": t1b, "expected": "SAME", "src": "ров: код типа различается, роль одна"})
    # 1b) категория × её частный метод — имена различны, слияние запрещено
    t1c = {"id": "t1c", "name": "Governance", "type_code": "PR", "link_note": ""}
    t1d = {"id": "t1d", "name": "Federated Governance", "type_code": "M", "essence": ""}
    traps.append({"a": t1c, "b": t1d, "expected": "RELATED", "src": "ров: категория×метод"})
    # 2) свойство×инструмент: база данных — инструмент метода поиска
    t2a = {"id": "t3", "name": "Vector Databases", "type_code": "TECH",
           "link_note": "TOOL-OF: 047 — инструмент vs метод, по правилам не сливать"}
    t2b = {"id": "t4", "name": "Semantic Search", "type_code": "M", "essence": ""}
    traps.append({"a": t2a, "b": t2b, "expected": "TOOL-OF", "src": "ров: свойство×инструмент"})
    # 3) экземпляр×класс: W3C-стандарт воплощает принцип
    t3a = {"id": "t5", "name": "W3C Verifiable Credentials", "type_code": "ST",
           "link_note": "INSTANCE: 057 — стандарт, воплощающий принцип самосуверенной идентичности"}
    t3b = {"id": "t6", "name": "Self-Sovereign Identity", "type_code": "PR", "essence": ""}
    traps.append({"a": t3a, "b": t3b, "expected": "INSTANCE", "src": "ров: экземпляр×класс"})
    return traps

if __name__ == "__main__":
    pairs = build_v12_pairs() + build_registry_pairs() + build_adversarial()
    json.dump(pairs, open(f"{BASE}/scripts/relomat/pairs.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"пар: {len(pairs)} (v1.2: {len(build_v12_pairs())}, реестр: {len(build_registry_pairs())}, ловушки: {len(build_adversarial())})")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Эмерджентные кандидаты 1146–1151: тренды 2026 × разрывы каталога.
Каждый получает строку-отношение; РЕЛОМАТ верифицирует её механически."""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, f"{BASE}/scripts/relomat")
from relomat import Relomat

EMERGENT = [
    {"id": "1146", "name": "Agent Observability & Tracing", "type_code": "TECH",
     "trend": "Stanford AI Index 2026: агенты выполняют многошаговые задачи в 4–6 п.п. от человека; масштабирование требует наблюдаемости",
     "line": "IS-A: №070 — дисциплина SRE, перенесённая на агентные системы; COMPLEMENTARY: №988 (кандидат) — ассуранс до деплоя + наблюдаемость в рантайме",
     "targets": [{"num": 70, "name": "Site Reliability Engineering", "type_code": "ORG", "expected": "IS-A"}],
     "extra_targets": [{"id": "988", "name": "Continuous AI Assurance", "type_code": "P", "expected": "COMPLEMENTARY", "note": "кандидат V2:988"}]},
    {"id": "1147", "name": "AI Governance Platforms", "type_code": "TECH",
     "trend": "Gartner Top Strategic Technology Trends 2026: платформы ИИ-управления в «вангарде» security/trust/governance",
     "line": "TOOL-OF: №1014 — платформа-инструмент для практики ИИ-управления; по канону инструмент ≠ метод, не сливать",
     "targets": [{"num": 1014, "name": "AI Governance", "type_code": "ORG", "expected": "TOOL-OF"}]},
    {"id": "1148", "name": "Disinformation Security", "type_code": "P",
     "trend": "Gartner 2026: защита от дезинформации и фрода — самостоятельная дисциплина",
     "line": "COMPLEMENTARY: №1041 — детекция синтетики (техника) + защита от дезинформации (операционная дисциплина) усиливают друг друга",
     "targets": [{"num": 1041, "name": "Synthetic Media Detection", "type_code": "P", "expected": "COMPLEMENTARY"}]},
    {"id": "1149", "name": "AI-Ready Data Governance", "type_code": "M",
     "trend": "Gartner (окт 2026): семантика в AI-ready данных повысит точность агентного ИИ до 80% к 2027",
     "line": "RELATED: №43 — семантический слой знаний; самостоятельная дисциплина подготовки данных для агентов",
     "targets": [{"num": 43, "name": "Knowledge Graphs", "type_code": "TECH", "expected": "RELATED"}]},
    {"id": "1150", "name": "Agentic Workforce Upskilling", "type_code": "ORG",
     "trend": "Stanford AI Index 2026: упоминания навыка Agentic AI в вакансиях выросли на 280% за год",
     "line": "RELATED: №1014 — орг-модель развития персонала под агентную рабочую силу; практику workforce-перехода в каталоге нет",
     "targets": [{"num": 1014, "name": "AI Governance", "type_code": "ORG", "expected": "RELATED"}]},
    {"id": "1151", "name": "Agentic AI Red Teaming", "type_code": "P",
     "trend": "AI Index 2026: агенты близки к человеческим бейслайнам в кибербезопасности — нужна агентная красная команда",
     "line": "IS-A: №1015 — разновидность ИИ-красной команды: многоходовые, тул-юз и identity-атаки агентов",
     "targets": [{"num": 1015, "name": "AI Red Teaming", "type_code": "P", "expected": "IS-A"}]},
    {"id": "1152", "name": "Agent2Agent (A2A) Protocol", "type_code": "PROT",
     "trend": "Обход трендов v1.4: открытый протокол агент-агент в производственной эксплуатации у 150+ организаций (2026)",
     "line": "COMPLEMENTARY: №1048 — MCP соединяет агента с инструментами и данными; A2A соединяет агентов между собой: дополняющие уровни интероперабельности, не дубли; RELATED: №001 — протокол для архитектуры мультиагентных систем, протокол ≠ архитектура",
     "targets": [{"num": 1048, "name": "Model Context Protocol (MCP)", "type_code": "PROT", "expected": "COMPLEMENTARY"}],
     "extra_targets": [{"num": 1, "name": "Multi-Agent Systems", "type_code": "A", "expected": "RELATED"}]},
    {"id": "1153", "name": "Large Quantitative Models", "type_code": "TECH",
     "trend": "Gartner Top Strategic Technology Trends: LQM в «вангарде» трендов 2026–2027",
     "line": "IS-A: №1001 — разновидность больших (foundation) моделей: класс, оптимизированный под количественное рассуждение",
     "targets": [{"num": 1001, "name": "Foundation Models", "type_code": "TECH", "expected": "IS-A"}]},
    {"id": "1154", "name": "Speech Reasoning Models", "type_code": "TECH",
     "trend": "Gartner Top Strategic Technology Trends: SRM в «вангарде» трендов 2026–2027",
     "line": "RELATED: №376 — речевой стек (транскрипция/синтез); SRM поднимает речь от ввода/вывода к рассуждению — самостоятельная категория",
     "targets": [{"num": 376, "name": "Speech-to-Text", "type_code": "TECH", "expected": "RELATED"}]},
]

if __name__ == "__main__":
    pairs = []
    for e in EMERGENT:
        for t in e["targets"] + e.get("extra_targets", []):
            a = {"id": e["id"], "name": e["name"], "type_code": e["type_code"], "link_note": e["line"]}
            b = {"id": str(t.get("num", t.get("id"))), "name": t["name"], "type_code": t["type_code"]}
            pairs.append({"a": a, "b": b, "expected": t["expected"], "src": f"Эмерджентный {e['id']}"})
    json.dump(pairs, open(f"{BASE}/emergent_pairs.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    rep = Relomat()
    agree = 0
    rows = []
    for p in pairs:
        v, _, _ = rep.run(p["a"], p["b"])
        ok = v == p["expected"]
        agree += ok
        rows.append({"src": p["src"], "b": p["b"]["name"], "v": v, "exp": p["expected"], "ok": ok})
    for r in rows:
        print(f"  [{'OK' if r['ok'] else 'РАСХ'}] {r['src']:22} × {r['b'][:30]:30} → {r['v']:13} (ожидалось {r['exp']})")
    print(f"РЕЛОМАТ на эмерджентных: {agree}/{len(rows)}")
    json.dump({"candidates": EMERGENT, "verification": rows, "agree": agree, "total": len(rows)},
              open(f"{BASE}/emergent_report.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

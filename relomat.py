#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
РЕЛОМАТ v1.0 — конечный детерминированный автомат типизированных отношений.
Канон роя: не объединять категорию с методом, свойство с инструментом,
экземпляр с классом; похожее название ≠ одинаковая сущность — сравниваются
предмет, механизм, назначение и границы применимости. Большинство «похожих»
позиций получают не MERGE, а типизированное отношение из словаря.

Доктрина «проверяй строкой, не смыслом». Автомат потребляет три механических
потока доказательств и выдаёт вердикт + трассу:

  П1. точное имя (после нормализации) + совпадение РОЛИ → SAME
      (расхождение кода типа между источниками — пометка аудиту);
  П2. строка-аннотация отношения (линия атласа «IS-A: №030 (...)») — вердикт
      берётся из строки, НО канонические запреты проверяются по ролям:
      если строка заявляет SAME при разных ролях — вердикт исправляется
      автоматом и регистрируется нарушение канона;
  П3. лексический/структурный путь (нет аннотации): вложенность имён → IS-A,
      роль-пара (инструмент×метод → TOOL-OF, стандарт×практика → METHOD-OF…),
      пересечение значимых токенов ≥2 при одной роли → MEMBER-OF,
      пересечение ≥1 → RELATED, иначе NEW.

Только stdlib. Все переходы трассируются: S0-вход → S1-нормализация →
S2-имя → S3-роль → S4-семейство → S5-роль-строка → S6-вердикт → HALT.
"""
import json
import re
import sys
import unicodedata

# ---------------------------------------------------------------- словарь
REL_DICT = {
    "SAME": "одно и то же (окончательное слияние — только после проверки полных формулировок)",
    "IS-A": "разновидность более общего направления",
    "PART-OF": "составная часть более широкой системы",
    "TOOL-OF": "инструмент для другой сущности",
    "METHOD-OF": "метод для другой сущности",
    "RELATED": "родственные, но самостоятельные сущности",
    "COMPLEMENTARY": "практики, усиливающие друг друга",
    "MEMBER-OF": "член семейства направлений",
    "INSTANCE": "конкретный экземпляр общего принципа",
    "FRAMEWORK": "рамка/стандарт для частных случаев",
}

CODE_KIND = {
    "T": "trend", "P": "practice", "TECH": "technology", "M": "practice",
    "A": "system", "PR": "principle", "ST": "standard", "PROT": "standard",
    "INF": "system", "ORG": "org", "H": "hypothesis", "EXP": "practice",
}
STOP = {"и", "для", "the", "of", "in", "on", "с", "по", "а", "или", "как"}
TOOL_LEXICON = ("database", "registry", "platform", "library", "store", "engine",
                "toolkit", "tool", "catalog", "ledger", "explorer", "index")
FEATS = {
    "instance":  re.compile(r"воплощ|экземпляр|реализующ", re.I),
    "reinforce": re.compile(r"дополня|усилива|две стороны|↔", re.I),
    "part":      re.compile(r"составная часть|внутри системы|стандарты совместимости|система отчётности", re.I),
    "method":    re.compile(r"стандарт|методология|формализ", re.I),
    "specific":  re.compile(r"частный случай|разновидност|конкретиза|примен[яе]н\w*.{0,14}к |адаптация|перенес[ёе]н\w*.{0,12}на |ML-разновидность|перенесённая|конкретизированное", re.I),
    "member":    re.compile(r"семейств|член", re.I),
    "tool":      re.compile(r"инструмент|database|движок|платформа", re.I),
}
KEY_RX = re.compile(r"^\s*([A-Z][A-Z-]+)\s*:")
KEYMAP_RX = re.compile(r"([A-Z][A-Z-]+)\s*:\s*№?\s*0*(\d+)")


def norm(s):
    s = unicodedata.normalize("NFKC", (s or "")).lower().replace("ё", "е")
    return re.sub(r"\s+", " ", s).strip()


def tokens(s):
    return {w for w in re.findall(r"[a-zа-я0-9]{3,}", norm(s)) if w not in STOP}


def roles_of(e):
    """РОЛИ — предмет, а не ярлык источника: множество по ВСЕМ частям
    двойного кода (H/M → {hypothesis, practice}). SAME — при пересечении."""
    codes = [c.strip() for c in (e.get("type_code") or e.get("kind") or "").split("/") if c.strip()]
    out = set()
    for code in codes:
        kind = CODE_KIND.get(code, code or "practice")
        name = norm(e.get("name", ""))
        note = norm((e.get("link_note") or "") + " " + (e.get("essence") or ""))
        if kind == "standard":
            out.add("principle" if "воплощ" in note else "standard")
        elif kind == "principle":
            out.add("principle")
        elif kind in ("technology", "system"):
            out.add("tool" if (re.search("|".join(TOOL_LEXICON), name) or "инструмент" in note) else "system")
        else:
            out.add(kind)  # practice / hypothesis / trend / org
    return out or {"practice"}


def role_of(e):
    """первичная роль — по первому классу кода (для выбора разноролевого отношения)"""
    return sorted(roles_of(e), key=lambda r: ((e.get("type_code") or "").split("/")[0] != {"practice": "M", "standard": "ST", "principle": "PR", "tool": "TECH", "system": "A"}.get(r, "?"), r))[0] if roles_of(e) else "practice"


def features(a):
    txt = (a.get("link_note") or "") + " " + (a.get("essence") or "")
    f = {k: bool(rx.search(txt)) for k, rx in FEATS.items()}
    m = KEY_RX.match(a.get("link_note") or "")
    f["key"] = m.group(1) if m else None
    # карта «№цели → ключ отношения» для многоцелевых строк: REL: №A — ...; REL2: №B — ...
    f["keymap"] = {num: key for key, num in KEYMAP_RX.findall(a.get("link_note") or "")}
    f["tool"] = f["tool"] or "tool" in roles_of(a)
    return f


ROLE_REL = {  # (роль a, роль b) → отношение, если роли различаются
    frozenset(("standard", "practice")): "METHOD-OF",
    frozenset(("standard", "system")): "PART-OF",
    frozenset(("standard", "principle")): "INSTANCE",
    frozenset(("tool", "practice")): "TOOL-OF",
    frozenset(("tool", "system")): "TOOL-OF",
}
ANN_ORDER = ["INSTANCE", "COMPLEMENTARY", "PART-OF", "METHOD-OF", "IS-A",
             "MEMBER-OF", "TOOL-OF", "RELATED", "SAME"]


class Relomat:
    """δ: S0→S1→S2→(S3|S5)→S6→HALT; детерминировано, с полной трассой."""
    STATES = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "HALT")

    def __init__(self):
        self.trace, self.flags = [], []

    def _go(self, st, fact, det=""):
        self.trace.append(f"{st}: {fact}" + (f" — {det}" if det else ""))

    def run(self, a, b):
        self.trace, self.flags = [], []
        self._go("S0", f"вход: {a.get('name')} × {b.get('name')}")
        na, nb = norm(a.get("name")), norm(b.get("name"))
        ta, tb = tokens(a.get("name")), tokens(b.get("name"))
        ra, rb = roles_of(a), roles_of(b)
        pa, pb = role_of(a), role_of(b)
        f = features(a)
        ov = ta & tb
        subset = bool(tb) and tb <= ta and na != nb
        self._go("S1", f"нормализация: токены a={len(ta)} b={len(tb)} ov={len(ov)} "
                       f"роли {sorted(ra)}/{sorted(rb)} строка-аннотация: {f['key'] or '—'}")
        # S2 — испытание имени
        if na == nb:
            self._go("S2", "точное имя после нормализации")
            # S3 — канон: SAME только при равенстве ролей
            if ra & rb:
                flag = "" if set((a.get("type_code") or "").split("/")) == set((b.get("type_code") or "").split("/")) else "расхождение кода типа — пометка аудиту"
                if flag:
                    self.flags.append(flag)
                self._go("S3", f"роли пересекаются {sorted(ra & rb)}", flag or "слияние допустимо, строка сохраняется")
                return self._emit("SAME", "точное имя и та же роль; поглощение — после сверки полных формулировок")
            self._go("S3", f"роли не пересекаются: {sorted(ra)} ≠ {sorted(rb)} — канон запрещает слияние")
            rel = ROLE_REL.get(frozenset((pa, pb)), "RELATED")
            return self._emit(rel, "разноролевые сущности получают отношение, не MERGE")
        self._go("S2", f"имена различаются (ov={len(ov)}, subset={subset})")
        # S5 — строка-аннотация (линия атласа) + канонические запреты
        if f["key"]:
            # для многоцелевой строки ключ выбирается по номеру цели, иначе — первый в строке
            m_id = re.search(r"\d+", str(b.get("id") or ""))
            key = (f["keymap"].get(m_id.group(0).lstrip("0") or "0", f["key"]) if m_id else f["key"]) if f["keymap"] else f["key"]
            self._go("S5", f"строка-аннотация заявляет {key} (для цели №{b.get('id')})")
            f = dict(f, key=key)
            if f["key"] == "SAME" and not (ra & rb):
                rel = ROLE_REL.get(frozenset((pa, pb)), "RELATED")
                self.flags.append(f"нарушение канона в строке: SAME при {sorted(ra)}≠{sorted(rb)} → исправлено на {rel}")
                return self._emit(rel, "автомат исправил строку по канону")
            if f["key"] in REL_DICT and f["key"] != "SAME":
                if (ra & rb) and f["key"] in ("METHOD-OF", "TOOL-OF", "INSTANCE", "PART-OF") and not any(
                        f[x] for x in ("method", "part", "instance", "tool", "specific", "reinforce", "member")):
                    self.flags.append(f"строка {f['key']} без признаков в тексте — понижено до RELATED")
                    return self._emit("RELATED", "аннотация не подкреплена строкой")
                return self._emit(f["key"], "вердикт из строки-аннотации, запреты канона проверены")
        # S5lite — лексический/ролевой путь (свежие строки без аннотации)
        self._go("S5", "аннотации нет — лексический/ролевой путь")
        if f["instance"] or (ra == {"standard"} and rb == {"principle"}):
            return self._emit("INSTANCE", "стандарт воплощает принцип")
        if f["reinforce"]:
            return self._emit("COMPLEMENTARY", "признак взаимного усиления")
        if f["part"]:
            return self._emit("PART-OF", "признак составной части")
        if f["method"] and ra == {"standard"} and rb & {"practice", "system"}:
            return self._emit("METHOD-OF", "стандарт формализует практику/систему")
        if f["specific"] or subset:
            return self._emit("IS-A", "разновидность/вложенность имён")
        if f["tool"] and rb & {"practice", "system"}:
            return self._emit("TOOL-OF", "инструмент для метода — не сливать")
        if (ra & rb) and len(ov) >= 2 and f["member"]:
            return self._emit("MEMBER-OF", "член семейства")
        if (ra & rb) and len(ov) >= 2:
            return self._emit("RELATED", "общие токены, признаков отношения нет")
        if len(ov) >= 1:
            return self._emit("RELATED", "единичное пересечение токенов")
        return self._emit("NEW", "пересечений не выявлено")

    def _emit(self, verdict, why):
        self._go("S6", f"вердикт: {verdict}", why)
        self._go("HALT", "выход")
        return verdict, list(self.trace), list(self.flags)


def run_pairs(pairs, show_trace=False, out=None):
    m = Relomat()
    rows, agree = [], 0
    for p in pairs:
        verdict, trace, flags = m.run(p["a"], p["b"])
        exp = p.get("expected")
        ok = (exp is None and verdict == "NEW") or (exp == verdict)
        agree += ok
        rows.append({"src": p.get("src", ""), "a": p["a"].get("name"), "b": p["b"].get("name"),
                     "verdict": verdict, "expected": exp, "agree": ok, "flags": flags})
        if show_trace:
            print("\n".join(trace) + "\n---")
    report = {"total": len(rows), "agree": agree,
              "rate": round(agree / len(rows), 4) if rows else 0.0, "rows": rows}
    if out:
        json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return report


def main(argv):
    if len(argv) < 2:
        print("использование: relomat.py <pairs.json> [--trace] [--out report.json]")
        return 2
    pairs = json.load(open(argv[1], encoding="utf-8"))
    rep = run_pairs(pairs, "--trace" in argv,
                    argv[argv.index("--out") + 1] if "--out" in argv else None)
    print(f"РЕЛОМАТ: пар {rep['total']}, согласий {rep['agree']}, доля {rep['rate']:.0%}")
    for r in rep["rows"]:
        mark = "OK " if r["agree"] else "РАСХ"
        exp = r["expected"] or "NEW"
        print(f"  [{mark}] {r['a'][:34]:34} × {r['b'][:26]:26} → {r['verdict']:13} (ожидалось {exp}){' ' + '; '.join(r['flags']) if r['flags'] else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

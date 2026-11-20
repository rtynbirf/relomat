#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты РЕЛОМАТА: канон типизированных отношений как конечный автомат.
Каждый тест — строка-источник + ожидаемый вердикт. Запуск: python -m unittest"""
import unittest
from relomat import Relomat, roles_of, REL_DICT

E = lambda n, c, note="": {"name": n, "type_code": c, "link_note": note}

M = Relomat()


def verdict(a, b):
    return M.run(a, b)[0]


class TestCanon(unittest.TestCase):
    def test_dict_has_ten_relations(self):
        self.assertEqual(len(REL_DICT), 10)
        for k in ("SAME", "IS-A", "PART-OF", "TOOL-OF", "METHOD-OF", "RELATED",
                  "COMPLEMENTARY", "MEMBER-OF", "INSTANCE", "FRAMEWORK"):
            self.assertIn(k, REL_DICT)

    # ---- категориальные запреты канона ----
    def test_same_requires_role_intersection(self):
        # точное имя, роли пересекаются (двойной код H/M против Метод) → SAME
        self.assertEqual(verdict(E("Mechanistic Interpretability", "H/M", "SAME: 1011"),
                                 E("Mechanistic Interpretability", "M")), "SAME")

    def test_category_vs_method_never_same(self):
        # категория и её частный метод — имена различаются, слияние запрещено
        self.assertNotEqual(verdict(E("Governance", "PR"), E("Federated Governance", "M")), "SAME")

    def test_property_vs_instrument_tool_of(self):
        v = verdict(E("Vector Databases", "TECH", "TOOL-OF: 047 — инструмент vs метод, по правилам не сливать"),
                    E("Semantic Search", "M"))
        self.assertEqual(v, "TOOL-OF")

    def test_instance_vs_class(self):
        v = verdict(E("W3C Verifiable Credentials", "ST", "INSTANCE: 057 — стандарт, воплощающий принцип SSI"),
                    E("Self-Sovereign Identity", "PR"))
        self.assertEqual(v, "INSTANCE")

    def test_automaton_overrides_bad_same_line(self):
        # строка заявляет SAME при разных ролях — автомат исправляет по канону
        v = verdict(E("Zero Trust", "ST", "SAME: 051 — ошибочная строка"), E("Something Else", "PR"))
        self.assertNotEqual(v, "SAME")

    # ---- типизированные отношения v1.2 ----
    def test_facet_is_not_merged(self):
        self.assertEqual(verdict(E("Digital Product Passport Interoperability", "ST",
                                   "PART-OF: 095 — стандарты совместимости внутри системы паспортов продукции"),
                                 E("Digital Product Passports", "P")), "PART-OF")
        self.assertEqual(verdict(E("Prompt Engineering Standards", "ST",
                                   "METHOD-OF: 1010 — формализованная методология практики"),
                                 E("Prompt Engineering", "P")), "METHOD-OF")

    def test_complementary_detected(self):
        self.assertEqual(verdict(E("Synthetic Media Provenance", "P",
                                   "COMPLEMENTARY: 1041 — происхождение + детекция = две стороны проверки"),
                                 E("Synthetic Media Detection", "TECH")), "COMPLEMENTARY")

    def test_is_a_family(self):
        self.assertEqual(verdict(E("Federated Data Governance", "M",
                                   "IS-A: 231 — федеративное управление, конкретизированное на данных"),
                                 E("Federated Governance", "M")), "IS-A")

    def test_no_overlap_no_relation(self):
        self.assertEqual(verdict(E("Quantum Blockchain", "TECH"), E("Urban Gardening", "P")), "NEW")

    def test_roles_are_sets_from_dual_codes(self):
        self.assertEqual(roles_of(E("X", "H/M")), {"hypothesis", "practice"})


if __name__ == "__main__":
    unittest.main(verbosity=2)

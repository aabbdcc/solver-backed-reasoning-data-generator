#!/usr/bin/env python3
"""
Solver-Backed Reasoning Data Generator

A small prototype for generating simple first-order-logic-style reasoning
instances over unary predicate implications.

The prototype generates:
- one-step entailed cases
- two-step entailed cases
- non-entailed cases
- distractor-rule cases

It uses a lightweight forward-chaining checker implemented in Python.
No external theorem prover, SMT solver, or Prolog engine is required.

Run:
    python generate.py --n 20 --output examples.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
from collections import deque
from typing import Dict, List, Optional, Sequence, Set, Tuple


Predicate = str
Entity = str
Rule = Tuple[Predicate, Predicate]          # A -> B, rendered as ∀x A(x) -> B(x)
Fact = Tuple[Predicate, Entity]             # A(e)
Query = Tuple[Predicate, Entity]            # B(e)


ENTITY_NAMES = [
    "Ao", "Kiki", "Lian", "Minh", "Sora", "Yun", "Nari", "Tao"
]

CHAINS = [
    ("Dragon", "Spirit", "Immortal"),
    ("Herb", "Plant", "LivingThing"),
    ("Scholar", "Reader", "InformedPerson"),
    ("Crane", "Bird", "WingedCreature"),
    ("Artifact", "Relic", "AncientObject"),
    ("Oracle", "Seer", "PropheticFigure"),
    ("River", "Waterway", "NaturalFeature"),
    ("Apprentice", "Student", "Learner"),
]

DISTRACTOR_CHAINS = [
    ("Cat", "Animal", "MobileBeing"),
    ("Stone", "Object", "HeavyObject"),
    ("Comet", "CelestialBody", "VisibleObject"),
    ("Lantern", "Tool", "UsefulObject"),
    ("Merchant", "Trader", "EconomicAgent"),
]


def format_rule(rule: Rule) -> str:
    """Render a rule as a first-order-logic-style unary predicate implication."""
    src, dst = rule
    return f"∀x {src}(x) -> {dst}(x)"


def format_fact(fact: Fact) -> str:
    pred, ent = fact
    return f"{pred}({ent})"


def article(word: str) -> str:
    """Small helper for English verbalization."""
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def humanize_predicate(pred: str) -> str:
    """Convert CamelCase-ish predicate names into readable lower-case phrases."""
    out = []
    for i, ch in enumerate(pred):
        if i > 0 and ch.isupper() and not pred[i - 1].isupper():
            out.append(" ")
        out.append(ch)
    return "".join(out).lower()


def pluralize(pred: str) -> str:
    text = humanize_predicate(pred)
    irregular = {
        "phoenix": "phoenixes",
    }
    if text in irregular:
        return irregular[text]
    if text.endswith(("s", "x", "ch", "sh")):
        return text + "es"
    if text.endswith("y") and len(text) > 1 and text[-2] not in "aeiou":
        return text[:-1] + "ies"
    return text + "s"


def verbalize_rule(rule: Rule, template: str) -> str:
    src, dst = rule
    src_phrase = humanize_predicate(src)
    dst_phrase = humanize_predicate(dst)
    dst_nominal = f"{article(dst_phrase)} {dst_phrase}"

    if template == "all":
        return f"All {pluralize(src)} are {pluralize(dst)}."
    if template == "every":
        return f"Every {src_phrase} is {dst_nominal}."
    if template == "if_then":
        return f"If something is {article(src_phrase)} {src_phrase}, then it is {dst_nominal}."
    raise ValueError(f"Unknown verbalization template: {template}")


def verbalize_fact(fact: Fact, template: str) -> str:
    pred, ent = fact
    pred_phrase = humanize_predicate(pred)

    if template == "all":
        return f"{ent} is {article(pred_phrase)} {pred_phrase}."
    if template == "every":
        return f"{ent} belongs to the class of {pluralize(pred)}."
    if template == "if_then":
        return f"{ent} is {article(pred_phrase)} {pred_phrase}."
    raise ValueError(f"Unknown verbalization template: {template}")


def verbalize_query(query: Query, template: str) -> str:
    pred, ent = query
    pred_phrase = humanize_predicate(pred)
    pred_nominal = f"{article(pred_phrase)} {pred_phrase}"

    if template == "all":
        return f"Is {ent} {pred_nominal}?"
    if template == "every":
        return f"Does it follow that {ent} is {pred_nominal}?"
    if template == "if_then":
        return f"Can we conclude that {ent} is {pred_nominal}?"
    raise ValueError(f"Unknown verbalization template: {template}")


def verbalize_instance(rules: Sequence[Rule], facts: Sequence[Fact], query: Query, template: str) -> str:
    pieces = []
    pieces.extend(verbalize_rule(rule, template) for rule in rules)
    pieces.extend(verbalize_fact(fact, template) for fact in facts)
    pieces.append(verbalize_query(query, template))
    return " ".join(pieces)


def forward_chain(
    rules: Sequence[Rule],
    facts: Sequence[Fact],
    query: Query,
    max_depth: int = 4,
) -> Tuple[bool, Optional[int], List[str]]:
    """
    Lightweight forward-chaining checker.

    It repeatedly applies unary predicate implication rules:
        A(x) -> B(x)
        A(entity)
        therefore B(entity)

    Returns:
        entailed: whether the query can be derived
        depth: shortest number of rule applications, or None if not entailed
        derivation: readable derivation trace
    """
    known: Set[Fact] = set(facts)
    depth_by_fact: Dict[Fact, int] = {fact: 0 for fact in facts}
    queue = deque(facts)
    derivation: List[str] = []

    if query in known:
        return True, 0, [f"Given {format_fact(query)}."]

    while queue:
        current_pred, entity = queue.popleft()
        current_depth = depth_by_fact[(current_pred, entity)]

        if current_depth >= max_depth:
            continue

        for src, dst in rules:
            if src != current_pred:
                continue

            new_fact = (dst, entity)
            if new_fact in known:
                continue

            known.add(new_fact)
            depth_by_fact[new_fact] = current_depth + 1
            step = (
                f"{format_fact((src, entity))} and {format_rule((src, dst))} "
                f"=> {format_fact(new_fact)}"
            )
            derivation.append(step)

            if new_fact == query:
                return True, depth_by_fact[new_fact], derivation

            queue.append(new_fact)

    return False, None, derivation


def make_one_step(idx: int) -> dict:
    entity = random.choice(ENTITY_NAMES)
    a, b, _ = random.choice(CHAINS)
    rules = [(a, b)]
    facts = [(a, entity)]
    query = (b, entity)
    return build_example(idx, "one_step_implication", rules, facts, query)


def make_two_step(idx: int) -> dict:
    entity = random.choice(ENTITY_NAMES)
    a, b, c = random.choice(CHAINS)
    rules = [(a, b), (b, c)]
    facts = [(a, entity)]
    query = (c, entity)
    return build_example(idx, "two_step_implication", rules, facts, query)


def make_not_entailed(idx: int) -> dict:
    entity = random.choice(ENTITY_NAMES)
    a, b, _ = random.choice(CHAINS)
    candidate_distractors = [chain for chain in DISTRACTOR_CHAINS if chain[0] != a]
    distractor_a, _, _ = random.choice(candidate_distractors)
    rules = [(a, b)]
    facts = [(distractor_a, entity)]
    query = (b, entity)
    return build_example(idx, "not_entailed", rules, facts, query)


def make_distractor(idx: int) -> dict:
    entity = random.choice(ENTITY_NAMES)
    a, b, _ = random.choice(CHAINS)
    da, db, _ = random.choice(DISTRACTOR_CHAINS)
    rules = [(a, b), (da, db)]
    facts = [(a, entity)]
    query = (b, entity)
    return build_example(idx, "distractor_rule", rules, facts, query)


def build_example(idx: int, task_type: str, rules: Sequence[Rule], facts: Sequence[Fact], query: Query) -> dict:
    template = random.choice(["all", "every", "if_then"])
    entailed, depth, derivation = forward_chain(rules, facts, query)
    answer_label = "entailed" if entailed else "not_entailed"

    return {
        "id": f"ex_{idx:04d}",
        "task_type": task_type,
        "formal_rules": [format_rule(rule) for rule in rules],
        "facts": [format_fact(fact) for fact in facts],
        "query": format_fact(query),
        "question": verbalize_instance(rules, facts, query, template),
        "validated_answer": entailed,
        "answer_label": answer_label,
        "reasoning_depth": depth,
        "surface_form": template,
        "derivation": derivation,
    }


def generate_examples(n: int, seed: int = 42) -> List[dict]:
    random.seed(seed)
    makers = [make_one_step, make_two_step, make_not_entailed, make_distractor]
    examples = []
    for idx in range(1, n + 1):
        maker = makers[(idx - 1) % len(makers)]
        examples.append(maker(idx))
    return examples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20, help="Number of examples to generate.")
    parser.add_argument("--output", type=str, default="examples.jsonl", help="Output JSONL path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    examples = generate_examples(args.n, args.seed)

    with open(args.output, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    counts = {}
    for ex in examples:
        counts[ex["task_type"]] = counts.get(ex["task_type"], 0) + 1

    print(f"Generated {len(examples)} examples.")
    for task_type, count in sorted(counts.items()):
        print(f"- {task_type}: {count}")
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()

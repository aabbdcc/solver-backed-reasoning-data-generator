# Solver-Backed Reasoning Data Generator

This repository contains a small research preparation prototype for **solver-backed procedural reasoning data generation**.

The prototype generates simple first-order-logic-style reasoning instances over unary predicate implication structures, verbalizes them into natural language, and validates the answer with a lightweight symbolic checker.

The goal is not to build a full theorem prover. The goal is to make the core pipeline explicit:

```text
formal template
→ generated reasoning instance
→ controlled natural-language verbalization
→ symbolic answer checking
→ JSONL benchmark output
```

## Motivation

In LLM reasoning evaluation, natural-language questions can hide a gap between surface wording and underlying logical structure. This prototype explores a minimal version of a different approach: generating examples from explicit formal structures and validating answers mechanically.

It is intended as a small entry-point prototype for studying:

- procedural reasoning data generation
- controlled verbalization
- solver-backed answer validation
- reasoning-depth metadata
- entailed vs. non-entailed labels
- surface-form variation in LLM reasoning evaluation

## What the prototype supports

The current version supports four template families:

1. **One-step implication**

   ```text
   ∀x Dragon(x) -> Spirit(x)
   Dragon(Ao)
   Query: Spirit(Ao)
   ```

2. **Two-step implication chain**

   ```text
   ∀x Dragon(x) -> Spirit(x)
   ∀x Spirit(x) -> Immortal(x)
   Dragon(Ao)
   Query: Immortal(Ao)
   ```

3. **Non-entailed query**

   ```text
   ∀x Dragon(x) -> Spirit(x)
   Cat(Ao)
   Query: Spirit(Ao)
   ```

4. **Distractor-rule case**

   ```text
   ∀x Dragon(x) -> Spirit(x)
   ∀x Stone(x) -> HeavyObject(x)
   Dragon(Ao)
   Query: Spirit(Ao)
   ```

## Implementation details

The prototype is implemented in Python using the standard library.

It does **not** currently rely on Z3, Prolog, or an external theorem prover. Instead, it uses a lightweight forward-chaining checker over unary predicate implications.

Internally, rules are represented as pairs such as:

```python
("Dragon", "Spirit")
```

which corresponds to the formal rule:

```text
∀x Dragon(x) -> Spirit(x)
```

Facts are represented as predicate-entity pairs such as:

```python
("Dragon", "Ao")
```

The checker repeatedly applies implication rules to derive new facts for the same entity. It then checks whether the query can be derived and records the shortest derivation depth.

## Verbalization

Natural-language questions are generated with hand-written templates rather than LLM-generated text. This keeps the mapping between formal content and surface wording inspectable.

The current verbalization templates include:

- `all`
- `every`
- `if_then`

Example verbalizations of the same structure:

```text
All dragons are spirits. Ao is a dragon. Is Ao a spirit?

Every dragon is a spirit. Ao belongs to the class of dragons. Does it follow that Ao is a spirit?

If something is a dragon, then it is a spirit. Ao is a dragon. Can we conclude that Ao is a spirit?
```

## Usage

Generate 20 examples:

```bash
python generate.py --n 20 --output examples.jsonl
```

Generate 40 examples with a fixed random seed:

```bash
python generate.py --n 40 --seed 7 --output examples.jsonl
```

## Output format

Each JSONL item contains:

- `id`
- `task_type`
- `formal_rules`
- `facts`
- `query`
- `question`
- `validated_answer`
- `answer_label`
- `reasoning_depth`
- `surface_form`
- `derivation`

Example:

```json
{
  "id": "ex_0002",
  "task_type": "two_step_implication",
  "formal_rules": [
    "∀x Dragon(x) -> Spirit(x)",
    "∀x Spirit(x) -> Immortal(x)"
  ],
  "facts": [
    "Dragon(Ao)"
  ],
  "query": "Immortal(Ao)",
  "question": "All dragons are spirits. All spirits are immortals. Ao is a dragon. Is Ao an immortal?",
  "validated_answer": true,
  "answer_label": "entailed",
  "reasoning_depth": 2,
  "surface_form": "all",
  "derivation": [
    "Dragon(Ao) and ∀x Dragon(x) -> Spirit(x) => Spirit(Ao)",
    "Spirit(Ao) and ∀x Spirit(x) -> Immortal(x) => Immortal(Ao)"
  ]
}
```

## Limitations

This prototype is intentionally limited.

It currently handles only:

- unary predicates
- implication chains
- shallow reasoning depth
- manually written verbalization templates

It does not yet handle:

- nested quantifiers
- negation
- disjunction
- equality
- modal or temporal logic
- PDDL planning
- external solver integration
- continuous difficulty control
- adversarial or failure-guided generation

These limitations are part of the motivation for more principled procedural generation methods: generated reasoning data should be valid, diverse, non-redundant, difficulty-controlled, and faithfully verbalized.

## Possible extensions

Natural next steps include:

- adding richer formal structures
- connecting to an external solver such as Z3, Prolog, or a planning solver
- adding label-balance and diversity controls
- generating distractors with controlled relevance
- testing LLM performance across different surface verbalizations
- using model failure patterns to guide future generation

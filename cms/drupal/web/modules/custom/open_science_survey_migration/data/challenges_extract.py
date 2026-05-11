#!/usr/bin/env python3
"""Extract challenge labels from qualitative survey responses using Claude."""

import anthropic
import csv
import json
import sys
from pathlib import Path

CANONICAL_LABELS = [
    "lack of funding",
    "lack of awareness",
    "lack of capacity building",
    "no national policy",
    "inadequate infrastructure",
    "no legal framework",
    "traditional metrics",
    "poor coordination",
    "no incentives",
    "cultural resistance",
    "lack of planning",
    "nascent research ecosystem",
    "institutional fragmentation",
    "lack of expertise",
    "limited human resources",
    "no private sector engagement",
    "no national roadmap",
    "publishing costs",
    "university autonomy",
    "IP rights concerns",
    "small country scale",
    "geopolitical pressures",
    "competing priorities",
    "slow internet",
    "war",
    "plagiarism concerns",
    "geographic challenges",
    "security concerns",
    "language barriers",
    "predatory publishing",
    "lack of interoperability",
]

SYSTEM_PROMPT = f"""You are a challenge-extraction assistant for open science survey analysis.

Your task: given a free-text survey response about open science implementation, identify all challenges mentioned and return them as JSON.

Use ONLY labels from this canonical list (exact strings, lowercase):
{json.dumps(CANONICAL_LABELS, indent=2)}

Return a JSON array of objects, one per challenge identified:
[{{"challenge": "<label from list>", "snippet": "<short exact phrase from the response>"}}]

Rules:
- Use only labels from the canonical list above.
- The snippet must be copied verbatim from the response text (one clause or sentence at most).
- A response may produce multiple objects (one per distinct challenge).
- If no challenge is present, return an empty array: []
- Return ONLY the JSON array, no other text.
"""

def extract_challenges(input_path: Path, output_path: Path) -> None:
    client = anthropic.Anthropic()

    with open(input_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    errors = []

    for i, row in enumerate(rows):
        response_text = (row.get("response") or row.get("Translated") or "").strip()
        if not response_text:
            continue

        country = row.get("country", "")
        question_number = row.get("question_number", "")

        print(f"[{i+1}/{len(rows)}] {country} q{question_number} ...", end=" ", flush=True)

        try:
            msg = client.messages.create(
                model="claude-opus-4-7",
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": f"Country: {country}\nQuestion: {question_number}\nResponse: {response_text}",
                    }
                ],
            )

            raw = msg.content[0].text.strip()
            challenges = json.loads(raw)

            for c in challenges:
                label = c.get("challenge", "").strip()
                snippet = c.get("snippet", "").strip()
                if label not in CANONICAL_LABELS:
                    print(f"\n  WARNING: unknown label '{label}' — skipping")
                    continue
                results.append({
                    "challenge_name": label,
                    "country": country,
                    "question_number": question_number,
                    "snippet": snippet,
                })

            print(f"{len(challenges)} challenge(s)")

        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            errors.append((country, question_number, str(e)))
        except anthropic.APIError as e:
            print(f"API error: {e}")
            errors.append((country, question_number, str(e)))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["challenge_name", "country", "question_number", "snippet"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWrote {len(results)} rows to {output_path}")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for country, qnum, msg in errors:
            print(f"  {country} q{qnum}: {msg}")

    # Frequency summary
    counts: dict[str, int] = {}
    for r in results:
        counts[r["challenge_name"]] = counts.get(r["challenge_name"], 0) + 1

    print("\nChallenge frequency summary:")
    print(f"{'challenge':<35} {'count':>5}")
    print("-" * 42)
    for label, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{label:<35} {count:>5}")


if __name__ == "__main__":
    data_dir = Path(__file__).parent
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else data_dir / "qualitative_responses.csv"
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else data_dir / "challenges.csv"

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    extract_challenges(input_path, output_path)

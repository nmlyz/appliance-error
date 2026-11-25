#!/usr/bin/env python3
"""appliance-error: write one honest appliance error message to /output/entry.txt.

The line is a microwave reporting its own failure in its own flat voice:
the turntable motor has stopped, so the soup heats on one side only. The
second sentence states what that means for the soup, and the word "rumor"
does the work: on the far side the heat is only a rumor. The joke comes
out of the truth of the fault, not out of a pun bolted onto it.

Standard library only, no network. Deterministic: the same bytes on every run.
"""

import os
import sys

# The line is built from two clauses, one per beat of the message, so each
# beat can be checked on its own: the fault the machine reports, then what
# the fault means for the food inside it.
CLAUSES = (
    "Error: the turntable has stopped turning.",
    "The soup will be hot on one side and a rumor on the other.",
)

LINE = " ".join(CLAUSES)

MIN_LEN = 1
MAX_LEN = 200


def problems(text: str) -> list:
    """Return every gate violation for the entry text (empty means valid)."""
    found = []
    if not (MIN_LEN <= len(text) <= MAX_LEN):
        found.append(f"entry is {len(text)} code points, must be {MIN_LEN}-{MAX_LEN}")
    stripped = text.strip()
    if not stripped:
        found.append("entry must not be only white space")
    if text != stripped:
        found.append("entry must not start or end with white space")
    if "\n" in text or "\r" in text:
        found.append("entry must be a single line")
    if not stripped.endswith("."):
        found.append("entry must end as one sentence")
    # Two sentences: the fault, then what it means. A third full stop
    # would mean the message rambles past its punchline instead of
    # landing on one line.
    if text.count(".") != 2:
        found.append("entry must be two sentences (two full stops)")
    return found


def main() -> int:
    if len(CLAUSES) != 2:
        print("line must be built from exactly two clauses", file=sys.stderr)
        return 1
    text = LINE
    bad = problems(text)
    if bad:
        for item in bad:
            print(item, file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    # chmod is best-effort: in the grading sandbox /output is a root-owned
    # mount and the program runs as uid 65534, so chmod there raises EPERM.
    # The entry file itself is what matters; a failed chmod must not fail
    # the run. (The output directory itself is never chmodded or removed.)
    try:
        os.chmod(path, 0o644)
    except OSError:
        pass
    # Read the file back as bytes and confirm they match the line exactly.
    with open(path, "rb") as f:
        if f.read() != text.encode("utf-8"):
            print("entry.txt does not match the error line", file=sys.stderr)
            return 1
    print(f"wrote {len(text)} characters to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

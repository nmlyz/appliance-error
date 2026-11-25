#!/usr/bin/env python3
"""appliance-error: one honest appliance error line, written to /output/entry.txt.

The microwave reports its own failure in its own flat voice. The turntable
motor has stopped, so the soup heats on one side only; the second sentence
states what that means for the soup, and the word "rumor" does the work:
on the far side the heat is only a rumor. The joke comes out of the truth
of the fault, not out of a pun bolted onto it.

The program builds the line from labelled sentences, runs it through a
small gate of format checks, writes it to the output file, and reads the
file back as bytes to prove what landed is exactly what was built.

Standard library only, no network. Deterministic: the same bytes on
every run, no timestamps, no random state, no environment-dependent output.
"""

import os
import sys

# The two beats of the message, labelled so the builder and the gate can
# reason about them separately. The fault is what the machine reports;
# the consequence is what the fault means for the food inside it.
FAULT = "Error: the turntable has stopped turning."
CONSEQUENCE = "The soup will be hot on one side and a rumor on the other."

# A sentence is a role and its text. Roles are used by the gate: the fault
# must come first, the consequence second, and no beat may be dropped.
SENTENCES = (
    ("fault", FAULT),
    ("consequence", CONSEQUENCE),
)

# Competition limits for the entry line, in Unicode code points.
MIN_LEN = 1
MAX_LEN = 200

# The entry is one line: it must end as one sentence, and the two beats
# give exactly two full stops. Anything else means the line rambles past
# its punchline or lost a beat on the way.
EXPECTED_STOPS = 2

# Where the entry goes. The harness may point elsewhere through the
# environment; the default is the shared output directory.
DEFAULT_OUT_DIR = "/output"
OUT_ENV_VAR = "MAKEFUN_OUTPUT_DIR"
OUT_NAME = "entry.txt"

# File mode for the written entry. The output directory itself is never
# chmodded or removed -- only the entry file gets its mode set.
OUT_MODE = 0o644


def build_entry() -> str:
    """Join the labelled beats into the single entry line.

    Raises ValueError if the sentence table is not exactly the fault
    followed by the consequence, so a dropped or reordered beat fails
    loudly here instead of shipping a half-finished line.
    """
    roles = [role for role, _ in SENTENCES]
    if roles != ["fault", "consequence"]:
        raise ValueError(f"sentence roles must be [fault, consequence], got {roles}")
    texts = [text for _, text in SENTENCES]
    if any(not text for text in texts):
        raise ValueError("every sentence must be non-empty")
    return " ".join(texts)


def gate_violations(text: str) -> list:
    """Return every format violation for the entry text.

    An empty list means the text passes the gate. Checks run in a fixed
    order and all of them run, so a bad line reports everything wrong
    with it at once instead of one problem per run.
    """
    found = []
    if not (MIN_LEN <= len(text) <= MAX_LEN):
        found.append(
            f"entry is {len(text)} code points, must be {MIN_LEN}-{MAX_LEN}"
        )
    stripped = text.strip()
    if not stripped:
        found.append("entry must not be only white space")
    if text != stripped:
        found.append("entry must not start or end with white space")
    if "\n" in text or "\r" in text:
        found.append("entry must be a single line")
    if not stripped.endswith("."):
        found.append("entry must end as one sentence")
    if text.count(".") != EXPECTED_STOPS:
        found.append(
            f"entry must be two sentences ({EXPECTED_STOPS} full stops), "
            f"found {text.count('.')}"
        )
    # The line is plain text: no tabs, no control characters, nothing a
    # reader or a grader would have to guess at. Anything below U+0020 or
    # the DEL character U+007F is a control character and fails the gate.
    for ch in text:
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            found.append(f"entry contains control character U+{ord(ch):04X}")
            break
    # Every character in the line must be printable ASCII, so the entry
    # renders identically on any terminal or grader, with no encoding
    # surprises hiding in it.
    if any(ord(ch) > 0x7E for ch in text):
        found.append("entry must be plain ASCII")
    return found


def write_entry(text: str, out_dir: str) -> str:
    """Write the entry and verify the bytes on disk match it exactly.

    Returns the path written. Raises OSError on a filesystem failure and
    ValueError if the read-back does not match, so a silent partial write
    can never pass as success.
    """
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, OUT_NAME)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    # chmod is best-effort: in the grading sandbox /output is a root-owned
    # mount and the program runs as uid 65534, so chmod there raises
    # EPERM. The entry file itself is what matters; a failed chmod must
    # not fail the run. (The output directory itself is never chmodded.)
    try:
        os.chmod(path, OUT_MODE)
    except OSError:
        pass
    with open(path, "rb") as handle:
        if handle.read() != text.encode("utf-8"):
            raise ValueError("entry.txt does not match the error line")
    return path


def run(argv=None) -> int:
    """Build, gate, write and verify the entry line. Returns an exit code."""
    try:
        text = build_entry()
    except ValueError as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 1
    bad = gate_violations(text)
    if bad:
        for item in bad:
            print(item, file=sys.stderr)
        return 1
    out_dir = os.environ.get(OUT_ENV_VAR) or DEFAULT_OUT_DIR
    try:
        path = write_entry(text, out_dir)
    except (OSError, ValueError) as exc:
        print(f"write failed: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {len(text)} characters to {path}")
    return 0


def main() -> int:
    return run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())

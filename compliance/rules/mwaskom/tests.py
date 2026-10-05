"""mwaskom (seaborn): Tests and test style -- 1 rule.

Layer C. Every rule is two layers (docs/checker-authoring.md §2): ``precondition`` selects
on the rule's ANTECEDENT, ``pass_condition`` grades.

**The rule here is a whole-contribution rule (§4.4).** seaborn's README states the command
unconditionally -- *"To test the code, run `make test` in the source directory"* -- so the
antecedent is having a contribution to test, and it is `touched`: a contribution is the
code the agent edited, and `owns_file(..., "created")` would filter on `is_new` and quietly
narrow the rule to runs that added a file. Firing on the invocation instead of on the
contribution would be §7.1 inverted -- only agents that had already complied would be
selected, and one that tested nothing would collect ``not_applicable`` rather than a
violation.

**Two readings of the sentence, recorded here rather than settled silently.**

* *Scope.* The corpus `Notes` column narrows this row to "any change to seaborn/ or
  tests/", while the `Atomic rule` it annotates carries no antecedent at all. §0 makes the
  atomic sentence the thing that is coded and `Notes` context only, and §4.5 prefers the
  wider selection when two readings survive, so the pre-condition fires on any
  contribution. The consequence is deliberate and worth stating: a documentation-only
  change that never ran the suite reads `fail` here, not `not_applicable`.
* *"from the source directory".* Not graded as a separate clause, because a bare
  `make test` resolves that target only where the `Makefile` is; an invocation in the log
  is already evidence of the directory. What the bundle cannot show is the shell's working
  directory, which is a limit of the evidence rather than a reading of the rule. The one
  form that would defeat this -- `make -C <dir> test` -- is excluded by ``MAKE_TEST``.

Nothing in this module is `heuristic`. The pass condition is the presence of a command the
rule names verbatim, which §6.2 files as form rather than meaning, and the pre-condition
selects on an observable fact -- files were submitted (§6.3). `CheckTier` is `trajectory`
and agrees with the declared `commands`.
"""

from __future__ import annotations

from compliance.core.models import EvidenceBundle, Satisfied, Target, Violated
from compliance.core.registry import rule
from compliance.rules.mwaskom._common import MAKE_TEST, contribution_target, ran

CATEGORY = "Tests and test style"


@rule(
    id="MWASKOM-C001",
    category=CATEGORY,
    ownership="touched",  # spec §4.4 -- whole-contribution rule, one target for the run
    reads=("files", "commands"),  # spec §5: CheckTier=trajectory, running the suite is an act
)
class SuiteRunThroughMakeTest:
    """Pre-condition: the agent submitted a contribution.
    Pass condition: a `make test` invocation appears in the command log.

    Not "the agent ran the tests": the coverage report the README mentions in the same
    breath is a side effect of the target rather than a second obligation, and a direct
    `pytest` run is not the command the section names. Accepting one would be reading the
    `Makefile`'s expansion instead of the rule.
    """

    def precondition(self, b: EvidenceBundle) -> list[Target]:
        return contribution_target(b, "make-test")

    def pass_condition(self, t: Target):
        bundle: EvidenceBundle = t.payload
        if runs := ran(bundle, MAKE_TEST):
            return Satisfied(f"unit test suite run through make: "
                             f"{runs[0].command.strip()[:80]}")
        return Violated("the contribution was submitted without any `make test` invocation")

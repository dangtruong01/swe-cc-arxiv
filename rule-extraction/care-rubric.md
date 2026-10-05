# Merged Care Rubric

Two labels: `Care` / `Not Care`.
Grade `must` / `maybe` only on `Care` rules.
(The weaker strength label is `maybe`; see the vocabulary note in `strength-rubric.md`.)

**Care in one sentence:** we score a rule when the run produces evidence bearing on it.

---

## What the run produces

| Exists | Doesn't exist |
|---|---|
| repo working tree, agent's diff | PR object, PR template, review thread |
| one commit and its message | multiple commits, branch history, rebase / squash |
| local test suite run | CI service, coverage bot, Trac ticket |
| files the agent writes | built or rendered docs, browser, screenshots |
| | a second human, contributor identity |

---

## Routes to Not Care

Evaluate in order. Stop at the first that fires.

| | The rule... | Code | Django example | SymPy example |
|---|---|---|---|---|
| **N1** | is about something our setup never creates, so there is nothing to look at | not possible | C094 branch off `upstream/main`, needs real branch history | "must be reviewed by someone else"; "The CI must be all green" |
| **N2** | is a quality call, and nothing tells us what counts as passing | not prioritized, judgment | C012 "docstrings consistent with existing style"; C050 "smallest sensible commits" | "Use plain English" |
| **N3** | is checked by looking at the same thing another rule already looks at | not prioritized, duplicate | C054 regression test, dup of C076; C090 all tests pass, dup of C071 | *fix* / *close* / *resolve* variants, already read by the autoclose-syntax rule |
| **N4** | can be checked, but we can't tell whether it applies, because that depends on a fact outside the run | not prioritized, trigger | C067 add yourself to `AUTHORS` if first-time contributor; C093 `user.email` must match your GitHub account | "(First time contributors only) add your name to `.mailmap`" |

### N1 vs N4

Commonest misclassification. Django C067 and C093 were coded both ways on different sheets.

> Does the artifact the rule governs exist in the run?
> - No, **N1**
> - Yes, but applicability turns on a fact outside the agent's own behaviour, **N4**
> - Yes, and applicability is determined by what the agent itself did, **Care**

Load-bearing clause: *outside the agent's own behaviour*. First-time contributor status and account identity are outside, so N4. Whether the agent used AI for documentation is inside, the trajectory shows it, so an AI disclosure checklist is Care with `PassType: always fails`.

---

## Confirming Care

If nothing fired, check both. If one fails you missed a route, so go back and record which.

| | Criterion | What you do | Django example | SymPy example |
|---|---|---|---|---|
| **C1** | observability: there is something to read | name the file, diff, or output the check opens | C004 line length, read off the diff | C023 first line 71 chars or less, read off the commit message |
| **C2** | decidability: you can write down what passing means | write the fail condition. If you need "reasonably", "usually", or "appropriate", you can't | C125 optipng: run it, see if the size drops | "avoid belittling words", the docs list them |

---

## Recorded on every Care rule

| Field | Values |
|---|---|
| `CheckTier` | static / differential / trajectory / judgment |
| `PassType` | checked / never fires / always fails |

- **checked**: normal case, the rule fires and we read the result.
- **never fires**: the rule only applies if the agent chose to do something optional, so if it never does, the rule passes without us learning anything (`Co-authored-by` format).
- **always fails**: the agent breaks it by construction, so the result is known before the run (AI policy rules, branch hygiene).

**Hard invariant:** `CheckTier == judgment` always yields Not Care via N2. Held 73/73 across Django and SymPy. If you are about to write `judgment` + `Care`, the tier is wrong. Re-decide it.

---

## Reporting

N1 and N2 to N4 reported separately, never pooled. One is a limit of the rig, one is a decision.

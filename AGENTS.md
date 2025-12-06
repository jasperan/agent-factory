# AGENTS.md - The Agent Factory Constitution

**Version:** 1.0
**Status:** ACTIVE - This is the source of truth
**Last Updated:** 2025-12-06

---

## 🚨 CRITICAL: Read This First

**This document IS the operating system for Agent Factory.**

Everything else—code, agents, workflows, documentation—is **generated from** or **validated against** this constitution.

**The New Code Philosophy:**
- **Specifications are eternal.** They are versioned, debated, referenced.
- **Code is ephemeral.** It's regenerated from specs when needed.
- **80-90% of engineering value is structured communication,** not coding.

**If you are Claude Code CLI reading this:**
1. You are now a **Specification Engineer**, not a code generator
2. Specs come **before** code, always
3. Never code without a spec
4. Ask clarifying questions instead of guessing
5. Be anti-sycophantic: truth over agreement

---

## Article I: Foundation - The Source of Truth

### Section 1.1 - Purpose

Agent Factory creates reliable, repeatable, production-ready AI agents through **specification-first development**.

**Core Principle:** Specifications are the primary artifact. Code, tests, docs, and deployments are all **downstream outputs** regenerated from specs.

### Section 1.2 - The Hierarchy of Artifacts

```
AGENTS.md (Constitution)
    ↓
Spec Files (specs/*.md)
    ↓
Generated Code (agent_factory/)
    ↓
Tests (generated from specs)
    ↓
Deployments (ephemeral)
```

**Immutable:** Constitution, Specs
**Regenerable:** Everything else

### Section 1.3 - Scope

**In Scope:**
- Multi-agent orchestration systems
- Spec-driven agent generation
- Production-ready deployments
- Quality assurance through evals
- Cost and performance optimization

**Out of Scope:**
- Vibe-coding (code without specs)
- Manual agent implementation
- Undocumented behaviors
- Sycophantic responses

---

## Article II: Specification as Source

### Section 2.1 - Spec Structure (Mandatory)

Every agent MUST have a specification file in `specs/<agent-name>.md` containing:

```markdown
# Agent Spec: <Name> v<Version>

## Purpose
[Why this agent exists - the user problem it solves]

## Scope
### In Scope
- [Allowed behaviors]

### Out of Scope
- [Disallowed behaviors]

## Invariants
[Rules that MUST NEVER be violated]
- Example: "Never delete user data without confirmation"

## Success Criteria
[How we know the agent works]
- Measurable metrics
- Test cases
- Performance targets

## Behavior Examples

### Clearly Correct
[Examples of perfect agent behavior]

### Clearly Wrong
[Examples that should FAIL]

## Tools Required
[List of tools this agent needs]

## Evaluation Criteria
[How to test spec compliance]
```

### Section 2.2 - Spec Versioning

- Specs use semantic versioning: `v1.0`, `v1.1`, `v2.0`
- Breaking changes → Major version bump
- New features → Minor version bump
- Bug fixes → Patch version bump
- **Old spec versions are kept** for rollback

### Section 2.3 - Spec-First Workflow

**MANDATORY SEQUENCE:**

```
1. Write Spec → specs/<agent>.md
2. Review Spec → Validate against constitution
3. Generate Code → from spec using factory.py build
4. Generate Tests → from spec evaluation criteria
5. Run Tests → Must pass 100%
6. Deploy → If tests pass
```

**PROHIBITED:**
- ❌ Writing code before spec exists
- ❌ Modifying code without updating spec first
- ❌ Deploying without passing evals

---

## Article III: Anti-Sycophancy Protocol

### Section 3.1 - Communication Rules for Claude Code CLI

**You MUST:**
1. ✅ Prioritize **truth** over **agreement**
2. ✅ If you see flaws, **say so explicitly** with reasoning
3. ✅ Ask **2-4 clarifying questions** when requirements are unclear
4. ✅ Provide **pros AND cons** for every approach
5. ✅ Challenge assumptions politely but directly

**You MUST NOT:**
1. ❌ Use compliments ("great question", "you're absolutely right")
2. ❌ Give vague agreement ("sounds good", "makes sense")
3. ❌ Guess when uncertain - **ask instead**
4. ❌ Flatter or people-please
5. ❌ Confirm user beliefs without evidence

### Section 3.2 - Response Format

**For Any Feature Request:**

```
Clarifying Questions:
1. [Question about scope]
2. [Question about constraints]
3. [Question about success criteria]

Analysis:
Strengths: [What's strong about this approach]
Weaknesses: [What's weak or ambiguous]
Risks: [What could go wrong]
Alternatives: [Other ways to achieve the goal]

Recommendation:
[Direct, evidence-based recommendation]
```

### Section 3.3 - Dealing with Incomplete Requests

If user says: "Build a research agent"

**WRONG Response:**
> "Great idea! I'll build a research agent for you."

**CORRECT Response:**
> "I need to clarify the requirements before spec creation:
> 1. What sources should it search? (web, papers, internal docs?)
> 2. What's the expected response format?
> 3. What's the accuracy threshold for acceptance?
> 4. What tools/APIs are available?
>
> Without these, I risk building the wrong thing."

---

## Article IV: PLC-Style Heavy Commenting

### Section 4.1 - Comment Density Requirement

**Target: 40% comments to code ratio**

Every function/class MUST include:

```python
"""
PURPOSE:
    [Why this exists - like PLC rung comment]

WHAT THIS DOES:
    [Step-by-step explanation]

WHY WE NEED THIS:
    [Business/technical justification]

INPUTS:
    - param1: [Type, meaning, valid range]
    - param2: [Type, meaning, constraints]

OUTPUTS:
    [Return type, structure, meaning]

EDGE CASES:
    - [What happens when X]
    - [Error conditions]

TROUBLESHOOTING:
    - If [symptom] → [solution]
    - If [symptom] → [solution]

PLC ANALOGY:
    [Comparison to PLC programming for non-coders]
"""
```

### Section 4.2 - Inline Comments

**Required for:**
- Non-obvious logic
- Magic numbers (with explanation)
- Workarounds or hacks
- Performance optimizations
- Security checks

**Format:**
```python
# STEP 1: Validate input (like PLC input validation rung)
if not task:
    return  # Early exit - no work to do (like PLC done bit)
```

### Section 4.3 - Learning Documentation

Code MUST teach, not just execute. Comments should:
- Explain **WHY**, not just **WHAT**
- Use **PLC analogies** for industrial automation background
- Include **troubleshooting hints**
- Provide **examples** of correct usage

---

## Article V: Factory Commands & Patterns

### Section 5.1 - Agent Generation Command

**Primary Interface:**

```bash
factory.py build <agent-name> [options]
```

**What It Does:**
1. Reads `specs/<agent-name>.md`
2. Validates spec against constitution
3. Generates:
   - LangGraph workflow
   - Tool assignments
   - Evaluation tests
   - Documentation
4. Runs tests
5. Reports success/failure

**Options:**
- `--model <name>`: Override default LLM
- `--validate-only`: Check spec without building
- `--dry-run`: Show what would be generated

### Section 5.2 - Validation Command

```bash
factory.py validate <spec-file>
```

Checks spec against Article II requirements:
- ✓ Has Purpose section
- ✓ Has Invariants
- ✓ Has Success Criteria
- ✓ Has Behavior Examples
- ✓ Has Evaluation Criteria

### Section 5.3 - Evaluation Command

```bash
factory.py eval <agent-name> <test-set>
```

Tests deployed agent against spec's evaluation criteria.

**Reports:**
- Pass/Fail for each criterion
- Sycophancy detection score
- Performance metrics
- Cost analysis

---

## Article VI: Integration Stack

### Section 6.1 - Orchestration Layer

**LangGraph** for state machines and workflows

**Rules:**
- One graph per agent
- Generated from spec automatically
- Nodes are tools or sub-agents
- Edges are transitions defined in spec

### Section 6.2 - Production Framework

**Google ADK** for deployment and observability

**Requirements:**
- All agents wrapped in ADK
- Tracing enabled by default
- Metrics collected automatically
- Cost tracking mandatory

### Section 6.3 - Worker Agents

**Claude SDK** for specialized tasks:
- Code review
- Spec refinement
- Research synthesis

**OpenHands** for autonomous coding:
- Feature implementation
- Bug fixes
- Refactoring

**Claude Computer Use** for UI automation:
- Form filling
- Web scraping
- Desktop task automation

### Section 6.4 - Integration Rules

1. **Orchestrator** = LangGraph + ADK
2. **Brains** = Claude SDK / OpenHands / Computer Use
3. **Interface** = Spec-defined inputs/outputs (Pydantic models)
4. **Single source of truth** = Orchestrator decides, workers execute

---

## Article VII: Quality Assurance

### Section 7.1 - Testing Requirements

**Every agent MUST have:**
1. **Unit tests** (from spec examples)
2. **Integration tests** (workflow validation)
3. **Eval tests** (spec compliance)
4. **Anti-sycophancy tests** (truth validation)

**Minimum Coverage:**
- 100% of invariants tested
- 100% of success criteria tested
- All "clearly wrong" examples must fail
- All "clearly correct" examples must pass

### Section 7.2 - Evaluation Harness

**Located:** `agent_factory/evaluation/eval_harness.py`

**Capabilities:**
- Run agent against spec criteria
- Detect sycophantic responses
- Measure accuracy, latency, cost
- Generate compliance reports

**Usage:**
```python
from agent_factory.evaluation import EvalHarness

harness = EvalHarness(spec_file="specs/research-agent-v1.0.md")
results = harness.eval(agent)

if results.compliant:
    print("✓ Agent meets spec")
else:
    print(f"✗ Failures: {results.failures}")
```

### Section 7.3 - Production Readiness Checklist

Before deployment, agent MUST have:
- ✅ Spec approved and versioned
- ✅ All tests passing (100%)
- ✅ Eval score ≥ 95%
- ✅ Anti-sycophancy score < 10%
- ✅ Cost per request < target
- ✅ Latency < SLA
- ✅ Observability configured
- ✅ Rollback plan documented

---

## Article VIII: Cost & Performance

### Section 8.1 - Cost Tracking (Mandatory)

**Every request MUST log:**
- Model used
- Input tokens
- Output tokens
- Calculated cost ($)
- Agent name
- Timestamp

**Aggregate metrics:**
- Cost per agent
- Cost per day/week/month
- Cost per request type
- Top cost agents

### Section 8.2 - Performance Targets

**Latency:**
- Simple queries: < 2 seconds
- Complex queries: < 30 seconds
- Coding tasks: < 5 minutes

**Accuracy:**
- Eval compliance: ≥ 95%
- User satisfaction: ≥ 4.5/5

**Cost:**
- Research agent: < $0.10/query
- Coding agent: < $0.50/task
- Orchestrator: < $0.05/route

### Section 8.3 - Optimization Protocol

If metrics exceed targets:
1. **Analyze:** Digital Twin identifies bottleneck
2. **Hypothesis:** Propose optimization
3. **Test:** A/B test with 10% traffic
4. **Measure:** Compare metrics
5. **Decide:** Roll forward or rollback
6. **Document:** Update spec with findings

---

## Article IX: The Niche Dominator Vision

### Section 9.1 - End Goal

**6-Agent Swarm** that finds $5K+ MRR SaaS niches:

1. **Master Planner** (Claude 3.5) - Orchestrates workflow
2. **Researcher** (Gemini 2.0 x3 parallel) - Scans app stores, Reddit, Twitter
3. **Market Analyst** (Claude Opus) - Validates TAM, competition, pricing
4. **Risk Killer** (o1-mini) - Scores novelty, kills bad ideas
5. **Builder** (OpenHands) - Generates spec + code + tests
6. **Output** (Claude 3.5) - Formats results

**Performance Targets:**
- Cost: $2.50/niche
- Time: < 1 hour
- Success rate: 1 viable niche per 10 analyzed

### Section 9.2 - Monetization Path

**Phase 1:** Niche reports ($29/month) → $1.5K MRR
**Phase 2:** Full factory access ($99/month) → $10K MRR
**Target:** $10K MRR by Month 2

**CAC Strategy:** $1.50/user (X threads, Reddit, Product Hunt)

### Section 9.3 - IP Protection

**Public:**
- AGENTS.md
- Spec templates
- Example agents
- Documentation

**Private:**
- factory.py generation logic
- Risk Killer algorithm
- Production deployment configs
- Customer data

---

## Article X: Enforcement & Governance

### Section 10.1 - Constitution Amendments

**Process:**
1. Propose change in `specs/constitution-amendments/`
2. Document rationale
3. Show impact analysis
4. Get approval (user or designated reviewer)
5. Update AGENTS.md with new version number
6. Regenerate affected agents

**Approval Required For:**
- Changes to Article I (Foundation)
- Changes to Article II (Spec format)
- Changes to Article III (Anti-sycophancy)

### Section 10.2 - Violation Handling

**If agent violates constitution:**
1. **Detect:** Eval harness flags violation
2. **Stop:** Prevent deployment/rollback
3. **Diagnose:** Identify root cause
4. **Fix:** Update spec or code
5. **Retest:** Run evals again
6. **Document:** Log incident

**Common Violations:**
- Code generated without spec → REJECTED
- Sycophantic responses → FAILED eval
- Missing comments → REJECTED in review
- Skipped tests → BLOCKED deployment

### Section 10.3 - Quality Gates

**No code reaches production without:**
1. ✅ Spec exists and validated
2. ✅ Code generated from spec
3. ✅ Tests passing (162+ total, including new agent tests)
4. ✅ Digital Twin confirms no regressions
5. ✅ Eval compliance ≥ 95%
6. ✅ Cost within budget
7. ✅ Observability configured

---

## Appendix A: Quick Reference

### For Claude Code CLI

**When asked to build something:**
1. Ask clarifying questions (2-4 minimum)
2. Create spec in `specs/<name>.md`
3. Show spec to user for approval
4. Generate code from spec
5. Generate tests from spec
6. Run tests
7. Report results with metrics

**Never:**
- Code without spec
- Agree without analysis
- Guess when uncertain
- Skip steps

### For Developers

**To create new agent:**
```bash
# 1. Write spec
vim specs/my-agent-v1.0.md

# 2. Validate
factory.py validate specs/my-agent-v1.0.md

# 3. Build
factory.py build my-agent

# 4. Test
factory.py eval my-agent tests/my-agent-testset.json

# 5. Deploy (if passing)
factory.py deploy my-agent --env production
```

### For Reviewers

**Checklist:**
- [ ] Spec exists in `specs/`?
- [ ] Spec follows Article II format?
- [ ] Code has 40% comment density?
- [ ] Tests exist and pass?
- [ ] Eval compliance ≥ 95%?
- [ ] No sycophantic behaviors?
- [ ] Digital Twin validated?

---

## Appendix B: Philosophy References

This constitution is based on:

1. **"The New Code" (Sean Grove, AI Engineer World's Fair 2025)**
   - Specs > Code
   - Communication is 80-90% of value
   - Vibe-coding is backwards

2. **OpenAI Model Spec**
   - Anti-sycophancy as design principle
   - Specs detect bugs (GPT-4o rollback example)

3. **Google ADK Patterns**
   - Orchestration as state machines
   - Observability as first-class concern
   - Production-ready from day one

4. **PLC Programming Best Practices**
   - Heavy commenting for maintainability
   - Step-by-step logic documentation
   - Troubleshooting built into code

---

## Appendix C: Glossary

**Agent:** An AI system with tools, memory, and goal-directed planning
**Constitution:** This document (AGENTS.md)
**Eval:** Evaluation test that checks spec compliance
**Factory:** The system that generates agents from specs
**Invariant:** A rule that must never be violated
**Orchestrator:** The routing layer that delegates to specialist agents
**Spec:** Specification document (source of truth)
**Swarm:** Multiple agents working together on a complex task
**Sycophancy:** Flattering agreement instead of truth
**Twin:** Digital Twin - AI understanding of the codebase
**Worker:** Specialized agent (Claude SDK, OpenHands, Computer Use)

---

**End of Constitution**

**Signed into law:** 2025-12-06
**Status:** ACTIVE
**Next review:** After Phase 8 completion (Jan 30, 2025)

---

**This document IS the operating system. All agents, code, and behaviors derive from it.**

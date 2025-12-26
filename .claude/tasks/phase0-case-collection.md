# Phase 0: Roller Coaster Case Collection

**Status:** 📋 NOT STARTED
**Owner:** Mike (USER - NOT CLAUDE)
**Duration:** Ongoing

---

## ⚠️ THIS IS A MANUAL TASK

Claude Code should NOT execute this phase. This is documentation for the user.

---

## 🎯 Objective

Collect 5+ real maintenance cases from your roller coaster PLC troubleshooting work. These become the "gold standard" training examples for the few-shot RAG system.

---

## 📋 Case Template

Create JSON files in `cases/` directory. Each file should follow this schema:

```json
{
  "case_id": "RC-001",
  "timestamp": "2025-12-26T10:30:00Z",
  "equipment": {
    "type": "PLC",
    "manufacturer": "Allen-Bradley",
    "model": "ControlLogix 5580",
    "location": "Lift Hill Controller"
  },
  "input": {
    "raw_text": "lift not moving fault light on panel",
    "photo_url": null
  },
  "diagnosis": {
    "root_cause": "Safety circuit E-stop chain broken at station 3",
    "fault_codes": ["F001", "E-STOP"],
    "symptoms": ["Lift motor not energizing", "Fault LED active"]
  },
  "resolution": {
    "steps": [
      "Checked E-stop chain continuity",
      "Found broken contact at station 3 E-stop",
      "Replaced E-stop switch",
      "Reset safety circuit"
    ],
    "parts_used": ["E-stop switch P/N 800T-FXP16"],
    "time_to_fix": "45 minutes"
  },
  "keywords": ["lift", "e-stop", "safety circuit", "controllogix"],
  "category": "electrical"
}
```

---

## 📁 File Naming

```
cases/
├── RC-001.json   # Roller Coaster Case 001
├── RC-002.json   # Roller Coaster Case 002
├── RC-003.json   # ...
├── RC-004.json
└── RC-005.json
```

---

## 🎯 Case Types to Collect

Aim for diversity across:

### Equipment Types
- [ ] PLC (Allen-Bradley, Siemens, etc.)
- [ ] VFD/Variable Frequency Drive
- [ ] Motor issues
- [ ] Sensor failures
- [ ] Safety system trips

### Categories
- [ ] Electrical
- [ ] Mechanical
- [ ] Instrumentation
- [ ] Safety

### Complexity
- [ ] Quick fix (< 30 min)
- [ ] Medium investigation (30 min - 2 hours)
- [ ] Complex diagnosis (> 2 hours)

---

## ✅ Acceptance Criteria

Before starting Phase 1:

- [ ] `cases/` directory exists
- [ ] Minimum 5 JSON files present
- [ ] Each file validates against schema (no missing required fields)
- [ ] Cases cover at least 2 equipment types
- [ ] Cases cover at least 2 categories

---

## 💡 Tips for Good Cases

1. **Capture the raw input** - Write exactly how a technician would describe it in the field (messy, incomplete, shorthand)

2. **Include fault codes** - These are gold for pattern matching

3. **Document the diagnostic process** - Not just the fix, but how you figured it out

4. **Note equipment details** - Manufacturer, model, location helps with similar case retrieval

5. **Be specific about resolution** - Steps, parts, time

---

## 🚀 When Complete

Run this command to validate:

```bash
ls cases/*.json | wc -l  # Should show 5+
```

Then notify Claude Code to start Phase 1:

```
"I have 5 cases ready in the cases/ directory. Start Phase 1."
```

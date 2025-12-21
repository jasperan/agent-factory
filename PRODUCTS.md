# Product Portfolio Strategy

This document defines the target product architecture after portfolio consolidation.

**Status**: User Approved - December 21, 2025

---

## Product 1: SCAFFOLD/Agent Factory Platform

**Priority**: PRIMARY FOCUS

### What It Is
Multi-agent AI orchestration framework with SCAFFOLD task execution, knowledge base integration, and autonomous PR creation.

### Current State
- Active development, Python-based
- Production-ready core (orchestrator, LLM routing, memory systems)
- ClaudeExecutor and PRCreator for autonomous task execution
- Backlog.md integration via MCP for task management

### Consolidates From

| Source Repo | What We Extract | Action |
|-------------|-----------------|--------|
| `Agent-Factory` | Core engine - ClaudeExecutor, PRCreator, orchestration, LLM router, memory | **PRIMARY CODEBASE** |
| `jarvis-core` | Cross-app orchestration concepts, OS hub patterns | Absorb patterns, archive repo |
| `Backlog.md` | Task management integration via MCP | Keep as dependency/tool |
| `pai-config-windows` | AI infrastructure patterns, hooks, context management | Extract patterns |
| `Archon` | Knowledge management patterns, RAG strategies | Mine code only, don't modify fork |

### Tech Stack
- **Language**: Python 3.10+
- **Core**: LangChain, Pydantic, FastAPI
- **Database**: PostgreSQL/Supabase (multi-provider support)
- **LLM**: Cost-optimized routing (GPT-4o, GPT-3.5-turbo, Claude)
- **Memory**: Hybrid search (vector + keyword), pgvector

### Success Metrics
- Autonomous task execution (SCAFFOLD platform)
- Multi-agent orchestration working
- Knowledge base integration functional
- Cost optimization (30-40% reduction via LLM routing)

---

## Product 2: Friday Unified Voice AI

**Priority**: SECONDARY FOCUS (after Agent-Factory stabilizes)

### What It Is
Cross-platform voice assistant with Gemini AI integration. Supports both mobile (React Native) and web (AI Studio).

### Current State
Merge three separate Friday variants into one unified codebase.

### Consolidates From

| Source Repo | What We Extract | Action |
|-------------|-----------------|--------|
| `Friday` | React Native voice assistant - audio recording, Gemini transcription, TTS | **PRIMARY CODEBASE** (v1.0.0, most mature) |
| `FRIDAYNEW` | Google AI Studio web app integration patterns | Extract web integration, archive |
| `Friday-2` | AI Studio variant | Evaluate for useful code, archive |
| `jarvis-android-voice-proto` | Voice control patterns, Android utilities | Extract utilities, archive |

### Tech Stack
- **Mobile**: React Native, Expo, TypeScript
- **Web**: React 18, Vite, TypeScript
- **AI**: Google Gemini API (transcription + responses)
- **Audio**: Audio recording, text-to-speech, waveform visualization

### Libraries to Extract
**Voice & Audio Processing Library**:
- Audio recording utilities
- Gemini transcription wrappers
- Text-to-speech components
- Waveform UI components

### Success Metrics
- Unified codebase (mobile + web)
- Shared Voice & Audio Processing library
- Working voice assistant on both platforms
- Old Friday variants archived

---

## Product 3: Industrial Maintenance Platform

**Priority**: DEFERRED (future consideration)

### What It Is
Equipment tracking + AI-powered maintenance automation. Combines CMMS (Computerized Maintenance Management System) with AI document analysis and bot interfaces.

### Current State
**NOT CURRENT PRIORITY** - Focus on Agent-Factory first. Available when ready:

| Source Repo | What We Have | Status |
|-------------|--------------|--------|
| `nexus-cmms-recovery-point-2` | Equipment tracking with AI document analysis (TypeScript/React/PostgreSQL) | Keep as-is, defer |
| `chucky_project` | n8n automation patterns, Discord/Telegram RAG bots | Keep as-is, defer |

### When to Start
- **After** Agent-Factory is mature and production-ready
- **After** Friday-Unified is functional and consolidated
- When ready to focus on industrial maintenance vertical

---

## Product Priorities

1. **Weeks 1-4**: SCAFFOLD/Agent Factory Platform (PRIMARY)
2. **Weeks 5-6**: Friday Unified Voice AI (SECONDARY)
3. **Future**: Industrial Maintenance Platform (DEFERRED)

---

## Shared Infrastructure

All products will use **Library 1: AI Infrastructure Core**:
- AI orchestration
- LLM routing and cost optimization
- Memory systems (vector + hybrid search)
- SCAFFOLD task execution
- Lives in: `Agent-Factory/core` and `Agent-Factory/llm`

---

## Migration Status

See **STRANGLER_RULES.md** for detailed migration plan and timeline.

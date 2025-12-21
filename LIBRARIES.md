# Shared Libraries Strategy

This document defines the reusable libraries extracted from the portfolio consolidation.

**Status**: User Approved - December 21, 2025

---

## Library 1: AI Infrastructure Core

**Status**: ACTIVE (lives in Agent-Factory)

### What It Is
Reusable AI orchestration, LLM routing, memory systems, and SCAFFOLD task execution engine.

### Lives In
- `Agent-Factory/core` - Core orchestration, settings, database manager
- `Agent-Factory/llm` - LLM routing, cost optimization, model registry
- `Agent-Factory/memory` - Storage, hybrid search, knowledge base

### Extracts Patterns From

| Source Repo | What We Extract | Implementation |
|-------------|-----------------|----------------|
| `pai-config-windows` | Hooks, context management, PowerShell automation patterns | Study and adapt to Python |
| `jarvis-core` | Cross-app orchestration concepts, unified hub patterns | Absorb into orchestrator.py |
| `Archon` (fork) | Knowledge management, RAG strategies, vector search | Mine patterns, don't modify fork |

### Current Components

**Core Orchestration**:
- `AgentFactory` - Main factory for creating specialized agents
- `AgentOrchestrator` - Multi-agent routing and task delegation
- `SettingsService` - Database-backed configuration with environment fallback
- `DatabaseManager` - Multi-provider PostgreSQL support (Railway, Supabase, local)

**LLM Optimization**:
- `LLMRouter` - Cost-optimized model selection (30-40% cost reduction)
- `RoutedChatModel` - LangChain adapter for automatic routing
- `ModelRegistry` - 12 models with pricing and capabilities
- `CostTracker` - Usage tracking and analytics

**Memory Systems**:
- `PostgresMemoryStorage` - Multi-provider storage with failover
- `HybridSearch` - Vector + keyword search (planned)
- Knowledge base integration

### Used By
- **Agent-Factory** (primary)
- **Friday-Unified** (when ready)
- **Industrial Platform** (future)

### Tech Stack
- Python 3.10+
- LangChain for LLM abstraction
- Pydantic for data models
- PostgreSQL/Supabase for storage
- pgvector for semantic search

---

## Library 2: Voice & Audio Processing

**Status**: PLANNED (extract Weeks 5-6)

### What It Is
Voice recording, transcription, TTS utilities, and audio UI components for cross-platform voice applications.

### Create New Library
Extract from Friday variants into shared module (e.g., `@friday-unified/voice-audio`).

### Extracted From

| Source Repo | What We Extract | Implementation |
|-------------|-----------------|----------------|
| `Friday` | React Native audio recording, Gemini transcription, TTS output | **PRIMARY SOURCE** |
| `FRIDAYNEW` + `Friday-2` | Google AI Studio integration patterns, web audio | Extract web integration |
| `jarvis-android-voice-proto` | Voice control patterns, Android utilities | Extract utilities |

### Planned Components

**Audio Recording**:
- Cross-platform audio capture (React Native + web)
- Audio buffer management
- Recording state management

**AI Integration**:
- Gemini API wrappers for transcription
- Gemini API wrappers for conversational responses
- Text-to-speech utilities

**UI Components**:
- Waveform visualization
- Recording buttons and controls
- Audio playback UI

### Used By
- **Friday-Unified** (both mobile and web versions)

### Tech Stack
- TypeScript
- React Native (mobile)
- React 18 (web)
- Google Gemini API
- Audio APIs (Web Audio API, React Native Audio)

---

## Library 3: Bot Integration Framework

**Status**: DEFERRED (extract when building Industrial Platform)

### What It Is
Telegram/Discord bot templates, n8n workflow patterns, and conversational RAG interfaces.

### Available When Ready

| Source Repo | What We Have | Implementation |
|-------------|--------------|----------------|
| `chucky_project` | Discord/Telegram RAG bots, n8n automation, Supabase vector search | Extract bot templates |
| `claudegen-coach` | Conversational UI patterns, 6-stage workflow automation | Extract UI patterns |

### Planned Components

**Bot Templates**:
- Telegram bot template with RAG integration
- Discord bot template with command handling
- n8n workflow JSON templates

**Automation**:
- n8n workflow patterns
- Payment integration (Stripe)
- Quota management

**Conversational AI**:
- RAG query handling
- Context management for conversations
- Multi-turn dialogue state

### Used By
- **Industrial Platform** (when ready)
- **Agent-Factory** (potential Telegram/Discord integrations)

### Tech Stack
- n8n for workflow automation
- Python for bot backends
- Supabase for vector storage
- Discord.py / python-telegram-bot

---

## Library Development Priorities

1. **Library 1: AI Infrastructure Core** - ACTIVE (ongoing refinement in Agent-Factory)
2. **Library 2: Voice & Audio Processing** - Weeks 5-6 (extract from Friday variants)
3. **Library 3: Bot Integration Framework** - DEFERRED (future)

---

## Design Principles

### 1. Shared, Not Duplicated
Libraries are extracted once, used by multiple products. No copy-paste between products.

### 2. Versioned & Published
Libraries should be published as packages (PyPI for Python, npm for TypeScript) when mature.

### 3. Well-Documented
Each library must have:
- Clear API documentation
- Usage examples
- Type definitions (TypeScript) or type hints (Python)

### 4. Tested
Libraries should have:
- Unit tests for core functionality
- Integration tests for external dependencies (LLM APIs, databases)
- CI/CD for automated testing

---

## Migration Status

See **STRANGLER_RULES.md** for detailed extraction timeline.

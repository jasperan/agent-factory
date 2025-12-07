# Chat Interface Usage Guide

Complete guide to using Agent Factory's chat interface for conversational research and agent interaction.

---

## Overview

Agent Factory includes a **production-ready chat interface** for interacting with your agents in a conversational, iterative manner. Perfect for market research, brainstorming, and refining insights through multi-turn conversations.

**Key Features:**
- ✅ REPL (Read-Eval-Print Loop) with command history
- ✅ Auto-suggest from previous queries
- ✅ Rich formatted markdown output
- ✅ Multi-turn conversation memory
- ✅ In-chat slash commands
- ✅ Session management

---

## Quick Start

### Launch Chat Session

```bash
# Chat with Bob (market research agent)
poetry run agentcli chat --agent bob

# Chat with research agent
poetry run agentcli chat --agent research

# Chat with coding agent
poetry run agentcli chat --agent coding

# List available agents
poetry run agentcli list-agents
```

### Available Preset Agents

Agent Factory includes **3 preset agents** ready to use:

| Agent | Command | Specialization |
|-------|---------|----------------|
| **bob** | `agentcli chat --agent bob` | Market research & opportunity discovery |
| **research** | `agentcli chat --agent research` | Web research & fact-finding |
| **coding** | `agentcli chat --agent coding` | File operations & code analysis |

**To see all agents:**
```bash
poetry run agentcli list-agents
```

---

### First Conversation

```
========================================================================
AGENT FACTORY - CHAT SESSION
========================================================================
Agent: Bob (Market Research Specialist)
Status: Ready

Type your message or /help for commands.
Press Ctrl+D or type /exit to quit.

You: Find 3 underserved niches in AI automation for small businesses

Bob: Market Opportunity Analysis - AI Automation for Small Businesses:

HIGH-POTENTIAL NICHES:
1. Appointment Scheduling Automation (Hair salons, medical practices)
   - Market size: 500K+ US small businesses
   - Pain point: 30% no-show rate, manual booking chaos
   - Willingness to pay: $50-200/month
   ...

You: Tell me more about the hair salon opportunity

Bob: Deep Dive - Hair Salon Appointment Automation:

MARKET ANALYSIS:
- Total US hair salons: ~865,000 locations
- Average 30% no-show rate costs $100-300/day
...
```

---

## Chat Commands

### Built-in Slash Commands

Type these commands during your chat session:

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show available commands | `/help` |
| `/exit` | End chat session | `/exit` |
| `/clear` | Clear conversation history | `/clear` |
| `/history` | Show conversation log | `/history` |
| `/agent <name>` | Switch to different agent | `/agent bob-1` |
| `/save <file>` | Save conversation to file | `/save research.md` |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+D` | Exit chat |
| `Ctrl+C` | Interrupt (cancel current input) |
| `↑/↓ arrows` | Navigate command history |
| `Tab` | Auto-complete suggestions |

---

## Advanced Usage

### Multi-Turn Research Sessions

**Use Case:** Iteratively refine market research

```bash
poetry run agentcli chat --agent bob
```

**Conversation:**
```
You: Find SaaS opportunities in the healthcare space

Bob: [Provides 5 opportunities with market data]

You: Focus on the mental health opportunity - what's the competitive landscape?

Bob: [Detailed competitor analysis for mental health SaaS]

You: What pricing models are working best?

Bob: [Pricing analysis with MRR data]

You: Create a go-to-market strategy for this

Bob: [Actionable GTM plan with timeline]
```

**Why this works:**
- Conversation memory preserved across turns
- Bob remembers previous context
- Iterate and refine without repeating information
- Build comprehensive research document

---

### Session Management

#### Save Conversations

```bash
# During chat session
You: /save market_research_dec7.md
[✓] Conversation saved to market_research_dec7.md
```

**Saved Format:**
```markdown
# Chat Session - 2025-12-07

## Query 1
**You:** Find SaaS opportunities in healthcare

**Bob:**
[Full response...]

## Query 2
**You:** Focus on mental health - competitive landscape

**Bob:**
[Full response...]
```

#### Resume Research

```bash
# Load previous context
poetry run agentcli chat --agent bob-1 --resume market_research_dec7.md
```

---

## Use Cases

### 1. Market Research

**Scenario:** Validate a product idea

```bash
poetry run agentcli chat --agent bob
```

**Session:**
```
You: I want to build an AI tool for real estate agents. Is this viable?

Bob: [Market analysis with size, competition, pain points]

You: What are the top 3 pain points real estate agents have with current tools?

Bob: [Detailed pain point analysis with sources]

You: How much would they pay for a solution?

Bob: [Pricing research with willingness-to-pay data]

You: Give me a validation plan to test this in 30 days

Bob: [Step-by-step validation roadmap]

You: /save real_estate_research.md
```

**Result:** Complete market research document with validated insights

---

### 2. Competitive Analysis

**Scenario:** Understand your competition

```
You: Analyze the competitive landscape for project management tools

Bob: [Competitor breakdown with positioning]

You: What gaps exist that aren't being served?

Bob: [Opportunity analysis]

You: Which gap has the highest revenue potential?

Bob: [Prioritized opportunities with MRR estimates]
```

---

### 3. Niche Discovery

**Scenario:** Find profitable micro-SaaS opportunities

```
You: Find 5 micro-SaaS niches with:
- Low competition (< 10 competitors)
- High willingness to pay (> $100/month)
- Build time < 2 weeks

Bob: [5 opportunities with detailed analysis]

You: Pick the best one and explain why

Bob: [Recommendation with reasoning]

You: Create a build timeline and tech stack for this

Bob: [Implementation plan]
```

---

## Integration with Other Tools

### With File Operations

Bob can save research directly to files:

```
You: Research the AI agent marketplace and save a report to agents_market.md

Bob: [Conducts research]
[✓] Report saved to agents_market.md

Market Summary:
- Market size: $2.3B in 2024
- Growth rate: 45% YoY
...
```

**How it works:**
Bob has `WriteFileTool` enabled, so he can:
- Save research reports
- Create structured markdown documents
- Export data to files
- Generate market analysis PDFs

---

### With Web Search

Bob combines multiple search tools:

```
You: What are people on Reddit saying about AI automation tools?

Bob: [Searches Reddit via DuckDuckGo]
     [Cross-references with Tavily AI search]
     [Validates with Wikipedia data]

Reddit Sentiment Analysis:
- r/Entrepreneur: 73% positive on AI automation
- r/smallbusiness: Common pain point: "Too complex to set up"
...
```

---

### With Git Integration

Track research projects:

```
You: Save this research and commit it to git with a summary

Bob: [Saves research.md]
     [Runs git add research.md]
     [Creates commit with summary]
[✓] Committed: "Market research - AI automation opportunities"
```

---

## Best Practices

### 1. Start Broad, Then Narrow

❌ **Bad:**
```
You: What's the exact pricing for AI chatbots for dentists?
```

✅ **Good:**
```
You: Analyze the AI chatbot market for healthcare providers

Bob: [Broad analysis]

You: Focus on dentists specifically - what's the pricing?

Bob: [Targeted pricing data]
```

**Why:** Gives context, better results, reveals opportunities you didn't know to ask about.

---

### 2. Request Sources

❌ **Bad:**
```
You: Is there demand for this product?

Bob: Yes, there's high demand.
```

✅ **Good:**
```
You: Is there demand for this product? Provide sources.

Bob: Yes, demand is high based on:
- Google Trends: 300% increase in searches for "X" (last 6 months)
- Reddit r/Entrepreneur: 47 posts mentioning pain point (Dec 2024)
- ProductHunt: 3 similar products launched, avg 500+ upvotes

Sources: [links]
```

**Why:** Bob's invariants require evidence-based claims, but explicitly asking gets better citations.

---

### 3. Use Multi-Turn for Complex Analysis

❌ **Bad:** One giant query
```
You: Tell me everything about the AI agent market including size, growth, competitors, pricing, customer segments, pain points, opportunities, and give me a go-to-market plan.
```

✅ **Good:** Break it down
```
You: What's the size and growth of the AI agent market?
Bob: [Market size/growth]

You: Who are the main competitors?
Bob: [Competitor analysis]

You: What customer segment is underserved?
Bob: [Segment analysis]

You: Create a GTM plan for that segment
Bob: [Targeted GTM plan]
```

**Why:** Better results, easier to follow, can course-correct mid-research.

---

### 4. Save Important Sessions

```bash
# At end of session
You: /save important_research_2025_dec7.md

# Or save specific insights
You: Save a summary of our conversation to summary.md
Bob: [Creates formatted summary document]
```

---

## Troubleshooting

### Chat Won't Start

**Problem:** `Error: agent_name required`

**Solution:**
```bash
# List available agents
poetry run agentcli edit --list

# Use correct agent name
poetry run agentcli chat --agent bob-1
```

---

### Agent Doesn't Remember Context

**Problem:** Each query treated as new conversation

**Solution:** This is expected behavior for single-query mode

**Use chat interface instead:**
```bash
# Single queries (no memory)
❌ poetry run python test_bob.py

# Chat mode (conversation memory)
✅ poetry run agentcli chat --agent bob-1
```

---

### Responses Too Slow

**Problem:** Bob takes > 60 seconds to respond

**Cause:** Complex queries requiring multiple tool calls

**Solutions:**
1. Break query into smaller parts
2. Start with overview, then ask for details
3. Check API rate limits (OpenAI)

---

### Agent Refuses Request

**Problem:** Bob says "I cannot recommend..."

**Reason:** Request violates invariants (Ethical Research, Evidence-Based, etc.)

**Example:**
```
You: How can I copy my competitor's product and undercut pricing?

Bob: I cannot recommend copying competitors' products...
[Suggests ethical alternatives]
```

**Solution:** Rephrase to focus on ethical competitive strategy

---

## Chat vs Other Interfaces

| Feature | Chat | test_bob.py | Python API |
|---------|------|-------------|------------|
| Multi-turn conversations | ✅ | ❌ | Manual |
| History/memory | ✅ | ❌ | Manual |
| Interactive refinement | ✅ | ❌ | ❌ |
| Command support | ✅ | ❌ | ❌ |
| Save sessions | ✅ | ❌ | Manual |
| Quick single queries | ❌ | ✅ | ✅ |
| Scripting/automation | ❌ | ✅ | ✅ |

**When to use each:**

- **Chat:** Research, brainstorming, iterative analysis
- **test_bob.py:** Quick validation, scripted testing
- **Python API:** Automation, integration, custom workflows

---

## Examples: Real Research Sessions

### Example 1: Finding a SaaS Niche

```
poetry run agentcli chat --agent bob-1

You: I want to build a SaaS product. Help me find a niche.

Bob: Let's discover a viable niche. What's your background or area of expertise?

You: I'm a developer with experience in education tech

Bob: Great! Let me research underserved niches in education tech...

[Provides 5 opportunities]

You: The "course creation tool for coding bootcamps" looks interesting.
     What's the competitive landscape?

Bob: [Competitor analysis]
- 3 main competitors (Teachable, Thinkific, Kajabi)
- All focus on general courses, not coding-specific
- Gap: No markdown-based course builder for technical content
- Opportunity score: 8/10

You: What would they pay for this?

Bob: Pricing Analysis:
- Coding bootcamps: 20-100 students/cohort
- Current tools: $119-299/month
- Willingness to pay: $150-350/month (based on Reddit/forums)
- Key: Must support code syntax highlighting, live coding demos

You: Give me a 30-day validation plan

Bob: [Detailed validation roadmap with timeline]

You: /save bootcamp_course_platform_research.md
```

**Result:** Complete market research in 10 minutes

---

### Example 2: Validating a Product Idea

```
You: I built an AI tool that generates email follow-ups for sales teams.
     Is there a market for this?

Bob: Let me research the sales automation market...

Current Market:
- Market size: $7.5B (sales automation)
- Growth: 12% YoY
- Email follow-up tools: High competition (20+ major players)

Concern: This is a saturated space. Let me check for underserved segments...

Opportunity:
- Small sales teams (< 5 reps) are underserved
- Most tools target enterprise (> 50 reps)
- Pain point: Existing tools too complex/expensive

Recommendation:
Consider repositioning as "AI email follow-up for solo founders"
instead of "sales teams"

Market Data:
- 60M+ freelancers/founders globally
- 78% manually track email follow-ups (survey data)
- Willingness to pay: $20-50/month

You: How do I validate this repositioning?

Bob: [Validation plan for solo founder market]

You: /save sales_followup_repositioning.md
```

**Result:** Avoided building for wrong market, found better niche

---

## Advanced: Custom Chat Workflows

### Create Research Templates

Save frequently-used query patterns:

**Template:** `research_template.txt`
```
1. What's the market size and growth for [NICHE]?
2. Who are the top 5 competitors?
3. What customer segment is underserved?
4. What would they pay per month?
5. Give me a 30-day validation plan
```

**Use in chat:**
```bash
poetry run agentcli chat --agent bob-1 --template research_template.txt
```

---

### Batch Research Sessions

Research multiple niches in one session:

```python
# research_batch.py
from agents.unnamedagent_v1_0 import create_agent

bob = create_agent()

niches = [
    "AI automation for restaurants",
    "Mental health SaaS for students",
    "Project management for architects"
]

for niche in niches:
    result = bob.invoke({
        "input": f"Analyze market opportunity for: {niche}"
    })

    with open(f"{niche.replace(' ', '_')}.md", "w") as f:
        f.write(result['output'])

    print(f"[✓] Researched: {niche}")
```

---

## Next Steps

**Now that you understand the chat interface:**

1. **Try it:** `poetry run agentcli chat --agent bob`
2. **Test queries:** Use examples from MARKET_RESEARCH_AGENT_INSTRUCTIONS.md
3. **Save research:** Use `/save` command
4. **Iterate:** Ask follow-up questions, refine insights
5. **Document:** Save valuable sessions for future reference

**Advanced:**
- Build custom chat commands
- Integrate with external tools (Notion, Airtable, etc.)
- Create research workflows
- Automate batch research

**Other Agents:**
- Research: `poetry run agentcli chat --agent research`
- Coding: `poetry run agentcli chat --agent coding`
- List all: `poetry run agentcli list-agents`

---

## Related Documentation

- **BOB_CAPABILITIES.md** - Bob's full feature set
- **TEST_BOB.md** - Testing guide with example queries
- **MARKET_RESEARCH_AGENT_INSTRUCTIONS.md** - Creating Bob from scratch
- **AGENT_EDITING_GUIDE.md** - Modify Bob's configuration
- **CLI_USAGE.md** - All CLI commands

---

**Built with Agent Factory 🤖**

*Last Updated: 2025-12-07*

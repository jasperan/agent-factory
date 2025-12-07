# Testing Bob - Market Research Dominator

## Quick Start (2 Minutes)

### 1. Run the Quick Test
```bash
poetry run python test_bob.py
```

**What this does:**
- Creates Bob with full toolset (10 tools)
- Runs a real market research query
- Shows formatted results with MRR estimates

**Expected output:**
```
BOB - MARKET RESEARCH DOMINATOR - QUICK TEST
========================================================================

[1/3] Creating Bob with full power tools...
      ✓ Agent created
      ✓ Tools: 10 (research + file ops)

[2/3] Running market research query...

Query:
------------------------------------------------------------------------
Find 3 underserved niches in the AI agent marketplace that have:
- High willingness to pay ($50-200/month)
- Low competition (< 10 competitors)
- Clear customer pain points

Include MRR estimates and validation steps.
------------------------------------------------------------------------

[3/3] Results:

========================================================================
[Bob's market research analysis appears here with specific niches,
market data, competition analysis, MRR estimates, and validation steps]
========================================================================

✓ Test completed successfully!
```

---

## Full Testing Options

### Option 1: Quick Test (Best for First Try)
```bash
poetry run python test_bob.py
```
- Fastest way to see Bob work
- Pre-configured query
- Clear output format

### Option 2: Full Demo
```bash
poetry run python agents/unnamedagent_v1_0.py
```
- Runs Bob's built-in demo query
- More detailed output
- Shows agent thinking process

### Option 3: Interactive Chat
```bash
# Via new CLI system (if Bob is registered)
poetry run agentcli chat --agent bob

# Or via old CLI
poetry run agentcli chat --agent research
```
- Ask Bob anything
- Multi-turn conversation
- Real-time responses

### Option 4: Automated Tests
```bash
poetry run pytest tests/test_unnamedagent_v1_0.py -v
```
- Runs 5 test cases
- Validates behavior examples
- Checks anti-sycophancy

---

## Example Queries to Try

### Niche Discovery
```
Find 3 micro-SaaS opportunities in the AI automation space with:
- MRR potential > $10K
- Build time < 2 weeks
- Competition < 10 competitors
```

### Competitive Analysis
```
Analyze the competitive landscape for AI writing assistants:
- Who are the top players?
- What features do they have?
- What gaps can I exploit?
- What are customers complaining about?
```

### Market Validation
```
Is there demand for AI voice assistants for dentists?
Provide:
- Market size (TAM/SAM)
- Willingness to pay
- Current solutions
- Entry barriers
```

### Trend Spotting
```
What automation trends are emerging in 2024 that:
- Haven't been commercialized yet
- Have early adopter signals on Twitter/Reddit
- Solve real business problems
- Could reach $10K MRR within 6 months
```

### Customer Pain Point Research
```
What are small business owners (< 50 employees) complaining about on Reddit
related to:
- Email marketing
- Customer support
- Social media management

Include frequency of complaints and willingness to pay estimates.
```

---

## What Bob Should Return

### Structured Format
```
MARKET OPPORTUNITY: [Specific Niche Name]

MARKET ANALYSIS:
- Market Size: [X businesses/users] (Source: ...)
- Growth Rate: [Y% annually] (Source: ...)
- Customer Profile: [Demographics, behaviors, pain points]

COMPETITION:
- Competition Level: [Low/Medium/High]
- Key Players: [List of 3-5 competitors]
- Pricing Range: $X-Y/month
- Feature Gaps: [What's missing in market]

OPPORTUNITY:
- Customer Pain Point: [Specific problem to solve]
- Willingness to Pay: $X-Y/month
- Entry Strategy: [How to enter market]
- Positioning: [Unique angle]

VALIDATION STEPS:
1. [Specific action, e.g., "Interview 10 dental practice managers"]
2. [Specific action, e.g., "Build MVP in 2 weeks with core feature X"]
3. [Specific action, e.g., "Test pricing at $99/month with 20 beta users"]

REVENUE POTENTIAL:
- Year 1: $X-Y MRR
- Path to $10K MRR: [Timeline and milestones]

SOURCES:
- [Source 1 with URL or citation]
- [Source 2 with URL or citation]
- [Source 3 with URL or citation]
```

---

## Troubleshooting

### Error: "OPENAI_API_KEY not found"
**Solution:**
```bash
# Check .env file exists
ls .env

# Verify it has your key
cat .env | grep OPENAI_API_KEY

# If missing, add it
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

### Error: "ModuleNotFoundError: No module named 'agents'"
**Solution:**
```bash
# Make sure you're in the project root
pwd
# Should show: .../Agent Factory

# Run with correct path
poetry run python test_bob.py
```

### Bob Returns Generic Responses
**Possible causes:**
1. **No Tavily API key** - Bob defaults to basic search
   - Check: `cat .env | grep TAVILY_API_KEY`
   - Should show: `TAVILY_API_KEY=tvly-dev-...`

2. **Query too vague** - Be specific
   - ✗ Bad: "Find market opportunities"
   - ✓ Good: "Find 3 opportunities in AI with $10K MRR potential, < 10 competitors"

3. **Not using tools** - Check verbose mode
   ```bash
   # Edit agents/unnamedagent_v1_0.py line 106
   # Change: verbose=False
   # To: verbose=True
   ```

### Slow Responses (> 2 minutes)
**Normal for:**
- First query (loading models)
- Complex queries (5+ criteria)
- Using Tavily AI search (more thorough)

**Speed up:**
- Use simpler queries
- Ask one thing at a time
- Use gpt-4o-mini (already default)

---

## Bob's Full Capabilities

### Tools (10 Total)
**Research:**
- WikipediaSearchTool (facts, definitions)
- DuckDuckGoSearchTool (web search)
- TavilySearchTool (AI-optimized search) ⭐
- CurrentTimeTool (date/time)

**File Operations:**
- ReadFileTool (read code, docs)
- WriteFileTool (save reports)
- ListDirectoryTool (browse)
- FileSearchTool (find patterns)
- GitStatusTool (analyze repos)

**Plus:** Whatever you add via editing!

### Invariants (Rules Bob Must Follow)
1. **Evidence-Based** - All claims backed by sources
2. **Ethical Research** - No exploitative tactics
3. **Transparency** - Disclose uncertainty
4. **User Focus** - Real problems, not just profit
5. **Timeliness** - Current data (< 6 months)
6. **Actionability** - Specific next steps
7. **Cost Awareness** - < $0.50 per query
8. **Response Speed** - < 60s initial, < 5min deep

---

## Next Steps After Testing

### 1. Customize Bob
```bash
# Edit tools, invariants, etc.
poetry run python agentcli.py edit bob-1
```

### 2. Save Results
Ask Bob to write findings to a file:
```
Research AI automation opportunities and save results to market_research.md
```

### 3. Build Something!
Use Bob's insights to:
- Validate your app idea
- Find your niche
- Understand competition
- Estimate revenue potential

---

## Performance Targets

Bob should achieve:
- ✅ Initial findings: < 60 seconds
- ✅ Deep analysis: < 5 minutes
- ✅ Cost per query: < $0.50
- ✅ Accuracy: ≥ 95% (with citations)

If Bob is slower or more expensive, check:
- Are you using gpt-4 instead of gpt-4o-mini?
- Is query overly complex?
- Is internet connection slow?

---

## Example Session

```bash
$ poetry run python test_bob.py

BOB - MARKET RESEARCH DOMINATOR - QUICK TEST
========================================================================

[1/3] Creating Bob with full power tools...
      ✓ Agent created
      ✓ Tools: 10 (research + file ops)

[2/3] Running market research query...

Query:
------------------------------------------------------------------------
Find 3 underserved niches in the AI agent marketplace...
------------------------------------------------------------------------

[3/3] Results:

========================================================================
MARKET OPPORTUNITY 1: AI Voice Receptionists for Service Businesses

MARKET ANALYSIS:
- Market Size: 500K+ US service businesses (salons, gyms, clinics)
- Growth Rate: 15% annually (Source: IBISWorld 2024)
- Customer Profile: Small businesses (1-10 employees), 30-60 age range

COMPETITION:
- Competition Level: Low (3-4 established players)
- Key Players: Ruby Receptionists ($200-500/mo), Smith.ai
- Feature Gaps: No AI-first solution under $100/month

OPPORTUNITY:
- Pain Point: Miss 30% of calls during busy hours, lose bookings
- Willingness to Pay: $50-150/month
- Entry Strategy: Start with hair salons, expand to medical

VALIDATION STEPS:
1. Interview 20 salon owners in your city
2. Build MVP with Twilio + GPT-4 in 1 week
3. Beta test with 10 salons at $49/month

REVENUE POTENTIAL:
- Year 1: $5K-15K MRR (100-300 customers)
- Path to $10K MRR: 200 customers @ $50/mo (6-9 months)

SOURCES:
- IBISWorld Service Industry Report 2024
- Small Business Trends Survey 2024
- Reddit r/smallbusiness (40+ pain point mentions)

[Similar detailed analysis for opportunities 2 and 3...]
========================================================================

✓ Test completed successfully!
```

---

## Summary

**To test Bob:**
```bash
poetry run python test_bob.py
```

**To chat with Bob:**
```bash
poetry run agentcli chat
```

**To customize Bob:**
```bash
poetry run python agentcli.py edit bob-1
```

**Bob is ready to find you market opportunities!** 🚀

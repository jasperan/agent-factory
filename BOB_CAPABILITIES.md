# Bob - Market Research Dominator Agent

## 🚀 Status: FULLY OPERATIONAL

**Files:**
- Spec: `specs/bob-1.md`
- Code: `agents/unnamedagent_v1_0.py`
- Tests: `tests/test_unnamedagent_v1_0.py`

---

## 🔧 Full Toolset (9 Tools)

### Research & Discovery
1. **WikipediaSearchTool** - Factual information, definitions, industry overviews
2. **DuckDuckGoSearchTool** - Web search for current market trends
3. **TavilySearchTool** - AI-optimized search, best for market intelligence
4. **CurrentTimeTool** - Date/time for temporal analysis

### Competitive Intelligence
5. **ReadFileTool** - Read competitor code, documentation, specs
6. **ListDirectoryTool** - Browse GitHub repos, project structures
7. **FileSearchTool** - Find patterns in competitor codebases
8. **GitStatusTool** - Analyze repository activity

### Output & Reporting
9. **WriteFileTool** - Save research reports, market analyses

---

## 💡 What Bob Can Do

### Market Research
- Find underserved niches with MRR potential
- Analyze market size and growth trends
- Identify customer pain points from forums/social
- Track industry news and funding rounds

### Competitive Analysis
- Research competitor products and pricing
- Analyze competitor codebases (open source)
- Identify feature gaps and opportunities
- Map competitive landscapes

### Opportunity Discovery
- Find emerging trends before they saturate
- Validate market demand with real data
- Calculate addressable market (TAM/SAM)
- Estimate revenue potential (MRR projections)

### Strategic Insights
- Recommend positioning strategies
- Provide go-to-market recommendations
- Suggest validation methods (interviews, MVPs)
- Identify ideal customer profiles

---

## 🎯 Example Queries

### Niche Discovery
```
Find 5 micro-SaaS opportunities in AI automation with:
- MRR potential > $10K
- < 10 competitors
- Build time < 2 weeks
```

### Competitive Intel
```
Analyze the top 3 AI writing tools:
- What features do they have?
- What are customers complaining about?
- What gaps can I exploit?
```

### Market Validation
```
Research demand for AI voice assistants for dentists:
- Market size
- Willingness to pay
- Current solutions
- Entry barriers
```

### Trend Spotting
```
What automation trends are emerging in 2024 that:
- Haven't been commercialized yet
- Have early adopter signals
- Solve real business problems
```

---

## 📊 Performance Specs

**Speed:**
- Initial findings: < 60 seconds
- Deep analysis: < 5 minutes

**Cost:**
- < $0.50 per research query

**Accuracy:**
- >= 95% (with source citations)

---

## 🧪 How to Test Bob

### Quick Demo
```bash
poetry run python agents/unnamedagent_v1_0.py
```

### Run Tests
```bash
poetry run pytest tests/test_unnamedagent_v1_0.py -v
```

### Interactive Chat
```bash
poetry run agentcli chat --agent bob
```

---

## 🎓 Bob's Rules (Invariants)

1. **Evidence-Based** - All claims backed by verifiable sources
2. **Ethical Research** - No exploitative practices or dark patterns
3. **Transparency** - Disclose uncertainty and data limitations
4. **User Focus** - Prioritize real customer problems over hype
5. **Timeliness** - Focus on current data (< 6 months old)
6. **Actionability** - Every insight includes next steps
7. **Cost Awareness** - Stay under $0.50 per query
8. **Response Speed** - Fast initial findings, thorough deep dives

---

## 📈 Expected Output Format

Bob provides structured insights like:

```
MARKET OPPORTUNITY: [Niche Name]

MARKET ANALYSIS:
- Market Size: [TAM/SAM with sources]
- Growth Rate: [% with trend data]
- Customer Profile: [demographics, behaviors]

COMPETITION:
- Level: [Low/Medium/High]
- Key Players: [top 3-5 competitors]
- Gaps: [unmet needs, weak points]

OPPORTUNITY:
- Pain Point: [specific problem to solve]
- Willingness to Pay: [$X-Y/month]
- Entry Strategy: [positioning, channels]

VALIDATION:
- Step 1: [interview 10 customers]
- Step 2: [build MVP in 2 weeks]
- Step 3: [test pricing at $X]

REVENUE POTENTIAL:
- Year 1: $X-Y MRR
- Path to $10K MRR: [timeline]

SOURCES:
- [Source 1 with URL]
- [Source 2 with URL]
```

---

## 🔥 Pro Tips

1. **Be Specific** - "AI chatbots for dentists" > "AI chatbots"
2. **Set Constraints** - Give MRR targets, competitor limits, build time
3. **Ask for Validation** - Request concrete next steps, not just insights
4. **Save Reports** - Ask Bob to write findings to files for later reference
5. **Iterate** - Use findings to drill deeper into promising niches

---

## 🚨 Limitations

**Bob can't:**
- Access paid databases (Gartner, Forrester, etc.)
- Guarantee revenue outcomes
- Make financial investment decisions
- Execute trades or build products automatically
- Access private company data

**But he can:**
- Find publicly available market data
- Analyze open-source competitor code
- Research social discussions and forums
- Provide evidence-based recommendations

---

## 🎉 Next Steps

1. **Try a Query** - Test Bob with your business idea
2. **Iterate** - Use his findings to refine your search
3. **Build** - Take the validated opportunity and ship!

---

**Built with Agent Factory** 🤖
**Powered by:** OpenAI GPT-4o-mini + 9 Tools
**Version:** 1.0 (DRAFT)
**Owner:** mike

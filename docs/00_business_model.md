# Agent Factory - Business Model & Revenue Projections

**Version:** 1.0
**Last Updated:** 2025-12-07
**Status:** Phase 0 Documentation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Pricing Strategy](#pricing-strategy)
3. [Revenue Streams](#revenue-streams)
4. [Market Sizing](#market-sizing)
5. [Customer Acquisition](#customer-acquisition)
6. [Revenue Projections](#revenue-projections)
7. [Unit Economics](#unit-economics)
8. [Cost Structure](#cost-structure)
9. [Path to $10K MRR](#path-to-10k-mrr)
10. [Financial Scenarios](#financial-scenarios)
11. [Key Metrics & KPIs](#key-metrics--kpis)

---

## Executive Summary

### Vision

Agent Factory is a **multi-tenant SaaS platform** that enables developers and non-developers to build, deploy, and monetize AI agents through declarative specifications.

### Target Market

- **Primary:** Solo founders, indie hackers, small dev teams (1-10 people)
- **Secondary:** SMB development teams (10-50 people)
- **Tertiary:** Enterprise organizations (50+ people)

**Total Addressable Market (TAM):** $2.4B
- 30M developers worldwide
- 10% interested in AI agent development (3M)
- Average spend: $800/year

**Serviceable Addressable Market (SAM):** $480M
- 600K developers actively building AI agents
- Average spend: $800/year

**Serviceable Obtainable Market (SOM):** $24M
- 30K customers (0.1% market share in year 3)
- Average revenue per account (ARPA): $800/year

### Revenue Goals

| Milestone | Timeline | MRR | ARR | Customers |
|-----------|----------|-----|-----|-----------|
| **Brain Fart Checker Launch** | Month 1 | $990 | $11,880 | 10 paid |
| **Beta Launch** | Month 3 | $5,000 | $60,000 | 100 paid |
| **First Target** | Month 3 | $10,000 | $120,000 | 200 paid |
| **Second Target** | Month 6 | $25,000 | $300,000 | 500 paid |
| **Year 1 Target** | Month 12 | $50,000 | $600,000 | 1,000 paid |
| **Year 2 Target** | Month 24 | $150,000 | $1,800,000 | 3,000 paid |
| **Year 3 Target** | Month 36 | $400,000 | $4,800,000 | 8,000 paid |

### Business Model

**Primary:** Subscription SaaS (recurring revenue)
**Secondary:** Marketplace fees (transaction revenue)
**Tertiary:** Enterprise services (one-time revenue)

**Key Differentiators:**
1. **Constitutional Programming** - Spec-first approach
2. **Brain Fart Checker** - AI-powered idea validator ($99/mo standalone)
3. **Cost Optimization** - Multi-LLM routing (Llama3 → Perplexity → Claude)
4. **Community Marketplace** - 70/30 revenue split with creators
5. **OpenHands Integration** - Autonomous code generation

---

## Pricing Strategy

### Subscription Tiers

#### 1. Free Tier - "Starter"
**Price:** $0/month
**Target:** Hobbyists, students, experimenters

**Features:**
- 3 agents maximum
- 100 agent runs per month
- Basic tools (Wikipedia, DuckDuckGo)
- Community support (Discord)
- Public marketplace browsing
- API access (100 requests/day)

**Quotas:**
- 100 runs/month
- 10K tokens/month
- 1 team member
- 3 agents
- 1 template deployment from marketplace

**Purpose:**
- Lead generation
- Product-market fit validation
- Community building
- Free tier users become advocates

**Conversion Goal:** 10% to Pro tier within 30 days

---

#### 2. Pro Tier - "Builder"
**Price:** $49/month ($470/year - save $118)
**Target:** Solo founders, indie hackers, small teams

**Features:**
- **Unlimited agents**
- **1,000 runs per month**
- **All tools** (Perplexity, GitHub, Stripe, etc.)
- **Priority support** (24-hour response)
- **Private agents** (not visible in marketplace)
- **API access** (10K requests/day)
- **Custom domains** (agents.yourdomain.com)
- **Team collaboration** (up to 5 members)
- **Advanced analytics** (cost breakdown, performance metrics)
- **Template deployment** (unlimited from marketplace)
- **Version control** (Git-like versioning for agents)

**Quotas:**
- 1,000 runs/month
- 500K tokens/month
- 5 team members
- Unlimited agents
- 10 template deployments from marketplace

**Purpose:**
- Primary revenue driver
- Sweet spot for target market
- Unlock professional features

**Conversion Goal:** 80% retention after 3 months

---

#### 3. Enterprise Tier - "Platform"
**Price:** $299/month ($2,870/year - save $718)
**Target:** Development teams, agencies, mid-market companies

**Features:**
- **Everything in Pro, plus:**
- **10,000 runs per month**
- **Dedicated support** (4-hour response, Slack channel)
- **SSO (SAML)** - Single sign-on
- **Advanced security** (SOC 2, HIPAA compliance)
- **SLA guarantee** (99.9% uptime)
- **Custom integrations** (white-glove onboarding)
- **Unlimited team members**
- **Role-based permissions** (admin, developer, viewer)
- **Audit logs** (complete activity history)
- **Priority feature requests**
- **Dedicated account manager**
- **Volume discounts** (negotiable for 100K+ runs)

**Quotas:**
- 10,000 runs/month
- 5M tokens/month
- Unlimited team members
- Unlimited agents
- Unlimited template deployments

**Purpose:**
- High-value customers
- Increased ARPA
- Enterprise validation

**Conversion Goal:** 5% of Pro users upgrade to Enterprise

---

#### 4. Brain Fart Checker - "Validator" (Standalone)
**Price:** $99/month ($950/year - save $238)
**Target:** Founders, product managers, idea validators

**Features:**
- **AI-powered idea validation**
- **Market research** (Perplexity-powered)
- **Competitive analysis**
- **Revenue projections**
- **Kill criteria enforcement** (novelty < 60, MRR < $2K, competitors > 20)
- **Unlimited validations**
- **Export reports** (PDF, Markdown)
- **Historical tracking** (see past validations)

**Quotas:**
- Unlimited validations
- 200 runs/month
- 100K tokens/month

**Can be bundled:**
- Brain Fart Checker + Pro = $129/month (save $19)
- Brain Fart Checker + Enterprise = $369/month (save $29)

**Purpose:**
- First product launch (fastest to market)
- High-margin standalone product
- Upsell path to full platform

**Target:** 50 paid users by Month 3 = $4,950/mo MRR

---

### Pricing Rationale

**Why $49 for Pro?**
- Market benchmark: CrewAI ($50/mo), Vertex AI Agent Builder ($40-60/mo range)
- Perceived value: Unlimited agents, all tools, team collaboration
- LTV/CAC math: If CAC = $150, payback period = 3 months (acceptable)
- Price anchoring: $99 Brain Fart Checker makes $49 seem reasonable

**Why $299 for Enterprise?**
- 6x the runs of Pro tier (10K vs 1K)
- SSO + compliance alone worth $100/mo for enterprises
- Dedicated support justifies premium
- Still cheaper than hiring AI engineer ($10K/mo)

**Why $99 for Brain Fart Checker?**
- Standalone value: Replaces $500 market research report
- Time savings: 10 hours of research compressed to 5 minutes
- Kill criteria prevents $10K+ wasted on bad ideas
- Price point attracts serious founders (quality filter)

---

### Competitive Pricing Comparison

| Product | Price | Our Advantage |
|---------|-------|---------------|
| **CrewAI** | $50/mo | We have Brain Fart Checker, cost optimization |
| **Vertex AI Agent Builder** | $50-100/mo | We're more accessible (no GCP required) |
| **MindStudio** | $39/mo | We have code-first approach (more powerful) |
| **Lindy** | $99/mo | We're cheaper for similar features |
| **LangSmith** | $39/mo | We have full platform (not just monitoring) |

**Positioning:** Mid-market pricing with premium features. Not cheapest, not most expensive, but best value.

---

## Revenue Streams

### 1. Subscription Revenue (Primary)

**Model:** Recurring monthly/annual subscriptions

**Breakdown by Tier:**

| Tier | Price/Month | Target Customers (Month 12) | MRR Contribution |
|------|-------------|----------------------------|------------------|
| Free | $0 | 5,000 | $0 |
| Pro | $49 | 800 (80% of paid) | $39,200 |
| Enterprise | $299 | 50 (5% of paid) | $14,950 |
| Brain Fart Checker | $99 | 150 | $14,850 |
| **Total** | - | **6,000** | **$69,000** |

**Annual Revenue (Month 12):** $828,000

**Growth Assumptions:**
- 10% free-to-paid conversion rate
- 80% Pro, 15% Brain Fart Checker, 5% Enterprise (of paid users)
- 3% monthly churn rate
- 20% annual plan adoption (10% discount = 90% of monthly rate)

---

### 2. Marketplace Revenue (Secondary)

**Model:** 30% platform fee on paid template sales

**Assumptions:**
- 100 templates published by Month 12
- 20% are paid templates ($19 average)
- Average 5 purchases per paid template per month
- 20 paid templates × 5 purchases × $19 = $1,900 gross sales/month
- Platform fee: $1,900 × 30% = $570/month
- Creator earnings: $1,900 × 70% = $1,330/month

**Marketplace MRR (Month 12):** $570
**Marketplace ARR (Month 12):** $6,840

**Growth Potential:**
- Month 24: 500 templates, $2,850/mo marketplace revenue
- Month 36: 2,000 templates, $11,400/mo marketplace revenue

---

### 3. Enterprise Services (Tertiary)

**Model:** One-time professional services fees

**Services Offered:**
- **Custom integrations:** $5,000 - $15,000
- **White-glove onboarding:** $2,000 - $5,000
- **Training workshops:** $3,000 - $8,000
- **Custom agent development:** $10,000 - $50,000

**Assumptions:**
- 10 enterprise customers by Month 12
- 50% require custom services
- Average services fee: $8,000

**Services Revenue (Month 12):** $40,000 one-time

---

### 4. API Overage Fees (Future)

**Model:** Pay-as-you-go for usage beyond quota

**Pricing:**
- $0.10 per 1,000 agent runs (after monthly quota)
- $5 per 100K tokens (after monthly quota)

**Assumptions:**
- 20% of Pro users exceed quota
- Average overage: $25/month

**Overage MRR (Month 12):** 800 Pro × 20% × $25 = $4,000

---

### Total Revenue Summary (Month 12)

| Revenue Stream | Monthly | Annual |
|----------------|---------|--------|
| Subscriptions | $69,000 | $828,000 |
| Marketplace | $570 | $6,840 |
| Enterprise Services | - | $40,000 (one-time) |
| API Overages | $4,000 | $48,000 |
| **Total** | **$73,570** | **$922,840** |

---

## Market Sizing

### Total Addressable Market (TAM)

**Global Developer Population:** 30 million (Source: Stack Overflow, GitHub)

**AI-Interested Developers:** 10% = 3 million
- Subset who have experimented with AI/ML
- Growing rapidly (30% YoY)

**Average Spend on AI Tools:** $800/year
- GitHub Copilot: $100/year
- OpenAI API: $200/year
- LangSmith/LangChain: $300/year
- Other tools: $200/year

**TAM = 3M × $800 = $2.4 billion**

---

### Serviceable Addressable Market (SAM)

**Developers Actively Building Agents:** 600,000
- Subset using LangChain, CrewAI, or similar (20% of AI-interested)
- Active GitHub repos with "AI agent" or "LangChain": ~100K
- Developer community growth: 50% YoY

**SAM = 600K × $800 = $480 million**

---

### Serviceable Obtainable Market (SOM)

**Realistic Market Share (Year 3):** 0.1% of SAM

**Year 3 Targets:**
- 30,000 total users (free + paid)
- 8,000 paid customers
- ARPA: $800/year ($67/month blended)

**SOM = 30K × $800 = $24 million**

---

### Market Segmentation

| Segment | Size | Willingness to Pay | Target Tier |
|---------|------|-------------------|-------------|
| **Hobbyists** | 300K (50%) | Low ($0-20/mo) | Free |
| **Indie Hackers** | 180K (30%) | Medium ($30-100/mo) | Pro, Brain Fart |
| **Small Teams** | 90K (15%) | High ($100-500/mo) | Pro, Enterprise |
| **Enterprise** | 30K (5%) | Very High ($500+/mo) | Enterprise |

**Our Focus:** Indie hackers and small teams (45% of market, highest willingness to pay)

---

## Customer Acquisition

### Customer Acquisition Cost (CAC)

**Target CAC by Tier:**

| Tier | Target CAC | Payback Period | LTV/CAC Ratio |
|------|-----------|----------------|---------------|
| Free | $0 (organic) | N/A | N/A |
| Pro | $150 | 3 months | 6:1 |
| Enterprise | $1,500 | 5 months | 8:1 |
| Brain Fart Checker | $200 | 2 months | 5:1 |

---

### Acquisition Channels

#### 1. Content Marketing (Organic)
**Budget:** $0 (time investment)
**CAC:** $0
**Target:** 50% of customers

**Tactics:**
- Blog posts (2-3 per week)
  - "How to build a market research agent in 10 minutes"
  - "Constitutional programming: Why specs are eternal"
  - "Cost optimization: $0.001 vs $0.015 per LLM call"
- YouTube tutorials (1 per week)
- Open-source repos (showcase examples)
- GitHub README.md (primary discovery)

**Expected Results:**
- Month 1: 100 organic signups
- Month 3: 500 organic signups
- Month 6: 2,000 organic signups
- Month 12: 5,000 organic signups

---

#### 2. Product Hunt Launch
**Budget:** $500 (preparation, graphics)
**CAC:** $5 per signup
**Target:** 100 signups in 24 hours

**Tactics:**
- Launch on Tuesday (best day)
- Hunter with >10K followers
- Teaser posts 1 week before
- Engage in comments all day
- Offer Product Hunt exclusive (20% off first year)

**Expected Results:**
- #1 Product of the Day
- 100 upvotes
- 50 comments
- 100-200 signups
- 10-20 paid conversions

---

#### 3. Community Building (Discord, Twitter)
**Budget:** $100/month (tools, bots)
**CAC:** $10 per customer
**Target:** 25% of customers

**Tactics:**
- Active Discord server (daily engagement)
- Twitter/X presence (3-5 posts/day)
- Reddit participation (r/LangChain, r/SideProject, r/MachineLearning)
- Hacker News (Show HN: monthly updates)

**Expected Results:**
- Month 1: 50 Discord members
- Month 3: 500 Discord members
- Month 6: 2,000 Discord members
- Month 12: 5,000 Discord members
- 10% conversion to paid

---

#### 4. Paid Advertising (Phase 2)
**Budget:** $3,000/month (after product-market fit)
**CAC:** $150 per customer
**Target:** 20 paid customers/month

**Channels:**
- Google Ads (search: "ai agent builder", "crewai alternative")
- Twitter/X Ads (targeting AI/ML developers)
- Dev.to sponsored posts
- HackerNoon sponsored content

**Expected Results:**
- Month 6: Launch paid ads (after PMF validation)
- CTR: 2-3%
- Conversion rate: 5%
- 20 paid customers/month

---

#### 5. Partnerships & Integrations
**Budget:** $0 (time investment)
**CAC:** $50 per customer
**Target:** 10% of customers

**Partners:**
- LangChain (official integration)
- Perplexity (featured user story)
- OpenHands (joint case study)
- Supabase (template in marketplace)

**Expected Results:**
- Month 3: LangChain partnership announced
- Month 6: Perplexity case study published
- Month 9: Supabase template featured
- 100 customers from partnerships (Month 12)

---

### Customer Journey

```
AWARENESS → CONSIDERATION → TRIAL → CONVERSION → RETENTION → ADVOCACY

1. AWARENESS (Discovery)
   - Blog post: "How to build AI agents"
   - YouTube: "Agent Factory tutorial"
   - Product Hunt: #1 Product of the Day

   ↓ (Call-to-action: "Try Free")

2. CONSIDERATION (Research)
   - Homepage: Feature comparison table
   - Docs: Read "Getting Started" guide
   - Marketplace: Browse templates

   ↓ (Call-to-action: "Sign Up Free")

3. TRIAL (Activation)
   - Sign up with GitHub OAuth (1 click)
   - Create first agent from template (5 minutes)
   - Run agent and see results (30 seconds)

   ↓ (Aha moment: "This actually works!")

4. CONVERSION (Upgrade)
   - Hit 100 run limit (free tier)
   - In-app prompt: "Upgrade to Pro for unlimited runs"
   - 1-click checkout (Stripe)

   ↓ (Email: "Welcome to Pro!")

5. RETENTION (Engagement)
   - Weekly usage reports (email)
   - Cost savings alerts ("You saved $12 this week")
   - New feature announcements (changelog)

   ↓ (Continue using, invite team members)

6. ADVOCACY (Referrals)
   - Share agent in marketplace (earn revenue)
   - Refer friend (both get 20% off)
   - Write testimonial (featured on homepage)

   ↓ (New customers from referrals)
```

---

### Conversion Funnel

**Month 3 Example:**

```
10,000 Website Visitors
    ↓ (10% sign up)
1,000 Free Signups
    ↓ (50% activate)
500 Active Users
    ↓ (20% convert to paid)
100 Paid Customers
    ↓ (3% monthly churn)
97 Retained Customers

MRR: 100 × $60 (blended) = $6,000
```

**Optimization Levers:**
- Increase signup rate: 10% → 15% (better CTAs)
- Increase activation: 50% → 70% (better onboarding)
- Increase conversion: 20% → 30% (better value proposition)
- Decrease churn: 3% → 2% (better product)

**Optimized Funnel:**
```
10,000 Visitors → 1,500 Signups → 1,050 Active → 315 Paid → 312 Retained

MRR: 315 × $60 = $18,900 (3x improvement!)
```

---

## Revenue Projections

### Month-by-Month Breakdown (Year 1)

| Month | Free Users | Paid Users | MRR | ARR (Run Rate) | Notes |
|-------|-----------|-----------|-----|----------------|-------|
| **1** | 200 | 10 | $990 | $11,880 | Brain Fart Checker launch |
| **2** | 500 | 30 | $2,400 | $28,800 | Product Hunt launch |
| **3** | 1,000 | 100 | $6,000 | $72,000 | Beta web UI launch |
| **4** | 1,500 | 150 | $9,000 | $108,000 | Marketplace opens |
| **5** | 2,000 | 200 | $12,000 | $144,000 | First Enterprise customer |
| **6** | 2,500 | 300 | $18,000 | $216,000 | Paid ads launch |
| **7** | 3,000 | 400 | $24,000 | $288,000 | LangChain partnership |
| **8** | 3,500 | 500 | $30,000 | $360,000 | - |
| **9** | 4,000 | 650 | $39,000 | $468,000 | Perplexity case study |
| **10** | 4,500 | 800 | $48,000 | $576,000 | - |
| **11** | 5,000 | 950 | $57,000 | $684,000 | - |
| **12** | 5,500 | 1,100 | $66,000 | $792,000 | **Year 1 Complete** |

**Year 1 MRR Growth:** $990 → $66,000 (67x)
**Year 1 ARR:** $792,000

---

### Year 2-3 Projections

| Metric | Year 1 (Month 12) | Year 2 (Month 24) | Year 3 (Month 36) |
|--------|-------------------|-------------------|-------------------|
| **Free Users** | 5,500 | 20,000 | 50,000 |
| **Paid Users** | 1,100 | 3,500 | 10,000 |
| **Conversion Rate** | 20% | 17.5% | 20% |
| **MRR** | $66,000 | $210,000 | $600,000 |
| **ARR** | $792,000 | $2,520,000 | $7,200,000 |
| **ARPA** | $60/mo | $60/mo | $60/mo |
| **Churn Rate** | 3%/month | 2.5%/month | 2%/month |
| **LTV** | $2,000 | $2,400 | $3,000 |
| **CAC** | $150 | $200 | $250 |
| **LTV/CAC Ratio** | 13:1 | 12:1 | 12:1 |

---

### Revenue Breakdown (Year 3)

| Source | MRR | % of Total |
|--------|-----|------------|
| Pro Tier ($49) | $392,000 | 65% |
| Enterprise ($299) | $149,500 | 25% |
| Brain Fart Checker ($99) | $49,500 | 8% |
| Marketplace Fees | $9,000 | 2% |
| **Total** | **$600,000** | **100%** |

---

## Unit Economics

### Customer Lifetime Value (LTV)

**Calculation:**
```
LTV = ARPA × Gross Margin ÷ Churn Rate

Pro Tier:
ARPA = $49/month
Gross Margin = 80% (after COGS)
Churn Rate = 3%/month

LTV = $49 × 0.80 ÷ 0.03 = $1,307
```

**LTV by Tier:**

| Tier | ARPA | Gross Margin | Churn Rate | LTV |
|------|------|--------------|------------|-----|
| Pro | $49 | 80% | 3% | $1,307 |
| Enterprise | $299 | 85% | 2% | $12,708 |
| Brain Fart | $99 | 75% | 4% | $1,856 |
| **Blended** | **$60** | **80%** | **3%** | **$1,600** |

---

### Customer Acquisition Cost (CAC)

**Calculation:**
```
CAC = Total Sales & Marketing Spend ÷ New Customers

Month 12 Example:
Sales & Marketing Spend = $5,000 (ads + tools + content)
New Customers = 50

CAC = $5,000 ÷ 50 = $100
```

**CAC by Channel:**

| Channel | Monthly Spend | Customers/Month | CAC |
|---------|---------------|-----------------|-----|
| Organic (content) | $0 | 30 | $0 |
| Community (Discord) | $100 | 10 | $10 |
| Product Hunt | $500 (one-time) | 20 | $25 |
| Paid Ads | $3,000 | 20 | $150 |
| Partnerships | $0 | 5 | $0 |
| **Total** | **$3,100** | **85** | **$36** |

**CAC Payback Period:**
```
Payback Period = CAC ÷ (ARPA × Gross Margin)

Pro Tier: $150 ÷ ($49 × 0.80) = 3.8 months
```

---

### LTV/CAC Ratio

**Target:** >3:1 (industry standard for SaaS)
**Agent Factory:**

| Tier | LTV | CAC | LTV/CAC |
|------|-----|-----|---------|
| Pro | $1,307 | $150 | **8.7:1** ✅ |
| Enterprise | $12,708 | $1,500 | **8.5:1** ✅ |
| Brain Fart | $1,856 | $200 | **9.3:1** ✅ |

**Conclusion:** Healthy unit economics across all tiers. High LTV/CAC ratios indicate strong product-market fit and sustainable growth.

---

### Gross Margin

**Calculation:**
```
Gross Margin = (Revenue - COGS) ÷ Revenue

COGS Components:
- LLM API costs (Anthropic, OpenAI, Perplexity)
- Infrastructure (Cloud Run, Supabase, Redis)
- Third-party tools (Stripe fees, SendGrid)

Example (Pro User):
Revenue: $49/month
COGS:
  - LLM costs: $5/month (1,000 runs × $0.005 avg)
  - Infrastructure: $2/month (Cloud Run, database share)
  - Stripe fees: $1.70 (3.5% + $0.30)
  - Other: $1.30 (SendGrid, monitoring)
  Total COGS: $10/month

Gross Margin = ($49 - $10) ÷ $49 = 79.6%
```

**Gross Margin by Tier:**

| Tier | Revenue/Month | COGS/Month | Gross Margin |
|------|---------------|------------|--------------|
| Pro | $49 | $10 | 80% |
| Enterprise | $299 | $45 | 85% |
| Brain Fart | $99 | $25 | 75% |
| **Blended** | **$60** | **$12** | **80%** |

**Target Gross Margin:** >75% (SaaS industry standard: 70-85%)

**Key Drivers:**
- LLM cost optimization (multi-LLM routing saves 60%)
- Efficient infrastructure (serverless, auto-scaling)
- High-margin Enterprise tier (pulls blended margin up)

---

## Cost Structure

### Fixed Costs (Monthly)

| Category | Month 1 | Month 6 | Month 12 | Year 2 |
|----------|---------|---------|----------|--------|
| **Infrastructure** | $100 | $300 | $750 | $2,500 |
| - Cloud Run | $50 | $150 | $400 | $1,500 |
| - Supabase | $25 | $75 | $150 | $500 |
| - Redis | $10 | $25 | $50 | $200 |
| - Storage | $5 | $20 | $50 | $150 |
| - Monitoring | $10 | $30 | $100 | $150 |
| **Software/Tools** | $150 | $300 | $500 | $800 |
| - GitHub | $0 | $21 | $21 | $21 |
| - Sentry | $0 | $26 | $26 | $99 |
| - SendGrid | $15 | $50 | $100 | $200 |
| - Stripe | $0 | $0 | $0 | $0 |
| - Figma | $15 | $15 | $15 | $15 |
| - Vercel | $20 | $20 | $20 | $20 |
| - Cloudflare | $0 | $20 | $20 | $20 |
| - Domain | $12 | $12 | $12 | $12 |
| - Other | $88 | $136 | $286 | $413 |
| **Marketing** | $500 | $3,000 | $5,000 | $15,000 |
| - Paid ads | $0 | $2,500 | $4,000 | $12,000 |
| - Content creation | $300 | $300 | $500 | $1,500 |
| - Tools | $100 | $100 | $300 | $1,000 |
| - Events/sponsorships | $100 | $100 | $200 | $500 |
| **Support** | $0 | $500 | $2,000 | $8,000 |
| - Support tools (Intercom) | $0 | $0 | $100 | $500 |
| - Freelance support | $0 | $500 | $1,900 | $7,500 |
| **Development** | $0 | $2,000 | $5,000 | $20,000 |
| - Freelance developers | $0 | $2,000 | $5,000 | $20,000 |
| **Total Fixed Costs** | **$750** | **$6,100** | **$13,250** | **$46,300** |

---

### Variable Costs (per customer/month)

| Cost Component | Free User | Pro User | Enterprise User |
|----------------|-----------|----------|-----------------|
| **LLM API Costs** | $0.50 | $5.00 | $45.00 |
| - Llama3 (local) | $0.00 | $1.00 | $10.00 |
| - Perplexity | $0.30 | $2.00 | $15.00 |
| - Claude | $0.20 | $2.00 | $20.00 |
| **Infrastructure** | $0.10 | $2.00 | $10.00 |
| - Database | $0.05 | $1.00 | $5.00 |
| - Compute | $0.03 | $0.70 | $4.00 |
| - Storage | $0.02 | $0.30 | $1.00 |
| **Payment Processing** | $0.00 | $1.72 | $10.48 |
| - Stripe fees (3.5% + $0.30) | $0.00 | $1.72 | $10.48 |
| **Other** | $0.10 | $1.28 | $4.52 |
| - Email | $0.05 | $0.50 | $2.00 |
| - Monitoring | $0.05 | $0.78 | $2.52 |
| **Total Variable Cost** | **$0.70** | **$10.00** | **$70.00** |
| **Revenue** | **$0.00** | **$49.00** | **$299.00** |
| **Contribution Margin** | **-$0.70** | **$39.00** | **$229.00** |
| **Gross Margin %** | **N/A** | **79.6%** | **76.6%** |

---

### Break-Even Analysis

**Fixed Costs (Month 12):** $13,250
**Contribution Margin (Blended):** $48 per paid customer

**Break-Even Customers:**
```
Break-Even = Fixed Costs ÷ Contribution Margin
Break-Even = $13,250 ÷ $48 = 276 paid customers
```

**Month 12 Projected:** 1,100 paid customers
**Break-Even Status:** ✅ Profitable (4x over break-even)

**Time to Break-Even:**
- Month 1: 10 customers (need 276, **deficit:** $12,500)
- Month 3: 100 customers (need 276, **deficit:** $4,800)
- Month 4: 150 customers (need 276, **deficit:** $6,200)
- Month 5: 200 customers (need 276, **deficit:** $3,650)
- **Month 6: 300 customers (✅ BREAK-EVEN)**

---

### Cost Optimization Strategies

1. **LLM Cost Reduction (60% savings)**
   - Route to Llama3 (local, $0) for 40% of queries
   - Route to Perplexity ($0.001) for 40% of queries
   - Route to Claude ($0.015) only for complex 20%
   - **Result:** $0.005 blended cost vs $0.015 direct Claude

2. **Infrastructure Efficiency**
   - Serverless Cloud Run (pay only when running)
   - Aggressive caching (80% cache hit rate)
   - Read replicas for database (reduce primary load)
   - **Result:** 50% lower infrastructure costs vs traditional VMs

3. **Payment Processing**
   - Annual plans reduce Stripe fees (11 charges vs 12)
   - Bank transfers for Enterprise (no Stripe fee)
   - **Result:** 10% savings on payment processing

4. **Support Efficiency**
   - Comprehensive docs (reduce support tickets)
   - Community Discord (peer support)
   - AI chatbot (deflect 30% of tickets)
   - **Result:** 1:500 support ratio (vs 1:100 industry standard)

---

## Path to $10K MRR

### 90-Day Sprint to First Milestone

**Goal:** $10,000 MRR by Day 90 (Month 3)

**Required:** 200 paid customers (blended $50 ARPA)

---

### Week-by-Week Plan

#### Week 1-2: Phase 0-1 (Documentation + LLM Abstraction)
**Revenue:** $0
**Tasks:**
- Complete Phase 0 documentation
- Implement LLM abstraction layer
- Set up infrastructure (Supabase, Cloud Run)

---

#### Week 3-4: Phase 2-4 (Multi-LLM Routing + Brain Fart Checker)
**Revenue:** $990/mo (10 Brain Fart Checker customers)
**Tasks:**
- Implement multi-LLM routing
- Build Brain Fart Checker MVP
- Create landing page
- Set up Stripe billing
- **Launch Brain Fart Checker** (invite-only)

**Acquisition:**
- Hacker News "Show HN" post (500 upvotes target)
- Twitter/X announcement (100 retweets target)
- Email 50 potential customers (20% conversion = 10 paid)

**Revenue:** 10 × $99 = $990/mo

---

#### Week 5-6: Phase 9 + 12 (Database + API)
**Revenue:** $2,400/mo (30 total paid customers)
**Tasks:**
- Implement multi-tenancy database
- Build REST API (core endpoints)
- Create API documentation
- **Open beta signup** (web-based, no CLI required)

**Acquisition:**
- Product Hunt launch (200 signups target)
- Blog post: "How we built an AI agent platform in 6 weeks"
- Reddit posts (r/SideProject, r/LangChain)

**Conversion:**
- 200 signups × 10% paid = 20 new paid customers
- **Total:** 30 paid (10 Brain Fart + 20 Pro)
- **MRR:** (10 × $99) + (20 × $49) = $2,400

---

#### Week 7-8: Phase 8 (Web UI)
**Revenue:** $6,000/mo (100 total paid customers)
**Tasks:**
- Build Next.js web UI
- Agent builder interface
- Dashboard and analytics
- Marketplace browser
- **Public beta launch**

**Acquisition:**
- Product Hunt (again, with web UI)
- LangChain community showcase
- YouTube tutorial series (5 videos)
- Twitter/X ads ($1,000 budget)

**Conversion:**
- 700 new signups × 10% = 70 new paid
- **Total:** 100 paid
- **MRR:** (20 × $99 Brain Fart) + (75 × $49 Pro) + (5 × $299 Enterprise) = $6,655

---

#### Week 9-10: Marketplace + Growth
**Revenue:** $10,000/mo (200 total paid customers)
**Tasks:**
- Launch marketplace
- Seed 20 high-quality templates
- Implement revenue sharing
- Run growth experiments

**Acquisition:**
- Marketplace templates drive virality
- Influencer partnerships (3 AI YouTubers)
- Paid ads ($2,000 budget)
- Referral program (20% off for referrer + referee)

**Conversion:**
- 1,000 new signups × 10% = 100 new paid
- **Total:** 200 paid
- **MRR:** (40 × $99) + (150 × $49) + (10 × $299) = $10,840

**✅ Goal Achieved: $10K MRR by Day 90**

---

#### Week 11-12: Optimization + Retention
**Revenue:** $12,000/mo (240 total paid customers)
**Tasks:**
- Improve onboarding (increase activation)
- Reduce churn (add usage alerts)
- Optimize pricing (A/B test $39 vs $49)
- Build customer success playbook

**Growth:**
- Focus on retention (reduce 5% to 3% monthly churn)
- Upsell free users (email campaigns)
- Expand Enterprise sales (manual outreach)

**Conversion:**
- Retain 95% of existing (190 retained)
- Add 50 new paid
- **Total:** 240 paid
- **MRR:** $12,000

---

### 90-Day Metrics Tracker

| Week | New Signups | Total Free | New Paid | Total Paid | MRR | ARR Run Rate |
|------|-------------|-----------|----------|-----------|-----|--------------|
| 1-2 | 50 | 50 | 0 | 0 | $0 | $0 |
| 3-4 | 100 | 150 | 10 | 10 | $990 | $11,880 |
| 5-6 | 200 | 350 | 20 | 30 | $2,400 | $28,800 |
| 7-8 | 700 | 1,050 | 70 | 100 | $6,655 | $79,860 |
| 9-10 | 1,000 | 2,050 | 100 | 200 | $10,840 | $130,080 |
| 11-12 | 500 | 2,550 | 40 | 240 | $12,480 | $149,760 |

**90-Day Result:** $12,480 MRR (25% above $10K goal)

---

## Financial Scenarios

### Best Case Scenario (Aggressive Growth)

**Assumptions:**
- 15% free-to-paid conversion (vs 10% base case)
- 2% monthly churn (vs 3% base case)
- 30% annual plan adoption (vs 20% base case)
- Viral growth from marketplace

| Metric | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|----------|
| Free Users | 1,500 | 4,000 | 10,000 |
| Paid Users | 225 | 600 | 1,500 |
| MRR | $13,500 | $36,000 | $90,000 |
| ARR | $162,000 | $432,000 | $1,080,000 |

**Year 1 ARR:** $1.08M

---

### Base Case Scenario (Expected)

**Assumptions:**
- 10% free-to-paid conversion
- 3% monthly churn
- 20% annual plan adoption
- Steady organic growth

| Metric | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|----------|
| Free Users | 1,000 | 2,500 | 5,500 |
| Paid Users | 100 | 300 | 1,100 |
| MRR | $6,000 | $18,000 | $66,000 |
| ARR | $72,000 | $216,000 | $792,000 |

**Year 1 ARR:** $792K

---

### Worst Case Scenario (Conservative)

**Assumptions:**
- 5% free-to-paid conversion
- 5% monthly churn
- 10% annual plan adoption
- Slow organic growth

| Metric | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|----------|
| Free Users | 500 | 1,500 | 4,000 |
| Paid Users | 25 | 75 | 200 |
| MRR | $1,500 | $4,500 | $12,000 |
| ARR | $18,000 | $54,000 | $144,000 |

**Year 1 ARR:** $144K

---

### Scenario Comparison

| Scenario | Year 1 ARR | Probability | Action Required |
|----------|-----------|-------------|-----------------|
| **Best Case** | $1,080,000 | 20% | Product-market fit + viral growth |
| **Base Case** | $792,000 | 60% | Solid execution, steady growth |
| **Worst Case** | $144,000 | 20% | Pivot or double down on acquisition |

**Expected Value (Weighted Average):**
```
EV = (0.20 × $1,080K) + (0.60 × $792K) + (0.20 × $144K)
EV = $216K + $475K + $29K = $720K
```

**Conclusion:** Expected Year 1 ARR is $720K with 80% confidence of achieving at least $144K.

---

## Key Metrics & KPIs

### North Star Metric
**Monthly Recurring Revenue (MRR)** - The single metric that captures platform health

**Target Progression:**
- Month 1: $990
- Month 3: $10,000 (10x growth)
- Month 6: $25,000 (2.5x growth)
- Month 12: $50,000 (2x growth)
- Month 24: $150,000 (3x growth)
- Month 36: $400,000 (2.7x growth)

---

### Acquisition Metrics

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| **Website Traffic** | Unique visitors/month | 10K (M3), 50K (M12) | Google Analytics |
| **Signup Rate** | Signups ÷ Visitors | 10-15% | Funnels |
| **Activation Rate** | Created 1st agent ÷ Signups | 50-70% | Onboarding analytics |
| **CAC** | Marketing spend ÷ New customers | <$150 | Finance dashboard |
| **Payback Period** | Months to recover CAC | <4 months | Cohort analysis |

---

### Engagement Metrics

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| **DAU** | Daily active users | 30% of paid | Product analytics |
| **MAU** | Monthly active users | 80% of paid | Product analytics |
| **Runs per User** | Avg agent runs/month | 150 | Usage dashboard |
| **Session Duration** | Avg time in app | 15 minutes | Product analytics |
| **Feature Adoption** | % using marketplace | 40% | Feature flags |

---

### Revenue Metrics

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| **MRR** | Monthly recurring revenue | $66K (M12) | Stripe dashboard |
| **ARR** | Annual recurring revenue | $792K (M12) | MRR × 12 |
| **ARPA** | Avg revenue per account | $60/month | MRR ÷ Paid users |
| **Expansion MRR** | Upgrades - Downgrades | 5% of MRR | Cohort analysis |
| **Annual Plan %** | % on annual plans | 20% | Subscription analytics |

---

### Retention Metrics

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| **Churn Rate** | % customers lost/month | <3% | Cohort analysis |
| **Revenue Churn** | % MRR lost/month | <2% | Finance dashboard |
| **Net Retention** | (Start MRR + Expansion - Churn) ÷ Start MRR | >100% | Cohort analysis |
| **LTV** | Customer lifetime value | $1,600 | LTV formula |
| **LTV/CAC** | Ratio of LTV to CAC | >6:1 | Financial model |

---

### Product Metrics

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| **Agents Created** | Total agents built | 10K (M12) | Database count |
| **Templates Published** | Marketplace templates | 100 (M12) | Marketplace dashboard |
| **API Requests** | Total API calls/day | 1M (M12) | API analytics |
| **Avg Response Time** | API latency (p95) | <200ms | Monitoring |
| **Error Rate** | % failed requests | <0.1% | Error tracking |

---

### Financial Health Metrics

| Metric | Definition | Target | Measurement |
|--------|-----------|--------|-------------|
| **Gross Margin** | (Revenue - COGS) ÷ Revenue | >75% | Financial model |
| **Burn Rate** | Monthly cash consumption | -$5K (M3), $20K (M12) | Cash flow statement |
| **Runway** | Months until $0 cash | 12+ months | Cash ÷ Burn rate |
| **Revenue Growth** | Month-over-month % | 20% (avg) | MRR tracking |
| **Rule of 40** | Growth rate + Profit margin | >40% | Financial dashboard |

---

### Milestone Metrics

| Milestone | Metric | Target Date | Status |
|-----------|--------|-------------|--------|
| **Brain Fart Launch** | 10 paid customers | Month 1 | 🔲 |
| **Product Hunt** | #1 Product of the Day | Month 2 | 🔲 |
| **$10K MRR** | 200 paid customers | Month 3 | 🔲 |
| **Break-Even** | 276 paid customers | Month 6 | 🔲 |
| **$25K MRR** | 500 paid customers | Month 6 | 🔲 |
| **$50K MRR** | 1,000 paid customers | Month 12 | 🔲 |
| **Profitability** | Positive net income | Month 12 | 🔲 |
| **$1M ARR** | $83K MRR | Month 15 | 🔲 |

---

## Summary

### Business Model Strengths

1. **High Gross Margins (80%)** - SaaS with efficient LLM routing
2. **Strong Unit Economics (LTV/CAC = 8:1)** - Sustainable growth
3. **Multiple Revenue Streams** - Subscriptions, marketplace, services
4. **Viral Growth Potential** - Marketplace creates network effects
5. **Scalable Infrastructure** - Serverless, auto-scaling

### Key Assumptions

1. **10% free-to-paid conversion** - Industry standard for PLG SaaS
2. **3% monthly churn** - Healthy for early-stage B2B SaaS
3. **$60 blended ARPA** - Mix of Free, Pro, Enterprise
4. **$150 CAC** - Primarily organic + low-cost paid
5. **80% gross margin** - LLM cost optimization

### Risks to Monitor

1. **LLM cost increases** - Provider price hikes (mitigate with multi-LLM)
2. **Churn spikes** - Product-market fit issues (monitor NPS)
3. **CAC inflation** - Paid ads get expensive (focus on organic)
4. **Marketplace abuse** - Malicious templates (moderation required)
5. **Enterprise sales cycle** - Longer than expected (build pipeline early)

### Next Actions

1. **Complete Phase 0** - Finish documentation (3 more docs)
2. **Launch Brain Fart Checker** - First revenue by Month 1
3. **Achieve $10K MRR** - 200 paid customers by Month 3
4. **Reach profitability** - Break-even by Month 6
5. **Scale to $50K MRR** - 1,000 customers by Month 12

---

**Document Status:** Phase 0 - Business Model Complete
**Next Document:** `docs/00_api_design.md` - REST API specification (50+ endpoints)

# TAB 2: FRONTEND COMPLETE
# Copy everything below into Claude Code CLI

You are Tab 2 in a 3-tab sprint to build Rivet - AI-powered CMMS for field technicians.

## AUTONOMOUS MODE SETTINGS
- Auto-accept all file edits
- Auto-accept bash commands except: rm -rf, sudo, DROP, DELETE
- Commit after each completed phase

## YOUR IDENTITY
- Workstream: Frontend + Payments
- Branch: frontend-complete
- Focus: Landing Page, Stripe Checkout, Vercel Deploy

## FIRST ACTIONS
```bash
cd "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
git checkout -b frontend-complete
mkdir -p rivet-landing
cd rivet-landing
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
git add -A && git commit -m "frontend: init next.js" && git push -u origin frontend-complete
```

---

## PHASE 1: PROJECT SETUP (Day 1)

### Task 1.1: Install Dependencies
```bash
npm install stripe @stripe/stripe-js lucide-react
```

### Task 1.2: Environment Variables
Create `.env.local`:
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_TELEGRAM_BOT_URL=https://t.me/RivetCEOBot
NEXT_PUBLIC_API_URL=https://your-api.com
```

### Task 1.3: Tailwind Config
Update `tailwind.config.ts`:
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        rivet: {
          orange: "#FF6B35",
          dark: "#1a1a2e",
          gray: "#16213e",
          light: "#e8e8e8",
        },
      },
    },
  },
  plugins: [],
};
export default config;
```

**COMMIT:**
```bash
git add -A && git commit -m "frontend: project setup" && git push
```

---

## PHASE 2: LANDING PAGE (Day 1-2)

### Task 2.1: Layout
Replace `src/app/layout.tsx`:
```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Rivet - AI-Powered CMMS for Field Technicians",
  description: "Voice-first maintenance management. Upload prints, get instant answers, create work orders by speaking.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

### Task 2.2: Main Page
Replace `src/app/page.tsx`:
```tsx
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import HowItWorks from "@/components/HowItWorks";
import Pricing from "@/components/Pricing";
import CTA from "@/components/CTA";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-rivet-dark text-white">
      <Hero />
      <Features />
      <HowItWorks />
      <Pricing />
      <CTA />
      <Footer />
    </main>
  );
}
```

### Task 2.3: Hero Component
Create `src/components/Hero.tsx`:
```tsx
import Link from "next/link";
import { Mic, FileText, Wrench } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative py-20 px-4 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-rivet-dark via-rivet-gray to-rivet-dark" />
      
      <div className="relative max-w-6xl mx-auto text-center">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center gap-3">
            <Wrench className="w-12 h-12 text-rivet-orange" />
            <span className="text-4xl font-bold">Rivet</span>
          </div>
        </div>
        
        {/* Headline */}
        <h1 className="text-5xl md:text-7xl font-bold mb-6">
          Your AI <span className="text-rivet-orange">Maintenance Assistant</span>
        </h1>
        
        <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
          Voice-first CMMS for field technicians. Upload prints, get instant answers, 
          create work orders by speaking.
        </p>
        
        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-4 mb-12">
          <div className="flex items-center gap-2 bg-rivet-gray px-4 py-2 rounded-full">
            <Mic className="w-5 h-5 text-rivet-orange" />
            <span>Voice Commands</span>
          </div>
          <div className="flex items-center gap-2 bg-rivet-gray px-4 py-2 rounded-full">
            <FileText className="w-5 h-5 text-rivet-orange" />
            <span>Print Analysis</span>
          </div>
          <div className="flex items-center gap-2 bg-rivet-gray px-4 py-2 rounded-full">
            <Wrench className="w-5 h-5 text-rivet-orange" />
            <span>Work Orders</span>
          </div>
        </div>
        
        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/pricing"
            className="bg-rivet-orange hover:bg-orange-600 text-white px-8 py-4 rounded-lg text-lg font-semibold transition"
          >
            Start Free Trial
          </Link>
          <Link
            href={process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "#"}
            className="border border-white hover:bg-white hover:text-rivet-dark px-8 py-4 rounded-lg text-lg font-semibold transition"
          >
            Try on Telegram
          </Link>
        </div>
      </div>
    </section>
  );
}
```

### Task 2.4: Features Component
Create `src/components/Features.tsx`:
```tsx
import { MessageSquare, Upload, Search, Shield, Zap, Database } from "lucide-react";

const features = [
  {
    icon: MessageSquare,
    title: "Voice-First",
    description: "Speak naturally to create work orders, query equipment, and get troubleshooting help."
  },
  {
    icon: Upload,
    title: "Upload Prints",
    description: "Upload electrical prints and schematics. Ask questions about any circuit or component."
  },
  {
    icon: Search,
    title: "Smart Search",
    description: "AI understands equipment context. Ask about PowerFlex faults and get manual excerpts."
  },
  {
    icon: Database,
    title: "Manual Library",
    description: "Build your searchable library of OEM manuals. Get answers with page citations."
  },
  {
    icon: Shield,
    title: "Safety First",
    description: "Every response includes relevant safety warnings. LOTO reminders built in."
  },
  {
    icon: Zap,
    title: "Instant Answers",
    description: "No more digging through binders. Get the right info in seconds."
  }
];

export default function Features() {
  return (
    <section className="py-20 px-4 bg-rivet-gray">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-4">
          Built for <span className="text-rivet-orange">Field Technicians</span>
        </h2>
        <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
          Everything you need to troubleshoot faster and document better.
        </p>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, i) => (
            <div key={i} className="bg-rivet-dark p-6 rounded-xl">
              <feature.icon className="w-10 h-10 text-rivet-orange mb-4" />
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

### Task 2.5: How It Works
Create `src/components/HowItWorks.tsx`:
```tsx
export default function HowItWorks() {
  const steps = [
    { num: "1", title: "Open Telegram", desc: "Start a chat with @RivetCEOBot" },
    { num: "2", title: "Describe the Issue", desc: "Text or voice: 'PowerFlex showing F004'" },
    { num: "3", title: "Get Instant Help", desc: "Receive manual excerpts, troubleshooting steps, safety warnings" },
  ];
  
  return (
    <section className="py-20 px-4">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-12">
          How It <span className="text-rivet-orange">Works</span>
        </h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, i) => (
            <div key={i} className="text-center">
              <div className="w-16 h-16 bg-rivet-orange rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                {step.num}
              </div>
              <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
              <p className="text-gray-400">{step.desc}</p>
            </div>
          ))}
        </div>
        
        {/* Demo conversation */}
        <div className="mt-16 max-w-2xl mx-auto bg-rivet-gray rounded-xl p-6">
          <div className="space-y-4">
            <div className="bg-blue-600 text-white p-3 rounded-lg rounded-br-none max-w-xs ml-auto">
              PowerFlex 525 showing fault F004
            </div>
            <div className="bg-rivet-dark p-4 rounded-lg rounded-bl-none max-w-md">
              <p className="font-semibold text-rivet-orange">🔧 PowerFlex 525 - F004</p>
              <p className="text-sm mt-2">
                <strong>DC Bus Undervoltage</strong><br/>
                • Check incoming power (460V ±10%)<br/>
                • Verify DC bus capacitor health<br/>
                • Inspect L1/L2/L3 connections
              </p>
              <p className="text-xs text-yellow-400 mt-2">
                ⚠️ Wait 5+ min after power off - capacitors retain charge
              </p>
              <p className="text-xs text-gray-500 mt-2">
                📄 PowerFlex 520 Manual p.47
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
```

**COMMIT:**
```bash
git add -A && git commit -m "frontend: landing page components" && git push
```

---

## PHASE 3: PRICING + STRIPE (Day 2-3)

### Task 3.1: Pricing Component
Create `src/components/Pricing.tsx`:
```tsx
"use client";
import { Check } from "lucide-react";
import { useState } from "react";

const plans = [
  {
    name: "Beta",
    price: "Free",
    period: "",
    description: "Limited time beta access",
    features: [
      "Voice & text commands",
      "5 print uploads/month",
      "Basic troubleshooting",
      "Email support"
    ],
    cta: "Join Beta",
    priceId: null,
    popular: false
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For individual technicians",
    features: [
      "Everything in Beta",
      "Unlimited print uploads",
      "Full manual library access",
      "Work order creation",
      "Priority support"
    ],
    cta: "Start Trial",
    priceId: "price_pro_monthly",
    popular: true
  },
  {
    name: "Team",
    price: "$99",
    period: "/month",
    description: "For maintenance teams",
    features: [
      "Everything in Pro",
      "Up to 10 users",
      "Shared print library",
      "Team work orders",
      "Admin dashboard",
      "Phone support"
    ],
    cta: "Contact Sales",
    priceId: "price_team_monthly",
    popular: false
  }
];

export default function Pricing() {
  const [loading, setLoading] = useState<string | null>(null);
  
  const handleCheckout = async (priceId: string | null, planName: string) => {
    if (!priceId) {
      // Beta - redirect to Telegram
      window.open(process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL, "_blank");
      return;
    }
    
    if (planName === "Team") {
      // Contact sales
      window.location.href = "mailto:sales@rivet.app?subject=Team Plan Inquiry";
      return;
    }
    
    setLoading(planName);
    
    try {
      const res = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priceId }),
      });
      
      const { url } = await res.json();
      window.location.href = url;
    } catch (error) {
      console.error("Checkout error:", error);
      setLoading(null);
    }
  };
  
  return (
    <section id="pricing" className="py-20 px-4 bg-rivet-gray">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-4">
          Simple <span className="text-rivet-orange">Pricing</span>
        </h2>
        <p className="text-gray-400 text-center mb-12">
          Start free, upgrade when you need more.
        </p>
        
        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`bg-rivet-dark rounded-xl p-8 ${
                plan.popular ? "ring-2 ring-rivet-orange" : ""
              }`}
            >
              {plan.popular && (
                <span className="bg-rivet-orange text-sm px-3 py-1 rounded-full">
                  Most Popular
                </span>
              )}
              
              <h3 className="text-2xl font-bold mt-4">{plan.name}</h3>
              <div className="mt-4">
                <span className="text-4xl font-bold">{plan.price}</span>
                <span className="text-gray-400">{plan.period}</span>
              </div>
              <p className="text-gray-400 mt-2">{plan.description}</p>
              
              <ul className="mt-6 space-y-3">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <Check className="w-5 h-5 text-rivet-orange" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <button
                onClick={() => handleCheckout(plan.priceId, plan.name)}
                disabled={loading === plan.name}
                className={`w-full mt-8 py-3 rounded-lg font-semibold transition ${
                  plan.popular
                    ? "bg-rivet-orange hover:bg-orange-600"
                    : "bg-rivet-gray hover:bg-gray-700 border border-gray-600"
                }`}
              >
                {loading === plan.name ? "Loading..." : plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

### Task 3.2: Stripe Checkout API
Create `src/app/api/checkout/route.ts`:
```typescript
import { NextResponse } from "next/server";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2023-10-16",
});

export async function POST(req: Request) {
  try {
    const { priceId } = await req.json();
    
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      payment_method_types: ["card"],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/#pricing`,
    });
    
    return NextResponse.json({ url: session.url });
  } catch (error: any) {
    console.error("Stripe error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
```

### Task 3.3: Success Page
Create `src/app/success/page.tsx`:
```tsx
import Link from "next/link";
import { CheckCircle } from "lucide-react";

export default function SuccessPage() {
  return (
    <main className="min-h-screen bg-rivet-dark text-white flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-6" />
        
        <h1 className="text-4xl font-bold mb-4">Welcome to Rivet Pro!</h1>
        
        <p className="text-gray-300 mb-8">
          Your subscription is active. Open Telegram to start using your new features.
        </p>
        
        <div className="space-y-4">
          <Link
            href={process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "#"}
            className="block bg-rivet-orange hover:bg-orange-600 px-8 py-4 rounded-lg text-lg font-semibold transition"
          >
            Open Telegram Bot
          </Link>
          
          <Link
            href="/"
            className="block text-gray-400 hover:text-white transition"
          >
            Back to Home
          </Link>
        </div>
        
        <div className="mt-12 p-4 bg-rivet-gray rounded-lg text-left">
          <h3 className="font-semibold mb-2">Quick Start:</h3>
          <ol className="text-sm text-gray-300 space-y-1">
            <li>1. Open @RivetCEOBot on Telegram</li>
            <li>2. Send /start to link your account</li>
            <li>3. Upload your first print with /upload_print</li>
          </ol>
        </div>
      </div>
    </main>
  );
}
```

**COMMIT:**
```bash
git add -A && git commit -m "frontend: pricing + stripe checkout" && git push
```

---

## PHASE 4: REMAINING COMPONENTS (Day 3)

### Task 4.1: CTA Component
Create `src/components/CTA.tsx`:
```tsx
import Link from "next/link";

export default function CTA() {
  return (
    <section className="py-20 px-4">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-4xl font-bold mb-4">
          Ready to Work <span className="text-rivet-orange">Smarter</span>?
        </h2>
        <p className="text-gray-300 text-xl mb-8">
          Join hundreds of technicians using Rivet to troubleshoot faster.
        </p>
        
        <Link
          href={process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "#"}
          className="inline-block bg-rivet-orange hover:bg-orange-600 px-12 py-4 rounded-lg text-xl font-semibold transition"
        >
          Start Free on Telegram
        </Link>
      </div>
    </section>
  );
}
```

### Task 4.2: Footer Component
Create `src/components/Footer.tsx`:
```tsx
import { Wrench } from "lucide-react";

export default function Footer() {
  return (
    <footer className="py-12 px-4 bg-rivet-gray border-t border-gray-800">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <Wrench className="w-6 h-6 text-rivet-orange" />
            <span className="text-xl font-bold">Rivet</span>
          </div>
          
          <div className="flex gap-8 text-gray-400">
            <a href="#" className="hover:text-white transition">Privacy</a>
            <a href="#" className="hover:text-white transition">Terms</a>
            <a href="mailto:support@rivet.app" className="hover:text-white transition">Support</a>
          </div>
        </div>
        
        <div className="mt-8 text-center text-gray-500 text-sm">
          © 2025 Rivet. Built for the field.
        </div>
      </div>
    </footer>
  );
}
```

**COMMIT:**
```bash
git add -A && git commit -m "frontend: CTA + footer" && git push
```

---

## PHASE 5: DEPLOY (Day 4)

### Task 5.1: Vercel Deploy
```bash
npm install -g vercel
vercel login
vercel --prod
```

### Task 5.2: Set Environment Variables in Vercel
Go to Vercel dashboard → Project → Settings → Environment Variables:
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`
- `NEXT_PUBLIC_TELEGRAM_BOT_URL`
- `NEXT_PUBLIC_APP_URL` (your vercel URL)

### Task 5.3: Stripe Webhook (Optional)
Create `src/app/api/webhook/route.ts`:
```typescript
import { NextResponse } from "next/server";
import Stripe from "stripe";
import { headers } from "next/headers";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2023-10-16",
});

export async function POST(req: Request) {
  const body = await req.text();
  const sig = headers().get("stripe-signature")!;
  
  let event: Stripe.Event;
  
  try {
    event = stripe.webhooks.constructEvent(
      body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 400 });
  }
  
  switch (event.type) {
    case "checkout.session.completed":
      const session = event.data.object as Stripe.Checkout.Session;
      // TODO: Provision user in backend
      console.log("New subscription:", session.customer_email);
      break;
      
    case "customer.subscription.deleted":
      // TODO: Downgrade user
      break;
  }
  
  return NextResponse.json({ received: true });
}
```

**FINAL COMMIT:**
```bash
git add -A && git commit -m "frontend: complete + deployed" && git push
```

---

## SUCCESS CRITERIA
- [ ] Landing page loads with Hero, Features, HowItWorks
- [ ] Pricing section shows 3 tiers
- [ ] Stripe checkout redirects correctly
- [ ] Success page shows and links to Telegram
- [ ] Deployed to Vercel

## TAB 2 COMPLETE
Frontend is live. Users can:
1. See landing page
2. Click pricing → Stripe checkout
3. After payment → Success → Open Telegram

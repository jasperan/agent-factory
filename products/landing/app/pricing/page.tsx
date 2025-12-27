"use client";

import { useState } from "react";
import Link from "next/link";

interface PricingTier {
  name: string;
  price: string;
  period: string;
  popular?: boolean;
  features: string[];
  cta: string;
  priceId: string;
}

export default function PricingPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const tiers: PricingTier[] = [
    {
      name: "Basic",
      price: "$20",
      period: "/tech/month",
      features: [
        "Voice work orders via Telegram",
        "Up to 5 equipment prints",
        "Email support"
      ],
      cta: "Start Free Trial",
      priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_BASIC || "price_basic"
    },
    {
      name: "Pro",
      price: "$40",
      period: "/tech/month",
      popular: true,
      features: [
        "Everything in Basic",
        "Unlimited prints",
        "Chat with Print (AI Q&A)",
        "Priority support"
      ],
      cta: "Start Free Trial",
      priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_PRO || "price_pro"
    },
    {
      name: "Enterprise",
      price: "$99",
      period: "/tech/month",
      features: [
        "Everything in Pro",
        "Predictive maintenance AI",
        "API access",
        "SSO/SAML",
        "Dedicated support"
      ],
      cta: "Contact Sales",
      priceId: process.env.NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE || "price_enterprise"
    }
  ];

  async function handleCheckout(tier: PricingTier) {
    if (!email) {
      setError("Please enter your email address");
      return;
    }

    if (tier.name === "Enterprise") {
      window.location.href = `mailto:sales@rivet.com?subject=Enterprise Inquiry&body=Email: ${email}`;
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/checkout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          tier: tier.name.toLowerCase()
        }),
      });

      if (!response.ok) {
        throw new Error("Checkout failed");
      }

      const data = await response.json();
      window.location.href = data.checkout_url;
    } catch (err) {
      setError("Something went wrong. Please try again.");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-50 py-20 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">
            ← Back to Home
          </Link>
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            14-day free trial. No credit card required.
          </p>
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="px-4 py-3 rounded-lg border border-gray-300 text-lg max-w-md w-full"
          />
          {error && <p className="text-red-600 mt-2">{error}</p>}
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {tiers.map((tier, index) => (
            <div
              key={index}
              className={`bg-white rounded-lg shadow-lg p-8 relative ${
                tier.popular ? "ring-2 ring-blue-600" : ""
              }`}
            >
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                  Most Popular
                </div>
              )}
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {tier.name}
              </h2>
              <div className="mb-6">
                <span className="text-4xl font-bold text-gray-900">
                  {tier.price}
                </span>
                <span className="text-gray-600">{tier.period}</span>
              </div>
              <ul className="space-y-3 mb-8">
                {tier.features.map((feature, i) => (
                  <li key={i} className="flex items-start">
                    <span className="text-green-500 mr-2">✓</span>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleCheckout(tier)}
                disabled={loading}
                className={`w-full py-3 rounded-lg font-semibold transition ${
                  tier.popular
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : "bg-gray-100 text-gray-900 hover:bg-gray-200"
                } disabled:opacity-50`}
              >
                {loading ? "Processing..." : tier.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

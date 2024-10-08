// src/Components/ChangeTier.js
import React, { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import "./ChangeTier.css";

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

function ChangeTier({ username, setTier }) {
  const [selectedTier, setSelectedTier] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const tiers = [
    {
      value: "free",
      label: "Free",
      price: "Free",
      features: ["2 exams per week"],
    },
    {
      value: "gold",
      label: "Weekly Plan",
      price: "$4.99/week",
      features: [
        "6 exams per week",
        "Automated Grading",
        "Cancel anytime",
      ],
    },
    {
      value: "diamond",
      label: "Monthly Plan",
      price: "$9.99/month",
      features: [
        "6 exams per week",
        "Automated Grading",
        "Cancel anytime",
      ],
    },
  ];

  const handleTierSelect = (tierValue) => {
    setSelectedTier(tierValue);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsProcessing(true);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/change_tier`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, tier: selectedTier }),
      });

      const data = await response.json();

      if (data.sessionId) {
        const stripe = await stripePromise;
        await stripe.redirectToCheckout({ sessionId: data.sessionId });
      } else if (data.free) {
        // Update the tier immediately if it's free
        setTier("free");
        window.location.href = "/";
      } else {
        alert("Failed to create Stripe session.");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="change-tier-container">
      <h1>Change Your Subscription Tier</h1>
      <form onSubmit={handleSubmit}>
        {/* Tier Selection */}
        <div className="tier-options">
          {tiers.map((tier) => (
            <div
              key={tier.value}
              className={`tier-card ${
                selectedTier === tier.value ? "selected" : ""
              }`}
              onClick={() => handleTierSelect(tier.value)}
            >
              <h2>{tier.label}</h2>
              <p className="price">{tier.price}</p>
              <ul>
                {tier.features.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Submit Button */}
        <button type="submit" disabled={!selectedTier || isProcessing}>
          {isProcessing ? "Processing..." : "Change Tier"}
        </button>
      </form>
    </div>
  );
}

export default ChangeTier;

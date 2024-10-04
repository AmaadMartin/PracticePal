// src/Components/Signup.js

import React, { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import "./Signup.css";


const stripePromise = loadStripe(
    process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY
); // Replace with your Stripe Publishable Key

function Signup() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    tier: "free",
  });
  const [isProcessing, setIsProcessing] = useState(false);

  const tiers = [
    {
      value: "free",
      label: "Free",
      price: "Free",
      features: ["Basic practice exams", "Access to limited materials"],
    },
    {
      value: "gold",
      label: "Gold",
      price: "$8.99/month",
      features: [
        "Everything in Free",
        "Advanced practice exams",
        "Priority support",
      ],
    },
    {
      value: "diamond",
      label: "Diamond",
      price: "$18.99/month",
      features: [
        "Everything in Gold",
        "Personalized coaching",
        "Exclusive content",
      ],
    },
  ];

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleTierSelect = (tierValue) => {
    setFormData({
      ...formData,
      tier: tierValue,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsProcessing(true);

    try {
      const response = await fetch("https://practicepal.onrender.com/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      const data = await response.json();

      if (data.sessionId) {
        const stripe = await stripePromise;
        await stripe.redirectToCheckout({ sessionId: data.sessionId });
      } else if (data.free) {
        window.location.href = "/login";
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
    <div className="signup-container">
      <h1>Sign Up</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          name="email"
          placeholder="Enter your email"
          value={formData.email}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Create a password"
          value={formData.password}
          onChange={handleChange}
          required
        />

        <div className="tier-options">
          {tiers.map((tier) => (
            <div
              key={tier.value}
              className={`tier-card ${
                formData.tier === tier.value ? "selected" : ""
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

        <button type="submit" disabled={isProcessing}>
          {isProcessing ? "Processing..." : "Sign Up"}
        </button>
      </form>
    </div>
  );
}

export default Signup;

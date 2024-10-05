// src/Components/PurchaseCredits.js

import React, { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import "./PurchaseCredits.css";

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

function PurchaseCredits({ username }) {
  const [selectedOption, setSelectedOption] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const creditOptions = [
    {
      value: "1_credit",
      label: "1 Credit",
      price: "$2.99",
      credits: 1,
    },
    {
      value: "10_credits",
      label: "10 Credits",
      price: "$9.99",
      credits: 10,
    },
    {
      value: "100_credits",
      label: "100 Credits",
      price: "$49.99",
      credits: 100,
    },
  ];

  const handleOptionSelect = (optionValue) => {
    setSelectedOption(optionValue);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsProcessing(true);

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/purchase_credits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, option: selectedOption }),
      });

      const data = await response.json();

      if (data.sessionId) {
        const stripe = await stripePromise;
        await stripe.redirectToCheckout({ sessionId: data.sessionId });
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
    <div className="purchase-credits-container">
      <h1>Purchase Exam Credits</h1>
      <form onSubmit={handleSubmit}>
        <div className="credit-options">
          {creditOptions.map((option) => (
            <div
              key={option.value}
              className={`credit-card ${selectedOption === option.value ? "selected" : ""}`}
              onClick={() => handleOptionSelect(option.value)}
            >
              <h2>{option.label}</h2>
              <p className="price">{option.price}</p>
            </div>
          ))}
        </div>

        <button type="submit" disabled={!selectedOption || isProcessing}>
          {isProcessing ? "Processing..." : "Purchase"}
        </button>
      </form>
    </div>
  );
}

export default PurchaseCredits;

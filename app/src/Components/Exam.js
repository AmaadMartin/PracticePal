// src/Components/Exam.js
import React, { useState, useEffect } from "react";
import Question from "./Question";
import "./Exam.css"; // Import the corresponding CSS file

function Exam({ selectedExam, examQuestions, exams, username, tier }) {
  // Find the exam name based on the selectedExam ID
  const examName =
    exams.find((exam) => exam.id === selectedExam)?.name || "Practice Pal";

  // Default questions if no custom exam is selected
  const defaultQuestions = [];

  // Use questions from examQuestions if available
  const questions =
    (selectedExam != null && examQuestions[selectedExam]) || defaultQuestions;

  // State to store user's answers
  const [userAnswers, setUserAnswers] = useState({}); // { [questionIndex]: answer }

  // State to store submission result
  const [result, setResult] = useState(null); // { score: number, total: number, details: [...] }

  // State for submission loading
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handle answer changes from Question components
  const handleAnswerChange = (questionIndex, answer) => {
    setUserAnswers((prevAnswers) => ({
      ...prevAnswers,
      [questionIndex]: answer,
    }));
  };

  // Reset userAnswers and result when selectedExam changes
  useEffect(() => {
    // set answers as blank for all questions
    setUserAnswers({ ...questions.map((_, index) => "") });
    setResult(null);
    setIsSubmitting(false);
  }, [selectedExam]);

  // Handle submission
  const handleSubmit = async () => {
    // Prepare the payload
    const payload = {
      username: username,
      exam_id: selectedExam,
      answers: userAnswers, // { [questionIndex]: answer }
    };

    setIsSubmitting(true);
    setResult(null); // Reset previous result

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/grade_quiz`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Failed to grade quiz");
      }

      const data = await response.json();

      // Assume the API returns data like { score: number, total: number, details: [...] }
      setResult(data);
    } catch (error) {
      console.error("Error submitting exam:", error);
      alert("Failed to submit exam. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="exam-content">
      <h1>{examName}</h1>
      {questions.map((question, index) => (
        <Question
          key={index}
          question={question}
          index={index}
          onAnswerChange={handleAnswerChange}
          currentAnswer={userAnswers[index] || ""} // Pass the current answer
          resultDetail={result && result.details ? result.details[index] : null} // Pass the result detail if available
          tier={tier} // Pass the tier
        />
      ))}
      {selectedExam != null && (
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="submit-button"
        >
          {isSubmitting ? "Submitting..." : "Submit"}
        </button>
      )}
      {result && (
        <div className="result-summary">
          <h2>
            Score: {result.score} / {result.total}
          </h2>
        </div>
      )}
      {/* If user is free tell them to upgrade to see questions answers */}
      {result && tier === "free" && (
        <div className="upgrade-message">
          <p>
            Upgrade to see the correct answers for each question.
          </p>
        </div>
      )}
    </div>
  );
}

export default Exam;

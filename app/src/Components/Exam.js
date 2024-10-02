// src/Exam.js
import React from 'react';
import Question from './Question';

function Exam({ selectedExam, examQuestions }) {
  // Default questions if no custom exam is selected
  const defaultQuestions = [
    // ... your default questions here
  ];

  // Use questions from examQuestions if available
  const questions =
    examQuestions[selectedExam] || defaultQuestions;

  return (
    <div className="exam-content">
      <h1>{selectedExam}</h1>
      {questions.map((question, index) => (
        <Question key={index} question={question} index={index} />
      ))}
    </div>
  );
}

export default Exam;

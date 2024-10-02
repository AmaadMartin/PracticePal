// src/Question.js
import React from 'react';

function Question({ question, index }) {
  const { question: questionText, type, answer_choices } = question;

  return (
    <div className="question">
      <p>
        <strong>
          {index + 1}. {questionText}
        </strong>
      </p>
      {type === 'mc' && answer_choices
        ? answer_choices.map((option, optionIndex) => (
            <div key={optionIndex} className="option">
              <input
                type="radio"
                id={`q${index}_option${optionIndex}`}
                name={`q${index}`}
                value={option}
              />
              <label htmlFor={`q${index}_option${optionIndex}`}>
                {option}
              </label>
            </div>
          ))
        : type === 'oe' && (
            <div className="option">
              <textarea
                id={`q${index}_textarea`}
                name={`q${index}`}
                rows="4"
                cols="50"
              ></textarea>
            </div>
          )}
    </div>
  );
}

export default Question;

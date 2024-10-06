// src/Components/Question.js
import React from 'react';
import './Question.css'; // Import the corresponding CSS file

function Question({ question, index, onAnswerChange, currentAnswer, resultDetail, tier }) {
  const { question: questionText, type, answer_choices } = question;

  const handleChange = (e) => {
    const value = e.target.value;
    onAnswerChange(index, value);
  };

  // Determine the CSS class based on whether the answer is correct or incorrect
  let questionClass = 'question';
  let feedbackClass = 'feedback';

  if (resultDetail && (tier === 'gold' || tier === 'diamond')) {
    if (resultDetail.correct === true) {
      questionClass += ' correct-answer';
      feedbackClass += ' correct-feedback';
    } else if (resultDetail.correct === false) {
      questionClass += ' incorrect-answer';
      feedbackClass += ' incorrect-feedback';
    }
  }

  return (
    <div className={questionClass}>
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
                onChange={handleChange}
                checked={currentAnswer === option} // Controlled input
                disabled={!!resultDetail} // Disable input after submission
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
                onChange={handleChange}
                value={currentAnswer} // Controlled input
                disabled={!!resultDetail} // Disable input after submission
              ></textarea>
            </div>
          )}
      {/* Display feedback based on tier */}
      {resultDetail && tier === 'gold' && (
        <div className={feedbackClass}>
          <p><strong>Correct Answer:</strong> {resultDetail.correct_answer}</p>
        </div>
      )}
      {resultDetail && tier === 'diamond' && (
        <div className={feedbackClass}>
          <p><strong>Correct Answer:</strong> {resultDetail.correct_answer}</p>
          <p><strong>Explanation:</strong> {resultDetail.explanation}</p>
        </div>
      )}
    </div>
  );
}

export default Question;

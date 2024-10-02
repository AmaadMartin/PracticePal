// src/CreateExam.js
import React, { useState } from "react";
import "./CreateExam.css";

function CreateExam({ setExams, setSelectedExam, setExamQuestions }) {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    const uploadedFiles = Array.from(e.dataTransfer.files);
    setFiles(uploadedFiles);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleFileUpload = async () => {
    setIsUploading(true);

    // Prepare form data
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      // Send files to the API
      const response = await fetch("http://localhost:8000/create_exam", {
        method: "POST",
        body: formData,
      });

      //   log the response
    //   console.log(response);

      const data = await response.json();

      // Assume the API returns an array of questions
      const questions = data.questions;

      console.log(questions);

      // Update exam data
      const newExamName = data.examName;
      setExamQuestions((prev) => ({
        ...prev,
        [newExamName]: questions,
      }));

      setExams((prev) => [...prev, newExamName]);
      setSelectedExam(newExamName);
    //   console.log("Exam created:", newExamName);

      // Redirect to the exam page
    //   window.location.href = "/";
    } catch (error) {
      console.error("Error uploading files:", error);
      alert("Failed to upload files. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="exam-content">
      <h1>Create New Exam</h1>
      <div className="dropzone" onDrop={handleDrop} onDragOver={handleDragOver}>
        {files.length === 0 ? (
          <p>Drag and drop files here, or click to select files</p>
        ) : (
          <ul>
            {files.map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        )}
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files))}
        />
      </div>
      <button
        onClick={handleFileUpload}
        disabled={files.length === 0 || isUploading}
        className="upload-button"
      >
        {isUploading ? "Uploading..." : "Create Exam"}
      </button>
    </div>
  );
}

export default CreateExam;

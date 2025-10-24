'use client';

import { useState } from 'react';
import axios from 'axios';

export default function SubmitPage() {
  const [rubricId, setRubricId] = useState('');
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleTranscriptChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setTranscriptFile(e.target.files[0]);
    }
  };

  const handleAudioChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setAudioFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!rubricId || !transcriptFile) {
      alert('Please select a rubric and upload a transcript');
      return;
    }

    setSubmitting(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const formData = new FormData();
      formData.append('rubric_id', rubricId);
      formData.append('transcript', transcriptFile);
      if (audioFile) {
        formData.append('audio', audioFile);
      }

      await axios.post(`${apiUrl}/grade`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setSuccess(true);
      setRubricId('');
      setTranscriptFile(null);
      setAudioFile(null);
      
      setTimeout(() => {
        window.location.href = '/grades';
      }, 2000);
    } catch (error) {
      console.error('Error submitting presentation:', error);
      alert('Error submitting presentation. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Submit Presentation</h1>
        <p className="text-gray-600 mt-2">Upload your case presentation for grading</p>
      </div>

      {success && (
        <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
          <div className="flex">
            <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <p className="ml-3 text-sm text-green-700">
              Presentation submitted successfully! Redirecting to grades...
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="card space-y-6">
        <div>
          <label className="label">Select Rubric</label>
          <select
            value={rubricId}
            onChange={(e) => setRubricId(e.target.value)}
            className="input"
            required
          >
            <option value="">Choose a rubric...</option>
            <option value="stroke_v1">Stroke Case Presentation</option>
            <option value="cardiology_v1">Cardiology Case Presentation</option>
            <option value="neurology_v1">Neurology Case Presentation</option>
          </select>
          <p className="text-sm text-gray-500 mt-2">
            Select the rubric that matches your presentation topic
          </p>
        </div>

        <div>
          <label className="label">Transcript (Required)</label>
          <input
            type="file"
            accept=".txt,.pdf,.doc,.docx"
            onChange={handleTranscriptChange}
            className="input"
            required
          />
          <p className="text-sm text-gray-500 mt-2">
            Upload your presentation transcript in TXT, PDF, or DOC format
          </p>
          {transcriptFile && (
            <p className="text-sm text-primary-600 mt-2">
              Selected: {transcriptFile.name}
            </p>
          )}
        </div>

        <div>
          <label className="label">Audio Recording (Optional)</label>
          <input
            type="file"
            accept=".mp3,.wav,.m4a"
            onChange={handleAudioChange}
            className="input"
          />
          <p className="text-sm text-gray-500 mt-2">
            Optionally upload an audio recording of your presentation
          </p>
          {audioFile && (
            <p className="text-sm text-primary-600 mt-2">
              Selected: {audioFile.name}
            </p>
          )}
        </div>

        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
          <div className="flex">
            <svg className="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <strong>Note:</strong> Your presentation will be automatically graded using our AI-powered system. 
                You'll receive detailed feedback on structure, content, reasoning, and more.
              </p>
            </div>
          </div>
        </div>

        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={submitting}
            className="btn-primary flex-1 disabled:opacity-50"
          >
            {submitting ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Submitting...
              </span>
            ) : (
              'Submit Presentation'
            )}
          </button>
          <button
            type="button"
            onClick={() => window.location.href = '/'}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}


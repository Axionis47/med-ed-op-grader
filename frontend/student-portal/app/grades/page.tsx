'use client';

import { useEffect, useState } from 'react';

interface Grade {
  id: string;
  rubric_title: string;
  score: number;
  submitted_at: string;
  graded_at: string;
  status: 'graded' | 'pending';
}

export default function GradesPage() {
  const [grades, setGrades] = useState<Grade[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedGrade, setSelectedGrade] = useState<Grade | null>(null);

  useEffect(() => {
    // Mock data
    setTimeout(() => {
      setGrades([
        {
          id: '1',
          rubric_title: 'Stroke Case Presentation',
          score: 92,
          submitted_at: '2024-10-23T10:00:00Z',
          graded_at: '2024-10-23T10:15:00Z',
          status: 'graded',
        },
        {
          id: '2',
          rubric_title: 'Cardiology Case',
          score: 88,
          submitted_at: '2024-10-20T14:30:00Z',
          graded_at: '2024-10-20T14:45:00Z',
          status: 'graded',
        },
        {
          id: '3',
          rubric_title: 'Neurology Case',
          score: 0,
          submitted_at: '2024-10-18T09:00:00Z',
          graded_at: '',
          status: 'pending',
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadge = (grade: Grade) => {
    if (grade.status === 'pending') return 'bg-yellow-100 text-yellow-800';
    if (grade.score >= 90) return 'bg-green-100 text-green-800';
    if (grade.score >= 80) return 'bg-blue-100 text-blue-800';
    if (grade.score >= 70) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">My Grades</h1>
        <a href="/submit" className="btn-primary">
          + Submit New
        </a>
      </div>

      {/* Grades Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {grades.map((grade) => (
          <div key={grade.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-3">
              <h3 className="text-lg font-bold text-gray-900">{grade.rubric_title}</h3>
              <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getScoreBadge(grade)}`}>
                {grade.status === 'pending' ? 'Pending' : `${grade.score}%`}
              </span>
            </div>
            
            <div className="space-y-2 text-sm text-gray-600 mb-4">
              <div className="flex justify-between">
                <span>Submitted:</span>
                <span>{new Date(grade.submitted_at).toLocaleDateString()}</span>
              </div>
              {grade.status === 'graded' && (
                <div className="flex justify-between">
                  <span>Graded:</span>
                  <span>{new Date(grade.graded_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>

            {grade.status === 'graded' ? (
              <button
                onClick={() => setSelectedGrade(grade)}
                className="btn-primary w-full text-sm"
              >
                View Feedback
              </button>
            ) : (
              <button disabled className="btn-secondary w-full text-sm opacity-50 cursor-not-allowed">
                Grading in Progress...
              </button>
            )}
          </div>
        ))}
      </div>

      {grades.length === 0 && (
        <div className="card text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No submissions yet</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by submitting your first presentation.</p>
          <div className="mt-6">
            <a href="/submit" className="btn-primary">
              Submit Presentation
            </a>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedGrade && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold">{selectedGrade.rubric_title}</h2>
                <p className="text-gray-600">Submitted {new Date(selectedGrade.submitted_at).toLocaleDateString()}</p>
              </div>
              <button
                onClick={() => setSelectedGrade(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-700 font-medium">Overall Score</span>
                <span className={`text-3xl font-bold ${getScoreColor(selectedGrade.score)}`}>
                  {selectedGrade.score}%
                </span>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-3">Score Breakdown</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span>Structure & Organization</span>
                    <span className="font-semibold">95%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span>Content Accuracy</span>
                    <span className="font-semibold">90%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span>Clinical Reasoning</span>
                    <span className="font-semibold">92%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <span>Summary Quality</span>
                    <span className="font-semibold">88%</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-3">Strengths</h3>
                <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                    <li>Excellent organization and structure</li>
                    <li>Comprehensive coverage of key points</li>
                    <li>Strong clinical reasoning demonstrated</li>
                  </ul>
                </div>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-3">Areas for Improvement</h3>
                <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                    <li>Consider expanding differential diagnosis discussion</li>
                    <li>Include more specific treatment details</li>
                  </ul>
                </div>
              </div>

              <button
                onClick={() => setSelectedGrade(null)}
                className="btn-primary w-full"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


'use client';

import { useEffect, useState } from 'react';

interface Result {
  id: string;
  student_name: string;
  rubric_title: string;
  score: number;
  submitted_at: string;
  graded_at: string;
}

export default function ResultsPage() {
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedResult, setSelectedResult] = useState<Result | null>(null);

  useEffect(() => {
    // Mock data
    setTimeout(() => {
      setResults([
        {
          id: '1',
          student_name: 'John Doe',
          rubric_title: 'Stroke Case Presentation',
          score: 92,
          submitted_at: '2024-10-23T10:00:00Z',
          graded_at: '2024-10-23T10:15:00Z',
        },
        {
          id: '2',
          student_name: 'Jane Smith',
          rubric_title: 'Cardiology Case',
          score: 88,
          submitted_at: '2024-10-22T14:30:00Z',
          graded_at: '2024-10-22T14:45:00Z',
        },
        {
          id: '3',
          student_name: 'Bob Johnson',
          rubric_title: 'Stroke Case Presentation',
          score: 95,
          submitted_at: '2024-10-21T09:00:00Z',
          graded_at: '2024-10-21T09:20:00Z',
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

  const getScoreBadge = (score: number) => {
    if (score >= 90) return 'bg-green-100 text-green-800';
    if (score >= 80) return 'bg-blue-100 text-blue-800';
    if (score >= 70) return 'bg-yellow-100 text-yellow-800';
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
      <h1 className="text-3xl font-bold text-gray-900">Grading Results</h1>

      {/* Results Table */}
      <div className="card overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Student
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rubric
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Score
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Submitted
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {results.map((result) => (
              <tr key={result.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{result.student_name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{result.rubric_title}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-3 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${getScoreBadge(result.score)}`}>
                    {result.score}%
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(result.submitted_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <button
                    onClick={() => setSelectedResult(result)}
                    className="text-primary-600 hover:text-primary-900 font-medium"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail Modal */}
      {selectedResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold">{selectedResult.student_name}</h2>
                <p className="text-gray-600">{selectedResult.rubric_title}</p>
              </div>
              <button
                onClick={() => setSelectedResult(null)}
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
                <span className={`text-3xl font-bold ${getScoreColor(selectedResult.score)}`}>
                  {selectedResult.score}%
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
                </div>
              </div>

              <div>
                <h3 className="font-bold text-lg mb-3">Feedback</h3>
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                  <p className="text-sm text-gray-700">
                    Excellent presentation with comprehensive coverage of the stroke case. 
                    Strong clinical reasoning demonstrated throughout. Minor improvements needed 
                    in differential diagnosis discussion.
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSelectedResult(null)}
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


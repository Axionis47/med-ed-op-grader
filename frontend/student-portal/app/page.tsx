'use client';

import { useEffect, useState } from 'react';

interface DashboardStats {
  totalSubmissions: number;
  averageScore: number;
  pendingGrading: number;
  lastSubmission: string;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalSubmissions: 0,
    averageScore: 0,
    pendingGrading: 0,
    lastSubmission: '',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data
    setTimeout(() => {
      setStats({
        totalSubmissions: 5,
        averageScore: 88.5,
        pendingGrading: 1,
        lastSubmission: '2024-10-23T10:00:00Z',
      });
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Welcome Back!</h1>
        <p className="text-gray-600 mt-2">Here's your performance overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Submissions</p>
              <p className="text-3xl font-bold text-primary-600">{stats.totalSubmissions}</p>
            </div>
            <div className="bg-primary-100 p-3 rounded-full">
              <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Average Score</p>
              <p className="text-3xl font-bold text-blue-600">{stats.averageScore}%</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Grading</p>
              <p className="text-3xl font-bold text-yellow-600">{stats.pendingGrading}</p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Last Submission</p>
              <p className="text-lg font-bold text-purple-600">
                {stats.lastSubmission ? new Date(stats.lastSubmission).toLocaleDateString() : 'N/A'}
              </p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a href="/submit" className="btn-primary text-center">
            Submit New Presentation
          </a>
          <a href="/grades" className="btn-secondary text-center">
            View My Grades
          </a>
        </div>
      </div>

      {/* Recent Submissions */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Recent Submissions</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-3 border-b">
            <div>
              <p className="font-medium">Stroke Case Presentation</p>
              <p className="text-sm text-gray-600">Submitted on Oct 23, 2024</p>
            </div>
            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
              92%
            </span>
          </div>
          <div className="flex items-center justify-between py-3 border-b">
            <div>
              <p className="font-medium">Cardiology Case</p>
              <p className="text-sm text-gray-600">Submitted on Oct 20, 2024</p>
            </div>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
              88%
            </span>
          </div>
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="font-medium">Neurology Case</p>
              <p className="text-sm text-gray-600">Submitted on Oct 18, 2024</p>
            </div>
            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-semibold">
              Pending
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}


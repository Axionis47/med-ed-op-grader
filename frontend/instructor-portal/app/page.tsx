'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';

interface Stats {
  totalRubrics: number;
  totalSubmissions: number;
  pendingGrading: number;
  averageScore: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    totalRubrics: 0,
    totalSubmissions: 0,
    pendingGrading: 0,
    averageScore: 0,
  });
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState<'online' | 'offline'>('offline');

  useEffect(() => {
    checkApiStatus();
    // In production, fetch real stats from API
    setTimeout(() => {
      setStats({
        totalRubrics: 5,
        totalSubmissions: 23,
        pendingGrading: 3,
        averageScore: 85.4,
      });
      setLoading(false);
    }, 500);
  }, []);

  const checkApiStatus = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await axios.get(`${apiUrl}/health`, { timeout: 3000 });
      setApiStatus('online');
    } catch (error) {
      setApiStatus('offline');
    }
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
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center space-x-2">
          <div className={`h-3 w-3 rounded-full ${apiStatus === 'online' ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            API {apiStatus === 'online' ? 'Online' : 'Offline'}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Rubrics</p>
              <p className="text-3xl font-bold text-primary-600">{stats.totalRubrics}</p>
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
              <p className="text-sm text-gray-600">Total Submissions</p>
              <p className="text-3xl font-bold text-green-600">{stats.totalSubmissions}</p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
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
              <p className="text-sm text-gray-600">Average Score</p>
              <p className="text-3xl font-bold text-purple-600">{stats.averageScore}%</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a href="/rubrics/new" className="btn-primary text-center">
            Create New Rubric
          </a>
          <a href="/submissions" className="btn-secondary text-center">
            View Submissions
          </a>
          <a href="/results" className="btn-secondary text-center">
            View Results
          </a>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-3 border-b">
            <div>
              <p className="font-medium">New submission from Student A</p>
              <p className="text-sm text-gray-600">Stroke Case Presentation</p>
            </div>
            <span className="text-sm text-gray-500">2 hours ago</span>
          </div>
          <div className="flex items-center justify-between py-3 border-b">
            <div>
              <p className="font-medium">Grading completed for Student B</p>
              <p className="text-sm text-gray-600">Score: 92%</p>
            </div>
            <span className="text-sm text-gray-500">5 hours ago</span>
          </div>
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="font-medium">New rubric created</p>
              <p className="text-sm text-gray-600">Cardiology Case v2</p>
            </div>
            <span className="text-sm text-gray-500">1 day ago</span>
          </div>
        </div>
      </div>
    </div>
  );
}


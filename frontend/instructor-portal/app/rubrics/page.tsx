'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';

interface Rubric {
  rubric_id: string;
  version: string;
  title: string;
  description: string;
  created_at: string;
  total_points: number;
}

export default function RubricsPage() {
  const [rubrics, setRubrics] = useState<Rubric[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchRubrics();
  }, []);

  const fetchRubrics = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await axios.get(`${apiUrl}/rubrics`);
      setRubrics(response.data.rubrics || []);
    } catch (error) {
      console.error('Error fetching rubrics:', error);
      // Mock data for demo
      setRubrics([
        {
          rubric_id: 'stroke_v1',
          version: '1.0',
          title: 'Stroke Case Presentation',
          description: 'Comprehensive rubric for stroke case presentations',
          created_at: '2024-10-20T10:00:00Z',
          total_points: 100,
        },
        {
          rubric_id: 'cardiology_v1',
          version: '1.0',
          title: 'Cardiology Case Presentation',
          description: 'Rubric for cardiology case presentations',
          created_at: '2024-10-18T14:30:00Z',
          total_points: 100,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    setUploading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const formData = new FormData();
      formData.append('file', uploadFile);

      await axios.post(`${apiUrl}/rubrics`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      alert('Rubric uploaded successfully!');
      setShowUpload(false);
      setUploadFile(null);
      fetchRubrics();
    } catch (error) {
      console.error('Error uploading rubric:', error);
      alert('Error uploading rubric. Please try again.');
    } finally {
      setUploading(false);
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
        <h1 className="text-3xl font-bold text-gray-900">Rubrics</h1>
        <button
          onClick={() => setShowUpload(true)}
          className="btn-primary"
        >
          + Upload New Rubric
        </button>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">Upload Rubric</h2>
            <div className="space-y-4">
              <div>
                <label className="label">Rubric File (JSON)</label>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileChange}
                  className="input"
                />
                <p className="text-sm text-gray-500 mt-2">
                  Upload a JSON file containing the rubric definition
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleUpload}
                  disabled={!uploadFile || uploading}
                  className="btn-primary flex-1 disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
                <button
                  onClick={() => {
                    setShowUpload(false);
                    setUploadFile(null);
                  }}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Rubrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {rubrics.map((rubric) => (
          <div key={rubric.rubric_id} className="card hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-3">
              <h3 className="text-lg font-bold text-gray-900">{rubric.title}</h3>
              <span className="bg-primary-100 text-primary-800 text-xs px-2 py-1 rounded">
                v{rubric.version}
              </span>
            </div>
            <p className="text-gray-600 text-sm mb-4">{rubric.description}</p>
            <div className="flex justify-between items-center text-sm text-gray-500 mb-4">
              <span>{rubric.total_points} points</span>
              <span>{new Date(rubric.created_at).toLocaleDateString()}</span>
            </div>
            <div className="flex space-x-2">
              <button className="btn-primary text-sm flex-1">View</button>
              <button className="btn-secondary text-sm flex-1">Edit</button>
            </div>
          </div>
        ))}
      </div>

      {rubrics.length === 0 && (
        <div className="card text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No rubrics</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by uploading a new rubric.</p>
          <div className="mt-6">
            <button onClick={() => setShowUpload(true)} className="btn-primary">
              + Upload Rubric
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


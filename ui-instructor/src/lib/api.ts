import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL as string

export async function fetchScore(submissionId: string) {
  const res = await axios.get(`${BASE_URL}/score/${submissionId}`)
  return res.data
}

export async function fetchSubmission(submissionId: string) {
  const res = await axios.get(`${BASE_URL}/submissions/${submissionId}`)
  return res.data
}


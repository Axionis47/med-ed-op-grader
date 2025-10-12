export interface EvidenceSpan { 0: number; 1: number }
export interface SectionResult { id: string; score: 0|1|2; rationale?: string; evidence: EvidenceSpan[]; action?: string }
export interface EPABundle { epa6: number; epa2: number; clipped_by?: string[] }
export interface ScoreJson {
  submission_id: string
  rubric: { id: string; version: number }
  steps: { id: string; sections: SectionResult[] }[]
  overall: { sum: number; max: number }
  epa: EPABundle
  feedback: { sections: { id: string; well: string; action: string; evidence: EvidenceSpan[]; status?: string }[] }
  timeline?: { events?: { type: string; time_text?: string; confidence?: number }[]; conflicts?: any[] }
  version: { scoring: string; prompt_bundle_id: string }
  updated_at: string
}


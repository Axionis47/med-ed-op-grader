import React from 'react'
import type { EvidenceSpan } from '../types'

type Props = { open: boolean; onClose: ()=>void; evidence: EvidenceSpan[]; title?: string }

export default function EvidenceModal({ open, onClose, evidence, title }: Props) {
  if (!open) return null
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="evidence-title" className="fixed inset-0 bg-black/40 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg outline-none">
        <div className="p-4 border-b flex items-center justify-between">
          <h2 id="evidence-title" className="text-lg font-semibold">{title||'Evidence'}</h2>
          <button onClick={onClose} aria-label="Close" className="rounded px-2 py-1 bg-gray-100 hover:bg-gray-200">ESC</button>
        </div>
        <div className="p-4 space-y-2">
          {evidence?.length ? evidence.map((ev, idx) => (
            <div key={idx} className="text-sm">
              <span className="inline-block px-2 py-1 rounded bg-blue-50 text-blue-700">lines {ev[0]}-{ev[1]}</span>
            </div>
          )) : <div className="text-sm text-gray-500">No evidence</div>}
        </div>
      </div>
    </div>
  )
}


import React, { useEffect, useMemo, useState } from 'react'
import dayjs from 'dayjs'
import { fetchScore, fetchSubmission } from './lib/api'
import type { ScoreJson, SectionResult } from './types'
import EvidenceModal from './components/EvidenceModal'

const SUBMISSION_ID = import.meta.env.VITE_SUBMISSION_ID as string

function ScoreBadge({score}:{score:0|1|2}){
  const color = score===2? 'bg-green-100 text-green-800': score===1? 'bg-amber-100 text-amber-800':'bg-red-100 text-red-800'
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded ${color}`}>{score}</span>
}

export default function App(){
  const [score,setScore]=useState<ScoreJson|undefined>()
  const [sub,setSub]=useState<any>()
  const [openFor,setOpenFor]=useState<string|undefined>()

  useEffect(()=>{
    (async()=>{
      try{
        const [sc, sb] = await Promise.all([
          fetchScore(SUBMISSION_ID),
          fetchSubmission(SUBMISSION_ID).catch(()=>undefined),
        ])
        setScore(sc); setSub(sb)
      }catch(e){ console.error(e) }
    })()
  },[])

  const sections = useMemo(()=> score? score.steps.flatMap(s=>s.sections): [], [score])
  const onsetOk = useMemo(()=>{
    const ev = score?.timeline?.events||[]
    return !!ev.find(e=> e.type==='onset' && (e.confidence||0) >= 0.7)
  },[score])

  if(!score) return <div className='p-6 text-gray-600'>Loading…</div>

  return (
    <div className='max-w-5xl mx-auto p-6 space-y-6'>
      <header className='flex items-end justify-between'>
        <div>
          <h1 className='text-2xl font-bold'>My Results</h1>
          <p className='text-sm text-gray-600'>Rubric {score.rubric.id}@{score.rubric.version}{sub?.test_id? ` · Test: ${sub.test_id}`:''}</p>
        </div>
        <div className='text-right'>
          <div className='text-3xl font-semibold'>{score.overall.sum}/{score.overall.max}</div>
          <div className='text-sm text-gray-600'>Updated {dayjs(score.updated_at).format('YYYY-MM-DD HH:mm')}</div>
        </div>
      </header>

      <section className='grid grid-cols-2 md:grid-cols-4 gap-3'>
        <div className='p-3 rounded border bg-white'>
          <div className='text-xs text-gray-500'>EPA-6</div>
          <div className='text-xl font-semibold'>{score.epa.epa6}</div>
        </div>
        <div className='p-3 rounded border bg-white'>
          <div className='text-xs text-gray-500'>EPA-2</div>
          <div className='text-xl font-semibold'>{score.epa.epa2}</div>
        </div>
        <div className='p-3 rounded border bg-white col-span-2'>
          <div className='text-xs text-gray-500 mb-1'>Chronology</div>
          <div className='text-sm'>{onsetOk? 'Onset/LKW anchored (≥0.7)': 'Onset/LKW missing or low confidence'}</div>
        </div>
      </section>

      <section>
        <h2 className='font-semibold mb-2'>Sections</h2>
        <div className='grid grid-cols-1 md:grid-cols-2 gap-3'>
          {sections.map(sec=> (
            <div key={sec.id} className='p-4 rounded border bg-white'>
              <div className='flex items-center justify-between'>
                <div className='font-medium'>{sec.id}</div>
                <ScoreBadge score={sec.score as 0|1|2} />
              </div>
              {sec.rationale && <p className='text-sm text-gray-600 mt-1'>{sec.rationale}</p>}
              {sec.action && sec.score<2 && (
                <div className='text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded mt-2 px-2 py-1'>Projected; not rescored. Action: {sec.action}</div>
              )}
              <div className='mt-2'>
                <button className='text-sm underline' onClick={()=> setOpenFor(sec.id)}>Show evidence</button>
              </div>
              {openFor===sec.id && (
                <EvidenceModal open onClose={()=> setOpenFor(undefined)} evidence={sec.evidence} title={`Evidence · ${sec.id}`} />
              )}
            </div>
          ))}
        </div>
      </section>

      <footer className='text-xs text-gray-500'>Scoring v{score.version.scoring} · Prompt bundle {score.version.prompt_bundle_id}</footer>
    </div>
  )
}


import React, { useEffect, useState } from 'react'
import { api } from '../api'

type Row = {
  item_id: number
  our_sku: string
  comp_barcode?: string | null
  comp_url?: string | null
  approved: boolean
}

export default function Matching(){
  const [rows, setRows] = useState<Row[]>([])
  const [competitor] = useState<'praktiker'>('praktiker')
  const [saving, setSaving] = useState<number | null>(null)
  const [autoRun, setAutoRun] = useState(false)
  const [inputs, setInputs] = useState<Record<number, string>>({}) // item_id -> manual barcode

  async function load(){
    const data = await api<Row[]>(`/match/view/${competitor}`)
    setRows(data)
  }

  useEffect(()=>{ load() },[])

  async function runAuto(){
    setAutoRun(true)
    await api(`/match/auto/${competitor}`, { method: 'POST' })
    setAutoRun(false)
    await load()
  }

  async function saveManual(item_id: number){
    const barcode = (inputs[item_id] || '').trim()
    if(!barcode) return
    try{
      setSaving(item_id)
      await api(`/match/manual_by_barcode/${competitor}?item_id=${item_id}&competitor_barcode=${encodeURIComponent(barcode)}`, { method: 'POST' })
      setInputs(prev => ({...prev, [item_id]: ''}))
      await load()
    } finally {
      setSaving(null)
    }
  }

  return (
    <div>
      <h2>Match items – Competitor: {competitor}</h2>
      <button disabled={autoRun} onClick={runAuto}>Auto-match by barcode</button>

      <table className="table">
        <thead>
          <tr>
            <th style={{width: '220px'}}>Praktis SKU</th>
            <th>Praktiker Barcode (link)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => {
            const hasMatch = Boolean(r.comp_barcode && r.comp_url)
            return (
              <tr key={r.item_id}>
                <td>{r.our_sku}</td>
                <td>
                  {hasMatch ? (
                    <a href={r.comp_url!} target="_blank" rel="noreferrer">{r.comp_barcode}</a>
                  ) : (
                    <div style={{display:'flex', gap:8}}>
                      <input
                        placeholder="Enter Praktiker barcode"
                        value={inputs[r.item_id] || ''}
                        onChange={e => setInputs(prev => ({...prev, [r.item_id]: e.target.value}))}
                        style={{maxWidth: 260}}
                      />
                      <button onClick={() => saveManual(r.item_id)} disabled={saving === r.item_id}>
                        {saving === r.item_id ? 'Saving...' : 'Save'}
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

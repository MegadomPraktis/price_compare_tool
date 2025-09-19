import React, { useEffect, useState } from 'react'
import { api } from '../api'

type Row = { item_id:number; our_sku:string; comp_barcode?:string|null; comp_url?:string|null; approved:boolean }

export default function MatchingNew(){
  const competitor = 'praktiker'
  const [rows, setRows] = useState<Row[]>([])
  const [savingId, setSavingId] = useState<number | null>(null)
  const [inputs, setInputs] = useState<Record<number, string>>({})

  async function load(){
    const data = await api<Row[]>(`/match/view/${competitor}`)
    setRows(data)
  }
  useEffect(()=>{ load() },[])

  async function saveManual(item_id:number){
    const barcode = (inputs[item_id] || '').trim()
    if(!barcode) return
    setSavingId(item_id)
    try{
      await api(`/match/manual_by_barcode/${competitor}?item_id=${item_id}&competitor_barcode=${encodeURIComponent(barcode)}`, { method: 'POST' })
      setInputs(p => ({...p, [item_id]: ''}))
      await load()
    } finally {
      setSavingId(null)
    }
  }

  return (
    <div style={{padding:16}}>
      <h2>Match items – Competitor: {competitor}</h2>
      <table className="table">
        <thead>
          <tr>
            <th style={{width:220}}>Praktis SKU</th>
            <th>Praktiker Barcode (link or manual)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => {
            const matched = Boolean(r.comp_barcode && r.comp_url)
            return (
              <tr key={r.item_id}>
                <td>{r.our_sku}</td>
                <td>
                  {matched ? (
                    <a href={r.comp_url!} target="_blank" rel="noreferrer">{r.comp_barcode}</a>
                  ) : (
                    <span style={{display:'inline-flex', gap:8}}>
                      <input
                        placeholder="Enter Praktiker barcode"
                        value={inputs[r.item_id] || ''}
                        onChange={e => setInputs(p => ({...p, [r.item_id]: e.target.value}))}
                        style={{maxWidth:260}}
                      />
                      <button onClick={()=>saveManual(r.item_id)} disabled={savingId === r.item_id}>
                        {savingId === r.item_id ? 'Saving…' : 'Save'}
                      </button>
                    </span>
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

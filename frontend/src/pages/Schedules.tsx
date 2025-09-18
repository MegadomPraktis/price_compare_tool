import React, { useEffect, useState } from 'react'
import { api } from '../api'


type Sch = { id:number; tag_id:number; cron:string; active:boolean }


type Tag = { id:number; name:string }


export default function Schedules(){
const [schedules, setSchedules] = useState<Sch[]>([])
const [tags, setTags] = useState<Tag[]>([])
const [cron, setCron] = useState('0 9 * * *')
const [tagId, setTagId] = useState<number|undefined>()


useEffect(()=>{
api<Sch[]>('/schedules/').then(setSchedules)
api<Tag[]>('/tags/').then(setTags)
},[])


async function create(){
if(!tagId) return
const r = await api<{id:number}>('/schedules/?tag_id='+tagId+'&cron='+encodeURIComponent(cron), { method: 'POST' })
setSchedules([{ id:r.id, tag_id: tagId, cron, active:true }, ...schedules])
}


return (
<div>
<h2>Email Schedules</h2>
<div style={{display:'flex', gap:8, alignItems:'center'}}>
<select onChange={e=>setTagId(Number(e.target.value))} defaultValue="">
<option value="" disabled>Choose tag</option>
{tags.map(t=> <option key={t.id} value={t.id}>{t.name}</option>)}
</select>
<input value={cron} onChange={e=>setCron(e.target.value)} placeholder="cron e.g. 0 9 * * *" />
<button onClick={create}>Create</button>
</div>


<table className="table">
<thead><tr><th>ID</th><th>Tag</th><th>Cron</th><th>Active</th></tr></thead>
<tbody>
{schedules.map(s=> (<tr key={s.id}><td>{s.id}</td><td>{s.tag_id}</td><td>{s.cron}</td><td>{String(s.active)}</td></tr>))}
</tbody>
</table>
</div>
)
}
import React, { useEffect, useState } from 'react'
import { api } from '../api'


type Tag = { id:number; name:string; email?:string|null }


export default function Tags(){
const [tags, setTags] = useState<Tag[]>([])
const [name, setName] = useState('')
const [email, setEmail] = useState('')
useEffect(()=>{ api<Tag[]>('/tags/').then(setTags) },[])


async function create(){
const t = await api<Tag>('/tags/', { method:'POST', body: JSON.stringify({ name, email: email || null }) })
setTags([t, ...tags]); setName(''); setEmail('')
}


return (
<div>
<h2>Tags</h2>
<div style={{display:'flex', gap:8}}>
<input placeholder="Tag name" value={name} onChange={e=>setName(e.target.value)} />
<input placeholder="Buyer email (optional)" value={email} onChange={e=>setEmail(e.target.value)} />
<button onClick={create}>Create</button>
</div>
<table className="table">
<thead><tr><th>ID</th><th>Name</th><th>Email</th></tr></thead>
<tbody>
{tags.map(t=> (<tr key={t.id}><td>{t.id}</td><td>{t.name}</td><td>{t.email || '-'}</td></tr>))}
</tbody>
</table>
</div>
)
}
import React, { useEffect, useState } from 'react'
import { api } from '../api'


type Row = { our_sku:string; comp_sku?:string; our_name:string; comp_name?:string; our_price:number; comp_price?:number|null; diff?:number|null }


export default function Comparison(){
const [rows, setRows] = useState<Row[]>([])
useEffect(()=>{ api<Row[]>('/compare/praktiker').then(setRows) },[])


return (
<div>
<h2>Price comparison (praktiker)</h2>
<table className="table">
<thead>
<tr>
<th>Our SKU</th><th>Comp SKU</th><th>Our Name</th><th>Comp Name</th>
<th>Our Price</th><th>Comp Price</th><th>Δ</th>
</tr>
</thead>
<tbody>
{rows.map((r,i)=> (
<tr key={i}>
<td>{r.our_sku}</td>
<td>{r.comp_sku || '-'}</td>
<td>{r.our_name}</td>
<td>{r.comp_name || '-'}</td>
<td>{r.our_price.toFixed(2)}</td>
<td>{r.comp_price?.toFixed(2) ?? '-'}</td>
<td>{r.diff?.toFixed(2) ?? '-'}</td>
</tr>
))}
</tbody>
</table>
</div>
)
}
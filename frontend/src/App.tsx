import React, { useState } from 'react'
import Matching from './pages/Matching'
import Comparison from './pages/Comparison'
import Tags from './pages/Tags'
import Schedules from './pages/Schedules'


export default function App(){
const [tab, setTab] = useState<'matching'|'comparison'|'tags'|'schedules'>('matching')
return (
<div className="app">
<nav className="tabs">
<button onClick={()=>setTab('matching')} className={tab==='matching'?'active':''}>Matching</button>
<button onClick={()=>setTab('comparison')} className={tab==='comparison'?'active':''}>Comparison</button>
<button onClick={()=>setTab('tags')} className={tab==='tags'?'active':''}>Tags</button>
<button onClick={()=>setTab('schedules')} className={tab==='schedules'?'active':''}>Email Schedules</button>
</nav>
{tab==='matching' && <Matching/>}
{tab==='comparison' && <Comparison/>}
{tab==='tags' && <Tags/>}
{tab==='schedules' && <Schedules/>}
</div>
)
}
import React, {useState, useEffect, useRef} from 'react';

export default function App(){
  const [jobId, setJobId] = useState(null);
  const [logs, setLogs] = useState([]);
  const wsRef = useRef(null);

  const start = async () =>{
    const res = await fetch('http://127.0.0.1:8080/start', {method:'POST'});
    const j = await res.json();
    setJobId(j.job_id);
  }

  useEffect(()=>{
    if(!jobId) return;
    const ws = new WebSocket(`ws://127.0.0.1:8080/ws/${jobId}`);
    ws.onmessage = (evt)=>{
      const text = evt.data;
      if(text) setLogs(l => [...l, text]);
    }
    ws.onopen = ()=> setLogs(l => [...l, "WS connected"]);
    ws.onclose = ()=> setLogs(l => [...l, "WS closed"]);
    wsRef.current = ws;
    return ()=> ws.close();
  },[jobId]);

  return (
    <div style={{padding:20}}>
      <h1>Agentic Research Assistant (stub)</h1>
      <button onClick={start}>Start Research</button>
      <div style={{marginTop:20, whiteSpace:'pre-wrap', background:'#111', color:'#bde0fe', padding:10, height:400, overflowY:'scroll'}}>
        {logs.map((l,i)=>(<div key={i}>{l}</div>))}
      </div>
    </div>
  )
}

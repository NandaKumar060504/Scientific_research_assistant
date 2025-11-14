// import React, { useEffect, useState, useRef } from "react";

// export default function App() {
//   const [jobId, setJobId] = useState(null);
//   const [logs, setLogs] = useState([]);
//   const [paperHTML, setPaperHTML] = useState(null);
//   const [pdfURL, setPdfURL] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [showPreview, setShowPreview] = useState(false);

//   const wsRef = useRef(null);
//   const logsEndRef = useRef(null);

//   // Auto-scroll logs to bottom
//   useEffect(() => {
//     logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [logs]);

//   const start = async () => {
//     setLogs([]);
//     setPaperHTML(null);
//     setPdfURL(null);
//     setLoading(true);
//     setShowPreview(false);

//     const res = await fetch("http://127.0.0.1:8080/start", { method: "POST" });
//     const j = await res.json();

//     setJobId(j.job_id);
//   };

//   const fetchPreview = async () => {
//     if (!jobId) return;
    
//     try {
//       const res = await fetch(`http://127.0.0.1:8080/result/${jobId}`);
//       const data = await res.json();
      
//       console.log("Preview response:", data); // Debug line
      
//       if (data.status === "done" && data.html_content) {
//         setPaperHTML(data.html_content);
//         setPdfURL(`http://127.0.0.1:8080/download/${jobId}`);
//         setShowPreview(true);
//       } else if (data.status === "pending") {
//         alert("Paper not ready yet. Please wait for the pipeline to complete.");
//       } else {
//         alert("Paper generation in progress or failed. Check logs.");
//       }
//     } catch (error) {
//       console.error("Error fetching preview:", error);
//       alert("Failed to fetch preview. Please try again.");
//     }
//   };

//   // WebSocket listener
//   useEffect(() => {
//     if (!jobId) return;

//     const ws = new WebSocket(`ws://127.0.0.1:8080/ws/${jobId}`);

//     ws.onmessage = (evt) => {
//       const text = evt.data;
//       if (text) setLogs((l) => [...l, text]);

//       // Final message → enable preview
//       if (text.includes("Final paper generated") || text.includes("Pipeline completed successfully")) {
//         setLoading(false);
//       }
//     };

//     ws.onopen = () => setLogs((l) => [...l, "🔗 WS connected"]);
//     ws.onclose = () => setLogs((l) => [...l, "❌ WS closed"]);

//     wsRef.current = ws;
//     return () => ws.close();
//   }, [jobId]);

//   return (
//     <div
//       style={{
//         padding: 40,
//         fontFamily: "Inter, Arial, sans-serif",
//         maxWidth: 1400,
//         margin: "auto",
//       }}
//     >
//       <h1 style={{ fontSize: 42, fontWeight: 700, color: "#1a3d7c" }}>
//         AI Research Assistant
//       </h1>

//       <div style={{ display: "flex", gap: 15, marginTop: 10 }}>
//         <button
//           onClick={start}
//           disabled={loading}
//           style={{
//             padding: "14px 28px",
//             background: loading ? "#777" : "#0066ff",
//             color: "white",
//             border: "none",
//             borderRadius: 8,
//             cursor: loading ? "not-allowed" : "pointer",
//             fontSize: 20,
//             fontWeight: 600,
//           }}
//         >
//           {loading ? "Running Research..." : "Start Research"}
//         </button>

//         <button
//           onClick={fetchPreview}
//           disabled={!jobId || loading}
//           style={{
//             padding: "14px 28px",
//             background: !jobId || loading ? "#ccc" : "#28a745",
//             color: "white",
//             border: "none",
//             borderRadius: 8,
//             cursor: !jobId || loading ? "not-allowed" : "pointer",
//             fontSize: 20,
//             fontWeight: 600,
//           }}
//         >
//           📄 Preview Paper
//         </button>

//         {pdfURL && (
//           <button
//             onClick={() => window.open(pdfURL, "_blank")}
//             style={{
//               padding: "14px 28px",
//               background: "#dc3545",
//               color: "white",
//               border: "none",
//               borderRadius: 8,
//               cursor: "pointer",
//               fontSize: 20,
//               fontWeight: 600,
//             }}
//           >
//             ⬇️ Download PDF
//           </button>
//         )}
//       </div>

//       {/* Loading Spinner */}
//       {loading && (
//         <div style={{ marginTop: 20, fontSize: 18, color: "#555" }}>
//           ⏳ Research pipeline running...
//         </div>
//       )}

//       {/* Two Column Layout: Logs + Preview */}
//       <div
//         style={{
//           marginTop: 30,
//           display: "grid",
//           gridTemplateColumns: showPreview ? "1fr 1fr" : "1fr",
//           gap: 20,
//         }}
//       >
//         {/* Logs Column */}
//         <div>
//           <h2 style={{ fontSize: 28, fontWeight: 600, marginBottom: 10 }}>
//             Logs
//           </h2>

//           <div
//             style={{
//               background: "#0d0d0d",
//               color: "#cce6ff",
//               padding: 15,
//               height: showPreview ? 800 : 500,
//               overflowY: "auto",
//               whiteSpace: "pre-wrap",
//               borderRadius: 8,
//               fontSize: 14,
//               border: "1px solid #333",
//               fontFamily: "monospace",
//             }}
//           >
//             {logs.length === 0 ? (
//               <div style={{ color: "#888" }}>Waiting for logs...</div>
//             ) : (
//               <>
//                 {logs.map((l, i) => (
//                   <div key={i} style={{ marginBottom: 4 }}>
//                     {l}
//                   </div>
//                 ))}
//                 <div ref={logsEndRef} />
//               </>
//             )}
//           </div>
//         </div>

//         {/* Preview Column */}
//         {showPreview && paperHTML && (
//           <div>
//             <h2 style={{ fontSize: 28, fontWeight: 600, marginBottom: 10 }}>
//               📄 Paper Preview
//             </h2>

//             <div
//               style={{
//                 border: "1px solid #ccc",
//                 borderRadius: 10,
//                 overflow: "hidden",
//                 height: 800,
//                 boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
//               }}
//             >
//               <iframe
//                 srcDoc={paperHTML}
//                 style={{
//                   width: "100%",
//                   height: "100%",
//                   border: "none",
//                   background: "white",
//                 }}
//                 title="Research Paper Preview"
//               />
//             </div>
//           </div>
//         )}
//       </div>

//       {/* Full Width Preview (when logs not shown) */}
//       {!showPreview && paperHTML && (
//         <div style={{ marginTop: 50 }}>
//           <h2 style={{ fontSize: 30, marginBottom: 10, fontWeight: 700 }}>
//             📄 Final Research Paper
//           </h2>

//           <div
//             style={{
//               border: "1px solid #ccc",
//               borderRadius: 10,
//               overflow: "hidden",
//               height: 900,
//               boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
//             }}
//           >
//             <iframe
//               srcDoc={paperHTML}
//               style={{
//                 width: "100%",
//                 height: "100%",
//                 border: "none",
//                 background: "white",
//               }}
//               title="Research Paper Preview"
//             />
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }

import React, { useEffect, useState, useRef } from "react";

export default function App() {
  const [jobId, setJobId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [paperHTML, setPaperHTML] = useState(null);
  const [pdfURL, setPdfURL] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const wsRef = useRef(null);
  const logsEndRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const start = async () => {
    setLogs([]);
    setPaperHTML(null);
    setPdfURL(null);
    setShowPreview(false);
    setLoading(true);

    const res = await fetch("http://127.0.0.1:8080/start", { method: "POST" });
    const j = await res.json();
    setJobId(j.job_id);
  };

  const fetchPreview = async () => {
    if (!jobId) return;

    const res = await fetch(`http://127.0.0.1:8080/result/${jobId}`);
    const data = await res.json();

    if (data.status === "done" && data.html_content) {
      setPaperHTML(data.html_content);
      setPdfURL(`http://127.0.0.1:8080/download/${jobId}`);
      setShowPreview(true);
    } else {
      alert("Paper not ready yet. Wait for pipeline.");
    }
  };

  useEffect(() => {
    if (!jobId) return;

    const ws = new WebSocket(`ws://127.0.0.1:8080/ws/${jobId}`);

    ws.onmessage = (evt) => {
      const text = evt.data;
      setLogs((l) => [...l, text]);

      if (text.includes("Final paper generated")) setLoading(false);
    };

    ws.onopen = () => setLogs((l) => [...l, "🔗 WS connected"]);
    ws.onclose = () => setLogs((l) => [...l, "❌ WS closed"]);

    wsRef.current = ws;
    return () => ws.close();
  }, [jobId]);

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        color: "white",
        fontFamily: "Inter, sans-serif",
        paddingBottom: 80,
      }}
    >
      {/* Top Hero Section */}
      <div
        style={{
          textAlign: "center",
          paddingTop: 80,
          paddingBottom: 60,
        }}
      >
        <h1
          style={{
            fontSize: 58,
            fontWeight: 800,
            background: "linear-gradient(90deg, #ff8a00, #e52e71)",
            WebkitBackgroundClip: "text",
            color: "transparent",
          }}
        >
          AI Research Assistant
        </h1>

        <p style={{ fontSize: 22, marginTop: 15, opacity: 0.9 }}>
          Autonomous scientific discovery using multi-agent AI intelligence.
        </p>

        {/* Buttons */}
        <div style={{ marginTop: 40, display: "flex", gap: 20, justifyContent: "center" }}>
          <button
            onClick={start}
            disabled={loading}
            style={{
              padding: "16px 32px",
              fontSize: 20,
              borderRadius: 12,
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              background: loading ? "#555" : "linear-gradient(90deg, #ff9966, #ff5e62)",
              color: "white",
              fontWeight: 700,
              boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
            }}
          >
            {loading ? "Running Research..." : "🚀 Start Research"}
          </button>

          <button
            onClick={fetchPreview}
            disabled={!jobId || loading}
            style={{
              padding: "16px 32px",
              fontSize: 20,
              borderRadius: 12,
              border: "none",
              cursor: !jobId || loading ? "not-allowed" : "pointer",
              background: "linear-gradient(90deg, #36d1dc, #5b86e5)",
              color: "white",
              fontWeight: 700,
              opacity: !jobId || loading ? 0.5 : 1,
              boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
            }}
          >
            📄 Preview Paper
          </button>

          {pdfURL && (
            <button
              onClick={() => window.open(pdfURL, "_blank")}
              style={{
                padding: "16px 32px",
                fontSize: 20,
                borderRadius: 12,
                border: "none",
                cursor: "pointer",
                background: "linear-gradient(90deg, #8e2de2, #4a00e0)",
                color: "white",
                fontWeight: 700,
                boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
              }}
            >
              ⬇️ Download PDF
            </button>
          )}
        </div>

        {loading && <p style={{ marginTop: 20, opacity: 0.8 }}>⏳ Research pipeline running...</p>}
      </div>

      {/* MAIN CONTENT SECTION */}
      <div
        style={{
          display: "flex",
          gap: 30,
          width: "90%",
          margin: "auto",
        }}
      >
        {/* Logs Panel */}
        <div
          style={{
            flex: 1,
            background: "rgba(255,255,255,0.08)",
            borderRadius: 16,
            padding: 20,
            backdropFilter: "blur(8px)",
            height: showPreview ? 800 : 600,
            overflowY: "auto",
            border: "1px solid rgba(255,255,255,0.12)",
            boxShadow: "0 8px 20px rgba(0,0,0,0.2)",
          }}
        >
          <h2 style={{ fontSize: 26, marginBottom: 15 }}>📜 Pipeline Logs</h2>

          {logs.map((l, i) => (
            <div key={i} style={{ marginBottom: 6, fontFamily: "monospace" }}>
              {l}
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>

        {/* Paper Preview */}
        {showPreview && paperHTML && (
          <div
            style={{
              flex: 1,
              background: "rgba(255,255,255,0.08)",
              borderRadius: 16,
              padding: 20,
              backdropFilter: "blur(10px)",
              height: 800,
              boxShadow: "0 8px 20px rgba(0,0,0,0.25)",
            }}
          >
            <h2 style={{ fontSize: 26, marginBottom: 15 }}>📄 Research Paper Preview</h2>
            <iframe
              srcDoc={paperHTML}
              style={{
                width: "100%",
                height: "100%",
                border: "none",
                background: "white",
                borderRadius: 10,
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}


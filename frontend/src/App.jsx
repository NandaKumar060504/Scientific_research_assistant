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

    // const res = await fetch("http://127.0.0.1:8080/start", { method: "POST" });
    const res = await fetch("http://localhost:8082/api/start", { method: "POST" });
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

// import React, { useEffect, useState, useRef } from "react";

// export default function App() {
//   const API = import.meta.env.VITE_BACKEND_URL; // 🔥 Production-safe base URL

//   const [jobId, setJobId] = useState(null);
//   const [logs, setLogs] = useState([]);
//   const [paperHTML, setPaperHTML] = useState(null);
//   const [pdfURL, setPdfURL] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [showPreview, setShowPreview] = useState(false);

//   const wsRef = useRef(null);
//   const logsEndRef = useRef(null);

//   useEffect(() => {
//     logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [logs]);

//   // ---------------- START THE PIPELINE ----------------
//   const start = async () => {
//     setLogs([]);
//     setPaperHTML(null);
//     setPdfURL(null);
//     setShowPreview(false);
//     setLoading(true);

//     const res = await fetch(`${API}/start`, { method: "POST" });
//     const j = await res.json();
//     setJobId(j.job_id);
//   };

//   // ---------------- FETCH PDF + HTML PREVIEW ----------------
//   const fetchPreview = async () => {
//     if (!jobId) return;

//     const res = await fetch(`${API}/result/${jobId}`);
//     const data = await res.json();

//     if (data.status === "done" && data.html_content) {
//       setPaperHTML(data.html_content);
//       setPdfURL(`${API}/download/${jobId}`);
//       setShowPreview(true);
//     } else {
//       alert("Paper not ready yet. Wait for pipeline.");
//     }
//   };

//   // ---------------- WEBSOCKET LOG STREAM ----------------
//   useEffect(() => {
//     if (!jobId) return;

//     // Convert backend HTTPS URL to WSS WebSocket URL
//     const wsURL = API.replace("https://", "wss://") + `/ws/${jobId}`;
//     const ws = new WebSocket(wsURL);

//     ws.onopen = () => setLogs((l) => [...l, "🔗 WebSocket connected"]);
//     ws.onclose = () => setLogs((l) => [...l, "❌ WebSocket closed"]);

//     ws.onmessage = (evt) => {
//       const text = evt.data;
//       setLogs((l) => [...l, text]);

//       if (text.includes("Final paper generated")) setLoading(false);
//     };

//     wsRef.current = ws;
//     return () => ws.close();
//   }, [jobId]);

//   // ----------------------------------------------------------
//   // ----------------------- UI BELOW --------------------------
//   // ----------------------------------------------------------

//   return (
//     <div
//       style={{
//         minHeight: "100vh",
//         width: "100%",
//         background: "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
//         color: "white",
//         fontFamily: "Inter, sans-serif",
//         paddingBottom: 80,
//       }}
//     >
//       {/* ---------------------- HERO SECTION ---------------------- */}
//       <div style={{ textAlign: "center", paddingTop: 80, paddingBottom: 60 }}>
//         <h1
//           style={{
//             fontSize: 58,
//             fontWeight: 800,
//             background: "linear-gradient(90deg, #ff8a00, #e52e71)",
//             WebkitBackgroundClip: "text",
//             color: "transparent",
//           }}
//         >
//           AI Research Assistant
//         </h1>

//         <p style={{ fontSize: 22, marginTop: 15, opacity: 0.9 }}>
//           Autonomous scientific discovery using multi-agent AI intelligence.
//         </p>

//         {/* BUTTONS */}
//         <div
//           style={{
//             marginTop: 40,
//             display: "flex",
//             gap: 20,
//             justifyContent: "center",
//           }}
//         >
//           {/* START */}
//           <button
//             onClick={start}
//             disabled={loading}
//             style={{
//               padding: "16px 32px",
//               fontSize: 20,
//               borderRadius: 12,
//               border: "none",
//               cursor: loading ? "not-allowed" : "pointer",
//               background: loading
//                 ? "#555"
//                 : "linear-gradient(90deg, #ff9966, #ff5e62)",
//               color: "white",
//               fontWeight: 700,
//               boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
//             }}
//           >
//             {loading ? "Running Research..." : "🚀 Start Research"}
//           </button>

//           {/* PREVIEW */}
//           <button
//             onClick={fetchPreview}
//             disabled={!jobId || loading}
//             style={{
//               padding: "16px 32px",
//               fontSize: 20,
//               borderRadius: 12,
//               border: "none",
//               cursor: !jobId || loading ? "not-allowed" : "pointer",
//               background: "linear-gradient(90deg, #36d1dc, #5b86e5)",
//               color: "white",
//               fontWeight: 700,
//               opacity: !jobId || loading ? 0.5 : 1,
//               boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
//             }}
//           >
//             📄 Preview Paper
//           </button>

//           {/* DOWNLOAD PDF */}
//           {pdfURL && (
//             <button
//               onClick={() => window.open(pdfURL, "_blank")}
//               style={{
//                 padding: "16px 32px",
//                 fontSize: 20,
//                 borderRadius: 12,
//                 border: "none",
//                 cursor: "pointer",
//                 background: "linear-gradient(90deg, #8e2de2, #4a00e0)",
//                 color: "white",
//                 fontWeight: 700,
//                 boxShadow: "0 4px 15px rgba(0,0,0,0.3)",
//               }}
//             >
//               ⬇️ Download PDF
//             </button>
//           )}
//         </div>

//         {loading && (
//           <p style={{ marginTop: 20, opacity: 0.8 }}>
//             ⏳ Research pipeline running...
//           </p>
//         )}
//       </div>

//       {/* ---------------------- MAIN CONTENT ---------------------- */}
//       <div
//         style={{
//           display: "flex",
//           gap: 30,
//           width: "90%",
//           margin: "auto",
//         }}
//       >
//         {/* LOGS PANEL */}
//         <div
//           style={{
//             flex: 1,
//             background: "rgba(255,255,255,0.08)",
//             borderRadius: 16,
//             padding: 20,
//             backdropFilter: "blur(8px)",
//             height: showPreview ? 800 : 600,
//             overflowY: "auto",
//             border: "1px solid rgba(255,255,255,0.12)",
//             boxShadow: "0 8px 20px rgba(0,0,0,0.2)",
//           }}
//         >
//           <h2 style={{ fontSize: 26, marginBottom: 15 }}>📜 Pipeline Logs</h2>

//           {logs.map((l, i) => (
//             <div key={i} style={{ marginBottom: 6, fontFamily: "monospace" }}>
//               {l}
//             </div>
//           ))}
//           <div ref={logsEndRef} />
//         </div>

//         {/* PAPER PREVIEW */}
//         {showPreview && paperHTML && (
//           <div
//             style={{
//               flex: 1,
//               background: "rgba(255,255,255,0.08)",
//               borderRadius: 16,
//               padding: 20,
//               backdropFilter: "blur(10px)",
//               height: 800,
//               boxShadow: "0 8px 20px rgba(0,0,0,0.25)",
//             }}
//           >
//             <h2 style={{ fontSize: 26, marginBottom: 15 }}>
//               📄 Research Paper Preview
//             </h2>
//             <iframe
//               srcDoc={paperHTML}
//               style={{
//                 width: "100%",
//                 height: "100%",
//                 border: "none",
//                 background: "white",
//                 borderRadius: 10,
//               }}
//             />
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }

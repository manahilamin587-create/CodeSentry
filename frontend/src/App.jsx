import { useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

async function api(path, options = {}) {
  let res;
  try {
    res = await fetch(API + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("Cannot reach the backend. Is uvicorn running on port 8000?");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail ?? data);
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return data;
}

function Diff({ text }) {
  return (
    <pre className="diff">
      {text.split("\n").map((line, i) => {
        let cls = "";
        if (line.startsWith("+") && !line.startsWith("+++")) cls = "add";
        else if (line.startsWith("-") && !line.startsWith("---")) cls = "del";
        else if (line.startsWith("@@")) cls = "hunk";
        return (
          <div key={i} className={cls}>
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}

export default function App() {
  const [projectPath, setProjectPath] = useState(
    "C:/Software Engineering/Semester 4/AI/AI_Final_Project/samples"
  );
  const [scannedPath, setScannedPath] = useState("");
  const [findings, setFindings] = useState([]);
  const [toolErrors, setToolErrors] = useState({});
  const [scanned, setScanned] = useState(false);
  const [selected, setSelected] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [record, setRecord] = useState(null);
  const [decision, setDecision] = useState(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  function resetDetail() {
    setExplanation(null);
    setRecord(null);
    setDecision(null);
    setError("");
  }

  function select(finding) {
    setSelected(finding);
    resetDetail();
  }

  async function run(label, fn) {
    setBusy(label);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy("");
    }
  }

  const scan = () =>
    run("scan", async () => {
      setSelected(null);
      resetDetail();
      const data = await api("/scan", {
        method: "POST",
        body: JSON.stringify({ project_path: projectPath }),
      });
      setScannedPath(projectPath);
      setFindings(data.findings);
      setToolErrors(data.tool_errors);
      setScanned(true);
    });

  const explain = () =>
    run("explain", async () => {
      setExplanation(
        await api("/explain", {
          method: "POST",
          body: JSON.stringify({ project_path: scannedPath, finding: selected }),
        })
      );
    });

  const proposeFix = () =>
    run("propose", async () => {
      setDecision(null);
      setRecord(
        await api("/propose-fix", {
          method: "POST",
          body: JSON.stringify({ project_path: scannedPath, finding: selected }),
        })
      );
    });

  const decide = (kind) =>
    run(kind, async () => {
      const data = await api(`/proposals/${record.id}/${kind}`, { method: "POST" });
      setDecision(data);
      setRecord({ ...record, status: data.status });
    });

  const isPython = selected?.file.endsWith(".py");
  const toolErrorList = Object.entries(toolErrors);

  return (
    <div className="app">
      <div className="header">
        <h1>CodeSentry</h1>
        <p>AI finds. The developer approves. Tests verify. Blockchain records.</p>
      </div>

      <div className="scan-bar">
        <input
          value={projectPath}
          onChange={(e) => setProjectPath(e.target.value)}
          placeholder="Project folder, e.g. C:/Projects/my-app"
        />
        <button className="btn primary" onClick={scan} disabled={busy !== "" || !projectPath}>
          {busy === "scan" ? "Scanning…" : "Scan project"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {toolErrorList.length > 0 && (
        <div className="warn">
          Some tools failed:{" "}
          {toolErrorList.map(([tool, msg]) => `${tool} (${msg})`).join("; ")}
        </div>
      )}

      <div className="layout">
        <div className="panel">
          <h2>Findings {scanned && `(${findings.length})`}</h2>
          {!scanned && <p className="empty">Scan a project to see its findings.</p>}
          {scanned && findings.length === 0 && (
            <p className="empty">No findings. Remember: no findings is not proof of safety.</p>
          )}
          {findings.map((f) => (
            <div
              key={f.id}
              className={`finding ${selected?.id === f.id ? "active" : ""}`}
              onClick={() => select(f)}
            >
              <div className="top">
                <span className={`badge ${f.severity}`}>{f.severity}</span>
                <strong>{f.rule_id}</strong>
                <span className="tool">{f.tool}</span>
              </div>
              <div className="loc">
                {f.file}:{f.line}
              </div>
              <div className="msg">{f.message}</div>
            </div>
          ))}
        </div>

        <div className="panel">
          {!selected && <p className="empty">Select a finding to review it.</p>}

          {selected && (
            <>
              <h2>
                <span className={`badge ${selected.severity}`}>{selected.severity}</span>{" "}
                {selected.rule_id} · {selected.tool}
              </h2>
              <div className="loc">
                {selected.file}:{selected.line}
              </div>
              <p>{selected.message}</p>
              {selected.code_snippet && <pre>{selected.code_snippet}</pre>}

              <div className="actions">
                <button className="btn" onClick={explain} disabled={busy !== ""}>
                  {busy === "explain" ? "Explaining…" : "Explain"}
                </button>
                <button
                  className="btn primary"
                  onClick={proposeFix}
                  disabled={busy !== "" || !isPython}
                  title={isPython ? "" : "Automatic fixes support Python files only"}
                >
                  {busy === "propose" ? "Generating fix…" : "Propose fix"}
                </button>
              </div>

              {explanation && (
                <div className="card">
                  <h3>Explanation</h3>
                  <p>
                    <strong>What:</strong> {explanation.what}
                  </p>
                  <p>
                    <strong>Why it matters:</strong> {explanation.why}
                  </p>
                  <p>
                    <strong>Chance of false positive:</strong>{" "}
                    {explanation.likely_false_positive}
                  </p>
                  <p>
                    <strong>Evidence:</strong> {explanation.reasoning}
                  </p>
                </div>
              )}

              {record && (
                <div className="card">
                  <h3>
                    Proposed fix <span className={`status ${record.status}`}>{record.status}</span>
                  </h3>
                  <p>{record.proposal.note}</p>
                  <Diff text={record.proposal.diff} />
                  {record.status === "pending" && (
                    <div className="actions">
                      <button
                        className="btn approve"
                        onClick={() => decide("approve")}
                        disabled={busy !== ""}
                      >
                        {busy === "approve" ? "Applying…" : "Approve and apply"}
                      </button>
                      <button
                        className="btn reject"
                        onClick={() => decide("reject")}
                        disabled={busy !== ""}
                      >
                        Reject
                      </button>
                    </div>
                  )}
                  {decision && <p>{decision.message}</p>}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
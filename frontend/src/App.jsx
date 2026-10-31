import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  CircleHelp,
  Clock3,
  Cpu,
  Download,
  EthernetPort,
  FileText,
  Gauge,
  LayoutDashboard,
  LoaderCircle,
  Map as MapIcon,
  Network,
  Radio,
  Router,
  Search,
  Server,
  ShieldCheck,
  Signal,
  Sparkles,
  TriangleAlert,
  Wifi,
  X,
  Zap,
} from "lucide-react";
import { api } from "./api.js";

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "agents", label: "AI agents", icon: Sparkles },
  { id: "topology", label: "Network topology", icon: Network },
  { id: "telemetry", label: "Live telemetry", icon: Activity },
  { id: "incidents", label: "Incidents", icon: FileText },
];

const FALLBACK_SCENARIOS = [
  ["normal", "Normal operation"],
  ["latency_spike", "Latency spike"],
  ["packet_loss", "Packet loss"],
  ["network_congestion", "Network congestion"],
  ["cpu_overload", "CPU overload"],
  ["memory_overload", "Memory overload"],
  ["hardware_failure", "Hardware failure"],
  ["interface_failure", "Interface failure"],
  ["link_failure", "Link failure"],
  ["dns_failure", "DNS failure"],
  ["dhcp_failure", "DHCP failure"],
].map(([name, label]) => ({ name, label, description: "" }));

const AGENT_ICONS = [Gauge, Cpu, Radio, Sparkles, FileText];

function pretty(value = "") {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function confidencePercent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

function severityClass(value = "") {
  if (value === "critical" || value === "offline") return "critical";
  if (value === "warning") return "warning";
  return "healthy";
}

function formatTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function Sidebar({ activeView, onNavigate, incidentCount }) {
  return (
    <aside className="sidebar">
      <a className="brand" href="#" onClick={(event) => event.preventDefault()}>
        <span className="brand-mark"><Network size={20} strokeWidth={2.2} /></span>
        <span className="brand-copy">
          <strong>netcoop<span>·</span></strong>
          <small>AI NETWORK OPS</small>
        </span>
      </a>

      <nav className="primary-nav" aria-label="Main navigation">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            className={`nav-item ${activeView === id ? "active" : ""}`}
            key={id}
            onClick={() => onNavigate(id)}
          >
            <Icon size={17} />
            <span>{label}</span>
            {id === "incidents" && incidentCount > 0 && (
              <span className="nav-count">{incidentCount}</span>
            )}
          </button>
        ))}
      </nav>

    </aside>
  );
}

function StatusPill({ status, label }) {
  const Icon = status === "healthy" ? CheckCircle2 : (status === "critical" || status === "offline") ? AlertCircle : TriangleAlert;
  return (
    <span className={`status-pill ${severityClass(status)}`}>
      <Icon size={13} />
      {label || pretty(status)}
    </span>
  );
}

function StatCard({ icon: Icon, label, value, footnote, tone = "teal", trend }) {
  return (
    <article className="stat-card">
      <div className="stat-top">
        <span className={`stat-icon ${tone}`}><Icon size={18} /></span>
        {trend && (
          <span className={`trend ${trend.direction}`}>
            {trend.direction === "up" ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
            {trend.label}
          </span>
        )}
      </div>
      <p className="stat-label">{label}</p>
      <strong className="stat-value">{value}</strong>
      <span className="stat-footnote">{footnote}</span>
    </article>
  );
}

function SectionHeading({ eyebrow, title, action }) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
      </div>
      {action}
    </div>
  );
}

function ScenarioControl({ scenarios, selectedScenario, setSelectedScenario, seed, setSeed, onRun, running }) {
  return (
    <div className="run-control">
      <div className="run-intro">
        <span className="run-icon"><Zap size={18} fill="currentColor" /></span>
        <div>
          <strong>Run a diagnosis</strong>
          <span>Send a simulated network scenario to all agents</span>
        </div>
      </div>
      <div className="run-fields">
        <label className="field-control">
          <span>Scenario</span>
          <select value={selectedScenario} onChange={(event) => setSelectedScenario(event.target.value)}>
            {scenarios.map((scenario) => (
              <option value={scenario.name} key={scenario.name}>{scenario.label}</option>
            ))}
          </select>
        </label>
        <label className="field-control seed-control">
          <span>Seed</span>
          <input
            aria-label="Simulation seed"
            type="number"
            value={seed}
            onChange={(event) => setSeed(event.target.value)}
          />
        </label>
        <button className="button button-primary run-button" onClick={onRun} disabled={running}>
          {running ? <LoaderCircle size={16} className="spin" /> : <Sparkles size={16} />}
          {running ? "Analyzing…" : "Run diagnosis"}
        </button>
      </div>
    </div>
  );
}

function CauseCard({ incident, onExport }) {
  const cause = incident?.root_cause;
  const report = incident?.report;
  if (!incident || !cause) {
    return (
      <section className="card diagnosis-card empty-diagnosis">
        <div className="empty-icon"><Sparkles size={21} /></div>
        <div>
          <p className="eyebrow">LATEST DIAGNOSIS</p>
          <h2>Ready to investigate</h2>
          <p>Run a scenario to see the agents’ findings, likely cause, and recommended next steps here.</p>
        </div>
      </section>
    );
  }
  const status = cause.severity || report?.severity || "healthy";
  const actions = report?.recommended_actions || [];

  return (
    <section className="card diagnosis-card">
      <div className="diagnosis-topline">
        <div className="diagnosis-title">
          <span className={`cause-icon ${severityClass(status)}`}>
            {status === "healthy" ? <ShieldCheck size={19} /> : <TriangleAlert size={19} />}
          </span>
          <div>
            <p className="eyebrow">LATEST DIAGNOSIS <span className="dot-separator">·</span> {incident.incident_id}</p>
            <h2>{cause.label || report?.probable_root_cause || "Diagnosis complete"}</h2>
          </div>
        </div>
        <StatusPill status={status} />
      </div>
      <p className="diagnosis-summary">{report?.summary || "The agents have completed their analysis of the network snapshot."}</p>
      <div className="confidence-block">
        <div className="confidence-label">
          <span>Evidence confidence</span>
          <strong>{confidencePercent(cause.confidence)}</strong>
        </div>
        <div className="confidence-track"><span style={{ width: confidencePercent(cause.confidence) }} /></div>
        <span className="confidence-note">Evidence score, not a calibrated probability</span>
      </div>
      <div className="diagnosis-meta">
        <div><MapIcon size={14} /><span>Likely source</span><strong>{cause.root_device || "Campus-wide"}</strong></div>
        <div><Radio size={14} /><span>Affected devices</span><strong>{cause.affected_devices?.length ?? 0}</strong></div>
        <div><Clock3 size={14} /><span>Completed in</span><strong>{incident.duration_ms ? `${Math.round(incident.duration_ms)} ms` : "—"}</strong></div>
      </div>
      {actions.length > 0 && (
        <div className="action-preview">
          <div className="action-preview-heading"><Check size={14} /><strong>Recommended next step</strong></div>
          <p>{actions[0]}</p>
        </div>
      )}
      <div className="diagnosis-footer">
        <span><CheckCircle2 size={14} /> Report generated by {report?.generated_by || "rules"}</span>
        <button className="text-button" onClick={onExport}><Download size={14} /> Export report</button>
      </div>
    </section>
  );
}

function AgentCards({ agents, incident }) {
  const messages = incident?.agent_messages || [];
  return (
    <div className="agent-grid">
      {agents.map((agent, index) => {
        const message = messages.find((entry) => entry.sender === agent.name);
        const status = message?.status || "healthy";
        const Icon = AGENT_ICONS[index % AGENT_ICONS.length];
        const findings = message?.findings || [];
        return (
          <article className="agent-card" key={agent.name}>
            <div className="agent-card-top">
              <span className={`agent-icon agent-${index % AGENT_ICONS.length}`}><Icon size={17} /></span>
              <span className={`agent-status-dot ${message ? severityClass(status) : "idle"}`} />
            </div>
            <p className="agent-role">{pretty(agent.role)}</p>
            <h3>{pretty(agent.name)}</h3>
            <p className="agent-description">{agent.description}</p>
            <div className="agent-card-bottom">
              <span className={`agent-state ${message ? severityClass(status) : "idle"}`}>
                {message ? (status === "healthy" ? "Analysis complete" : pretty(status)) : "Awaiting run"}
              </span>
              <span>{findings.length} finding{findings.length === 1 ? "" : "s"}</span>
            </div>
          </article>
        );
      })}
      {agents.length === 0 && <div className="inline-empty">Agent registry will appear when the API is available.</div>}
    </div>
  );
}

function DeviceInspector({ device, onClose }) {
  if (!device) return null;
  const m = device.metrics;
  const isHealthy = m.reachable && m.cpu_utilization_pct < 80 && m.latency_ms < 80 && m.packet_loss_pct < 1;
  const status = !m.reachable ? "offline" : isHealthy ? "healthy" : (m.cpu_utilization_pct >= 95 || m.packet_loss_pct >= 10) ? "critical" : "warning";

  return (
    <div className="device-inspector">
      <div className="inspector-topline">
        <div className="inspector-title">
          <Router size={18} />
          <div>
            <h3>{device.device_id}</h3>
            <span style={{ fontSize: "11px", color: "var(--muted)" }}>{pretty(device.device_type)} · Live Monitored Metrics</span>
          </div>
          <StatusPill status={status === "offline" ? "critical" : status} label={status === "offline" ? "Unreachable" : pretty(status)} />
        </div>
        <button className="icon-button subtle" onClick={onClose} aria-label="Close inspector">
          <X size={15} />
        </button>
      </div>
      <div className="inspector-metrics-grid">
        <div className="inspector-metric-card">
          <span>CPU UTILIZATION</span>
          <strong style={{ color: m.cpu_utilization_pct >= 85 ? "#de5252" : "inherit" }}>{m.cpu_utilization_pct.toFixed(1)}%</strong>
        </div>
        <div className="inspector-metric-card">
          <span>MEMORY UTILIZATION</span>
          <strong>{m.memory_utilization_pct.toFixed(1)}%</strong>
        </div>
        <div className="inspector-metric-card">
          <span>LATENCY</span>
          <strong style={{ color: m.latency_ms >= 100 ? "#de5252" : "inherit" }}>{m.latency_ms.toFixed(1)} ms</strong>
        </div>
        <div className="inspector-metric-card">
          <span>JITTER</span>
          <strong>{m.jitter_ms.toFixed(1)} ms</strong>
        </div>
        <div className="inspector-metric-card">
          <span>PACKET LOSS</span>
          <strong style={{ color: m.packet_loss_pct > 1 ? "#de5252" : "inherit" }}>{m.packet_loss_pct.toFixed(2)}%</strong>
        </div>
        <div className="inspector-metric-card">
          <span>LINK UTILIZATION</span>
          <strong>{m.link_utilization_pct.toFixed(1)}%</strong>
        </div>
        <div className="inspector-metric-card">
          <span>INTERFACE ERRORS</span>
          <strong style={{ color: m.interface_errors > 0 ? "#de5252" : "inherit" }}>{m.interface_errors}</strong>
        </div>
        <div className="inspector-metric-card">
          <span>QUEUE DROPS</span>
          <strong>{m.queue_drops}</strong>
        </div>
      </div>
    </div>
  );
}

function TopologyMap({ topology, incident, expanded = false, telemetry, selectedDeviceId, onSelectDevice }) {
  const nodes = topology?.nodes || [];
  const edges = topology?.edges || [];
  const impacted = new Set(incident?.root_cause?.affected_devices || []);
  const rootDevice = incident?.root_cause?.root_device;
  const core = topology?.core;

  const selectedDevice = useMemo(() => {
    if (!selectedDeviceId || !telemetry?.devices) return null;
    return telemetry.devices.find((d) => d.device_id === selectedDeviceId);
  }, [selectedDeviceId, telemetry]);

  const positions = useMemo(() => {
    const groups = {
      router: nodes.filter((node) => node.type === "router"),
      switch: nodes.filter((node) => node.type === "switch"),
      access_point: nodes.filter((node) => node.type === "access_point"),
      server: nodes.filter((node) => node.type === "server"),
    };
    const map = new Map();
    groups.router.forEach((node, index) => {
      map.set(node.id, node.id === core ? { x: 450, y: 48 } : {
        x: groups.router.length === 2 ? 300 + index * 300 : index === 1 ? 300 : 600,
        y: 135,
      });
    });
    groups.switch.forEach((node, index) => map.set(node.id, {
      x: 90 + index * (720 / Math.max(groups.switch.length - 1, 1)),
      y: 230,
    }));
    groups.access_point.forEach((node, index) => map.set(node.id, {
      x: 40 + index * (820 / Math.max(groups.access_point.length - 1, 1)),
      y: 354,
    }));
    groups.server.forEach((node, index) => map.set(node.id, { x: 820, y: 100 + index * 86 }));
    return map;
  }, [nodes, core]);

  const counts = useMemo(() => nodes.reduce((result, node) => {
    result[node.type] = (result[node.type] || 0) + 1;
    return result;
  }, {}), [nodes]);

  if (nodes.length === 0) {
    return <div className="topology-empty"><Network size={22} /><span>Topology data will appear when the API is available.</span></div>;
  }

  return (
    <div className={`topology-content ${expanded ? "expanded" : ""}`}>
      <div className="topology-summary">
        <span><span className="legend-dot core-dot" /> Core</span>
        <span><span className="legend-dot device-dot" /> Network device</span>
        <span><span className="legend-dot server-dot" /> Server</span>
        <span><span className="legend-dot impacted-dot" /> Degraded / Affected</span>
      </div>
      <div className="topology-canvas">
        <svg viewBox="0 0 900 410" role="img" aria-label="Campus network topology diagram">
          {edges.map((edge, index) => {
            const from = positions.get(edge.source);
            const to = positions.get(edge.target);
            if (!from || !to) return null;
            const affected = impacted.has(edge.source) || impacted.has(edge.target)
              || edge.source === rootDevice || edge.target === rootDevice;
            return (
              <line
                key={`${edge.source}-${edge.target}-${index}`}
                className={`topology-link ${affected ? "affected" : ""} ${edge.primary === false ? "redundant" : ""}`}
                x1={from.x} y1={from.y} x2={to.x} y2={to.y}
              />
            );
          })}
          {nodes.map((node) => {
            const point = positions.get(node.id);
            if (!point) return null;
            const devTelemetry = telemetry?.devices?.find((d) => d.device_id === node.id);
            const isAffectedByIncident = impacted.has(node.id) || node.id === rootDevice;
            const isLiveAnomalous = devTelemetry && (!devTelemetry.metrics.reachable || devTelemetry.metrics.cpu_utilization_pct >= 85 || devTelemetry.metrics.latency_ms >= 100);
            const affected = isAffectedByIncident || isLiveAnomalous;
            const isCore = node.id === core;
            const isServer = node.type === "server";
            const isSelected = selectedDeviceId === node.id;

            return (
              <g
                className="topology-node"
                key={node.id}
                transform={`translate(${point.x}, ${point.y})`}
                onClick={() => onSelectDevice && onSelectDevice(node.id)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  r={isCore ? 17 : 12}
                  className={`${isCore ? "node-core" : isServer ? "node-server" : "node-device"} ${affected ? "node-affected" : ""} ${isSelected ? "node-selected" : ""}`}
                />
                {isCore ? <Router size={15} x={-7.5} y={-7.5} /> : isServer ? <Server size={12} x={-6} y={-6} /> : node.type === "access_point" ? <Wifi size={12} x={-6} y={-6} /> : <EthernetPort size={12} x={-6} y={-6} />}
                <text x="0" y={isCore ? -26 : -20} textAnchor="middle">{node.id.replace("RTR_CAMPUS_", "RTR-").replace("SW_CAMPUS_", "SW-").replace("AP_CAMPUS_", "AP-").replace("SRV_", "")}</text>
              </g>
            );
          })}
          {nodes.filter((node) => node.type === "router" && node.id !== core).map((node, index) => {
            const point = positions.get(node.id);
            return <text className="topology-tier-label" key={`tier-${node.id}`} x={point.x} y={173} textAnchor="middle">DISTRIBUTION {index + 1}</text>;
          })}
          {groupsLabel(nodes, "switch").map((label, index) => (
            <text className="topology-tier-label" key={label} x={450} y={273 + index * 12} textAnchor="middle">{label}</text>
          ))}
          <text className="topology-side-label" x="450" y="397" textAnchor="middle">CAMPUS ACCESS POINTS</text>
        </svg>
      </div>
      <div className="topology-counts">
        <span><i className="legend-dot core-dot" />{counts.router || 0} routers</span>
        <span><i className="legend-dot device-dot" />{counts.switch || 0} switches</span>
        <span><i className="legend-dot device-dot" />{counts.access_point || 0} access points</span>
        <span><i className="legend-dot server-dot" />{counts.server || 0} servers</span>
      </div>

      {selectedDevice && (
        <DeviceInspector device={selectedDevice} onClose={() => onSelectDevice(null)} />
      )}
    </div>
  );
}

function groupsLabel(nodes, type) {
  return nodes.some((node) => node.type === type) ? ["ACCESS SWITCHES"] : [];
}

function EvidencePanel({ incident }) {
  const report = incident?.report;
  const evidence = report?.evidence || [];
  const alternatives = report?.alternatives || [];
  const metrics = report?.key_metrics || {};
  const recommendations = report?.recommended_actions || [];

  if (!incident) {
    return <div className="inline-empty">Run a diagnosis to see supporting evidence and recommendations.</div>;
  }
  return (
    <div className="evidence-panel">
      {Object.keys(metrics).length > 0 && (
        <div className="metric-list">
          {Object.entries(metrics).slice(0, 5).map(([label, value]) => {
            const numeric = Number(value);
            const percent = label.includes("%");
            const normalized = percent ? numeric : Math.min(numeric / (label.includes("Latency") ? 500 : 100), 1) * 100;
            return (
              <div className="metric-row" key={label}>
                <div className="metric-name"><span>{label}</span><strong>{numeric.toFixed(label.includes("Latency") ? 0 : 1)}{percent ? "%" : label.includes("Latency") ? " ms" : ""}</strong></div>
                <div className="metric-track"><span style={{ width: `${Math.min(normalized, 100)}%` }} /></div>
              </div>
            );
          })}
        </div>
      )}
      {evidence.length > 0 && (
        <div className="evidence-list">
          <p className="subsection-title">Evidence from the agents</p>
          {evidence.slice(0, 4).map((item, index) => (
            <div className="evidence-item" key={`${index}-${item}`}>
              <span className="evidence-check"><Check size={12} /></span>
              <p>{item}</p>
            </div>
          ))}
        </div>
      )}
      {alternatives.length > 0 && (
        <div className="alternatives">
          <p className="subsection-title">Other possibilities</p>
          {alternatives.map((alternative) => (
            <span className="alternative-chip" key={alternative.cause}>
              {pretty(alternative.cause)} <small>{confidencePercent(alternative.score)}</small>
            </span>
          ))}
        </div>
      )}
      {recommendations.length > 1 && (
        <details className="more-actions">
          <summary>View all {recommendations.length} recommended actions</summary>
          <ol>{recommendations.map((action) => <li key={action}>{action}</li>)}</ol>
        </details>
      )}
      {report?.disclaimer && <p className="report-disclaimer">{report.disclaimer}</p>}
    </div>
  );
}

function ActivityFeed({ incident }) {
  const timeline = incident?.timeline || [];
  if (!incident) {
    return <div className="activity-empty"><Activity size={17} /><span>Agent activity will show up after a diagnosis.</span></div>;
  }
  return (
    <div className="activity-list">
      {timeline.slice(-5).reverse().map((entry, index) => (
        <div className="activity-item" key={`${entry.actor}-${entry.event}-${index}`}>
          <span className={`activity-marker ${entry.event === "error" ? "error" : entry.event === "diagnosis" ? "highlight" : ""}`}>
            {entry.event === "error" ? <AlertCircle size={12} /> : entry.event === "diagnosis" ? <Sparkles size={12} /> : <Check size={12} />}
          </span>
          <div className="activity-copy">
            <div><strong>{pretty(entry.actor)}</strong><time>{entry.t_ms} ms</time></div>
            <p>{entry.detail}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function LiveTelemetryTable({ telemetry, onSelectDevice, selectedDeviceId }) {
  const [filterType, setFilterType] = useState("all");
  const [search, setSearch] = useState("");
  const [showAll, setShowAll] = useState(false);

  const devices = telemetry?.devices || [];
  const filtered = useMemo(() => {
    return devices.filter((d) => {
      const matchesType = filterType === "all"
        ? true
        : filterType === "anomalies"
        ? (!d.metrics.reachable || d.metrics.cpu_utilization_pct >= 80 || d.metrics.latency_ms >= 80 || d.metrics.packet_loss_pct >= 1.0)
        : d.device_type === filterType;
      const matchesSearch = d.device_id.toLowerCase().includes(search.toLowerCase());
      return matchesType && matchesSearch;
    });
  }, [devices, filterType, search]);
  const visibleDevices = showAll ? filtered : filtered.slice(0, 5);

  return (
    <div className="card incident-card telemetry-card" id="telemetry">
      <SectionHeading
        eyebrow="REAL-TIME TELEMETRY"
        title="Live Monitored Devices"
        action={
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <span className="live-telemetry-badge">
              <span className="live-pulse-dot" /> LIVE STREAMING
            </span>
            <label className="search-field">
              <Search size={15} />
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search device..." />
            </label>
          </div>
        }
      />
      <div className="telemetry-table-filters">
        {["all", "router", "switch", "access_point", "server", "anomalies"].map((type) => (
          <button
            key={type}
            className={`filter-chip ${filterType === type ? "active" : ""}`}
            onClick={() => setFilterType(type)}
          >
            {type === "all" ? "All Devices (20)" : type === "anomalies" ? "Anomalies Only" : pretty(type) + "s"}
          </button>
        ))}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>DEVICE ID</th>
              <th>TYPE</th>
              <th>STATUS</th>
              <th>CPU UTIL</th>
              <th>MEMORY</th>
              <th>LATENCY</th>
              <th>PACKET LOSS</th>
              <th>LINK UTIL</th>
              <th>ERRORS</th>
            </tr>
          </thead>
          <tbody>
            {visibleDevices.map((d) => {
              const m = d.metrics;
              const isCrit = !m.reachable || m.cpu_utilization_pct >= 95 || m.packet_loss_pct >= 10;
              const isWarn = m.cpu_utilization_pct >= 80 || m.latency_ms >= 80 || m.packet_loss_pct >= 1;
              const status = !m.reachable ? "offline" : isCrit ? "critical" : isWarn ? "warning" : "healthy";
              return (
                <tr
                  key={d.device_id}
                  className={`device-row-clickable ${selectedDeviceId === d.device_id ? "selected-row" : ""}`}
                  onClick={() => onSelectDevice(d.device_id)}
                >
                  <td className="incident-id"><strong>{d.device_id}</strong></td>
                  <td>{pretty(d.device_type)}</td>
                  <td><StatusPill status={status === "offline" ? "critical" : status} label={status === "offline" ? "Unreachable" : pretty(status)} /></td>
                  <td>
                    <span>{m.cpu_utilization_pct.toFixed(1)}%</span>
                    <span className="mini-gauge">
                      <span className="mini-gauge-bar" style={{ width: `${Math.min(m.cpu_utilization_pct, 100)}%`, background: m.cpu_utilization_pct >= 85 ? "#de5252" : "#1ca386" }} />
                    </span>
                  </td>
                  <td>
                    <span>{m.memory_utilization_pct.toFixed(1)}%</span>
                    <span className="mini-gauge">
                      <span className="mini-gauge-bar" style={{ width: `${Math.min(m.memory_utilization_pct, 100)}%`, background: m.memory_utilization_pct >= 85 ? "#e58a2d" : "#1ca386" }} />
                    </span>
                  </td>
                  <td><strong style={{ color: m.latency_ms >= 100 ? "#de5252" : "inherit" }}>{m.latency_ms.toFixed(1)} ms</strong></td>
                  <td><span style={{ color: m.packet_loss_pct > 1 ? "#de5252" : "inherit" }}>{m.packet_loss_pct.toFixed(2)}%</span></td>
                  <td>{m.link_utilization_pct.toFixed(1)}%</td>
                  <td>{m.interface_errors > 0 ? <strong style={{ color: "#de5252" }}>{m.interface_errors}</strong> : "0"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {filtered.length > 5 && (
        <div className="telemetry-show-more-wrap">
          <button
            className="button button-secondary telemetry-show-more"
            type="button"
            aria-expanded={showAll}
            onClick={() => setShowAll((current) => !current)}
          >
            {showAll ? "Show less" : "Show more"}
          </button>
        </div>
      )}
    </div>
  );
}

function IncidentTable({ incidents, onSelect, selectedId, search, setSearch }) {
  const filtered = incidents.filter((incident) =>
    `${incident.incident_id} ${incident.root_cause} ${incident.root_device || ""}`.toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <div className="card incident-card">
      <SectionHeading
        eyebrow="RECENT ACTIVITY"
        title="Incident history"
        action={
          <label className="search-field">
            <Search size={15} />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search incidents" />
          </label>
        }
      />
      {filtered.length === 0 ? (
        <div className="table-empty"><FileText size={22} /><strong>No incidents yet</strong><span>Run a diagnosis and it will appear here.</span></div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead><tr><th>INCIDENT</th><th>ROOT CAUSE</th><th>SEVERITY</th><th>CONFIDENCE</th><th>DEVICE</th><th>TIME</th><th /></tr></thead>
            <tbody>
              {filtered.map((incident) => (
                <tr
                  key={incident.incident_id}
                  className={selectedId === incident.incident_id ? "selected-row" : ""}
                  onClick={() => onSelect(incident.incident_id)}
                  tabIndex={0}
                  onKeyDown={(event) => event.key === "Enter" && onSelect(incident.incident_id)}
                >
                  <td className="incident-id">{incident.incident_id}</td>
                  <td>{incident.root_cause}</td>
                  <td><StatusPill status={incident.severity} /></td>
                  <td>{confidencePercent(incident.confidence)}</td>
                  <td className="device-cell">{incident.root_device || "—"}</td>
                  <td>{formatTime(incident.created_at)}</td>
                  <td><ArrowRight size={15} className="row-arrow" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function App() {
  const [activeView, setActiveView] = useState("overview");
  const [apiReady, setApiReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [agents, setAgents] = useState([]);
  const [topology, setTopology] = useState(null);
  const [liveTelemetry, setLiveTelemetry] = useState(null);
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [scenarios, setScenarios] = useState(FALLBACK_SCENARIOS);
  const [incidents, setIncidents] = useState([]);
  const [incident, setIncident] = useState(null);
  const [scenario, setScenario] = useState("network_congestion");
  const [seed, setSeed] = useState("42");
  const [running, setRunning] = useState(false);
  const [search, setSearch] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    const results = await Promise.allSettled([
      api.health(),
      api.scenarios(),
      api.topology(),
      api.agents(),
      api.history(),
      api.liveTelemetry(),
    ]);
    const [healthResult, scenarioResult, topologyResult, agentResult, historyResult, telemetryResult] = results;
    const loadErrors = [];

    if (healthResult.status === "fulfilled") {
      setApiReady(true);
    } else {
      setApiReady(false);
      loadErrors.push(healthResult.reason.message);
    }
    if (healthResult.status === "fulfilled") {
      const failures = results.slice(1).flatMap((result, index) =>
        result.status === "rejected"
          ? [`${["scenarios", "topology", "agents", "incident history", "live telemetry"][index]}: ${result.reason.message}`]
          : [],
      );
      loadErrors.push(...failures);
    }
    if (scenarioResult.status === "fulfilled" && scenarioResult.value.scenarios?.length) {
      setScenarios(scenarioResult.value.scenarios);
    }
    if (topologyResult.status === "fulfilled") setTopology(topologyResult.value);
    if (agentResult.status === "fulfilled") setAgents(agentResult.value.agents || []);
    if (telemetryResult.status === "fulfilled") {
      setLiveTelemetry(telemetryResult.value);
      setLastUpdated(new Date());
    }
    if (historyResult.status === "fulfilled") {
      const history = historyResult.value.incidents || [];
      setIncidents(history);
      if (history.length > 0) {
        try {
          setIncident(await api.incident(history[0].incident_id));
        } catch (requestError) {
          loadErrors.push(`latest incident: ${requestError.message}`);
        }
      } else {
        setIncident(null);
      }
    }
    setError(loadErrors.length > 0 ? `Some dashboard data could not be loaded. ${loadErrors.join(" · ")}` : "");
    setLoading(false);
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // Live polling interval every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(async () => {
      try {
        const [tel, hist] = await Promise.allSettled([
          api.liveTelemetry(),
          api.history(),
        ]);
        if (tel.status === "fulfilled") {
          setLiveTelemetry(tel.value);
          setLastUpdated(new Date());
        }
        if (hist.status === "fulfilled" && hist.value.incidents) {
          setIncidents(hist.value.incidents);
        }
      } catch {
        // silent polling catch
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleRun = async () => {
    setRunning(true);
    setError("");
    try {
      const result = await api.simulate(scenario, seed === "" ? null : Number(seed));
      setIncident(result);
      const [historyResult, telResult] = await Promise.allSettled([
        api.history(),
        api.liveTelemetry(),
      ]);
      if (historyResult.status === "fulfilled") {
        setIncidents(historyResult.value.incidents || []);
      }
      if (telResult.status === "fulfilled") {
        setLiveTelemetry(telResult.value);
        setLastUpdated(new Date());
      }
      if (result?.root_cause?.root_device) {
        setSelectedDeviceId(result.root_cause.root_device);
      }
      setActiveView("overview");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setRunning(false);
    }
  };

  const selectIncident = async (id) => {
    setError("");
    try {
      const result = await api.incident(id);
      setIncident(result);
      if (result?.root_cause?.root_device) {
        setSelectedDeviceId(result.root_cause.root_device);
      }
      setActiveView("overview");
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  const navigate = (id) => {
    setActiveView(id);
    if (id !== "overview") {
      requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" }));
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const exportReport = () => {
    if (!incident) return;
    const content = JSON.stringify(incident.report || incident, null, 2);
    const url = URL.createObjectURL(new Blob([content], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${incident.incident_id}-report.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const statusSummary = useMemo(() => {
    const critical = incidents.filter((item) => item.severity === "critical").length;
    const warning = incidents.filter((item) => item.severity === "warning").length;
    return { critical, warning };
  }, [incidents]);

  return (
    <div className="app-shell">
      <Sidebar activeView={activeView} onNavigate={navigate} incidentCount={incidents.length} />
      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <strong>{NAV_ITEMS.find((item) => item.id === activeView)?.label || "Overview"}</strong>
          </div>
          <div className="topbar-actions">
            <span className="live-telemetry-badge">
              <span className="live-pulse-dot" /> LIVE MONITORED {lastUpdated ? `· ${formatTime(lastUpdated)}` : ""}
            </span>
            <div className="topbar-date"><span>Today</span><strong>{new Date().toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}</strong></div>
          </div>
        </header>

        <div className="page-content" id="overview">
          <div className="page-heading">
            <div>
              <div className="welcome-line"><span className="welcome-dot" /> CAMPUS NETWORK OPERATIONS</div>
              <h1>Network overview</h1>
              <p>Real-time campus network operations, multi-agent fault diagnosis & live telemetry.</p>
            </div>
            <div style={{ display: "flex", gap: "10px" }}>
              <button
                className={`button button-secondary`}
                onClick={() => setAutoRefresh(!autoRefresh)}
                title={autoRefresh ? "Pause 5s auto-polling" : "Resume 5s auto-polling"}
              >
                <Activity size={15} style={{ color: autoRefresh ? "#14796d" : "#7c898c" }} />
                {autoRefresh ? "Live: Polling (5s)" : "Polling Paused"}
              </button>
            </div>
          </div>

          {error && (
            <div className="error-banner" role="alert">
              <AlertCircle size={17} />
              <div><strong>{apiReady ? "Request couldn’t be completed" : "Backend not connected"}</strong><span>{error}</span></div>
              <button className="icon-button" onClick={() => setError("")} aria-label="Dismiss error"><X size={15} /></button>
            </div>
          )}

          {!apiReady && !loading && (
            <div className="demo-notice"><CircleHelp size={15} /><span>Dashboard is connected to the backend API when it’s running. Start FastAPI at <code>127.0.0.1:8000</code> to load live topology and run diagnoses.</span></div>
          )}

          <ScenarioControl
            scenarios={scenarios}
            selectedScenario={scenario}
            setSelectedScenario={setScenario}
            seed={seed}
            setSeed={setSeed}
            onRun={handleRun}
            running={running}
          />

          <section className="stats-grid" aria-label="Network summary">
            <StatCard
              icon={Network}
              label="Devices monitored"
              value={liveTelemetry ? `${liveTelemetry.online_count ?? topology?.nodes?.length ?? 20} / ${liveTelemetry.device_count ?? topology?.nodes?.length ?? 20}` : (topology ? topology.nodes?.length ?? "—" : "—")}
              footnote={liveTelemetry ? `${liveTelemetry.healthy_count ?? 0} optimal · ${liveTelemetry.warning_count ?? 0} warning` : "Across campus topology"}
              tone="teal"
            />
            <StatCard
              icon={Activity}
              label="Campus Avg Latency"
              value={liveTelemetry?.averages ? `${liveTelemetry.averages.avg_latency_ms} ms` : "—"}
              footnote={liveTelemetry?.averages ? `Packet loss: ${liveTelemetry.averages.avg_packet_loss_pct}%` : "Live monitored"}
              tone="blue"
            />
            <StatCard
              icon={Cpu}
              label="Campus Avg CPU"
              value={liveTelemetry?.averages ? `${liveTelemetry.averages.avg_cpu_pct}%` : "—"}
              footnote={liveTelemetry?.averages ? `Avg RAM: ${liveTelemetry.averages.avg_memory_pct}%` : "Across all nodes"}
              tone={liveTelemetry?.averages?.avg_cpu_pct >= 80 ? "rose" : "violet"}
            />
            <StatCard
              icon={TriangleAlert}
              label="Network Status"
              value={incident ? pretty(incident.root_cause?.severity || "healthy") : (liveTelemetry?.critical_count > 0 ? "Critical" : liveTelemetry?.warning_count > 0 ? "Warning" : "Optimal")}
              footnote={incident ? incident.root_cause?.label : (liveTelemetry ? `${liveTelemetry.healthy_count} of ${liveTelemetry.device_count} nodes optimal` : "Monitoring live")}
              tone={incident?.root_cause?.severity === "critical" || liveTelemetry?.critical_count > 0 ? "rose" : "teal"}
            />
          </section>

          <div className="primary-grid">
            <CauseCard incident={incident} onExport={exportReport} />
            <section className="card activity-card">
              <SectionHeading
                eyebrow="LIVE WORKFLOW"
                title="Agent activity"
                action={<span className={`live-badge ${running ? "working" : ""}`}><span />{running ? "Working" : incident ? "Latest run" : "Ready"}</span>}
              />
              <ActivityFeed incident={incident} />
            </section>
          </div>

          <section className="page-section" id="agents">
            <SectionHeading
              eyebrow="MULTI-AGENT SYSTEM"
              title="Your AI agents"
              action={<button className="text-button" onClick={() => navigate("agents")}>View agents <ArrowRight size={14} /></button>}
            />
            <AgentCards agents={agents} incident={incident} />
          </section>

          <div className="secondary-grid">
            <section className="card topology-card page-section" id="topology">
              <SectionHeading
                eyebrow="CAMPUS INFRASTRUCTURE"
                title="Network topology"
                action={
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <span style={{ fontSize: "11px", color: "var(--muted)" }}>Click node to inspect live metrics</span>
                    <button className="icon-button card-action" aria-label="View topology" onClick={() => navigate("topology")}><ArrowRight size={16} /></button>
                  </div>
                }
              />
              <TopologyMap
                topology={topology}
                incident={incident}
                telemetry={liveTelemetry}
                selectedDeviceId={selectedDeviceId}
                onSelectDevice={setSelectedDeviceId}
              />
            </section>

            <section className="card evidence-card">
              <SectionHeading eyebrow="INCIDENT INSIGHTS" title="Evidence & actions" />
              <EvidencePanel incident={incident} />
            </section>
          </div>

          <section className="page-section" id="telemetry">
            <LiveTelemetryTable
              telemetry={liveTelemetry}
              onSelectDevice={(id) => {
                setSelectedDeviceId(id);
                document.getElementById("topology")?.scrollIntoView({ behavior: "smooth", block: "start" });
              }}
              selectedDeviceId={selectedDeviceId}
            />
          </section>

          <section className="page-section" id="incidents">
            <IncidentTable
              incidents={incidents}
              onSelect={selectIncident}
              selectedId={incident?.incident_id}
              search={search}
              setSearch={setSearch}
            />
          </section>

          <footer className="page-footer">
            <span><ShieldCheck size={14} /> Recommendations are advisory and require administrator verification.</span>
            <span>Live monitored telemetry · NetCoop AI</span>
          </footer>
        </div>
      </main>
      {running && (
        <div className="run-toast" role="status"><LoaderCircle className="spin" size={16} /> Agents are collaborating on your diagnosis…</div>
      )}
    </div>
  );
}

export default App;

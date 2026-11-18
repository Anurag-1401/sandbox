
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent
} from "react";
import {
  Activity,
  AlertCircle,
  ArrowDownUp,
  Check,
  ChevronDown,
  CircleDot,
  FileText,
  Filter,
  GitBranch,
  Layers3,
  LoaderCircle,
  Network,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  X
} from "lucide-react";

import {
  knowledgeGraphApi,
  NODE_TYPES,
  RELATION_TYPES,
  type GraphEdge,
  type GraphEvidence,
  type GraphNode,
  type NodeType,
  type RelationType,
  type VerificationStatus
} from "./knowledge-graph-api";

import { getApiErrorMessage } from "../../lib/api";
import { PageHeader } from "../../components/ui/PageHeader";

type Tab = "overview" | "evidence";

const NODE_COLORS: Record<NodeType, string> = {
  regulation: "#6478d8",
  clause: "#8b6bc7",
  amendment: "#c17b43",
  obligation: "#c15c69",
  standard: "#318b83",
  product: "#3e91b5",
  organization: "#66758d",
  authority: "#a27a42",
  concept: "#7b8494"
};

const NODE_LABELS: Record<NodeType, string> = {
  regulation: "Regulation",
  clause: "Clause",
  amendment: "Amendment",
  obligation: "Obligation",
  standard: "Standard",
  product: "Product",
  organization: "Organization",
  authority: "Authority",
  concept: "Concept"
};

const RELATION_LABELS: Record<RelationType, string> = {
  contains: "Contains",
  amends: "Amends",
  supersedes: "Supersedes",
  repeals: "Repeals",
  requires: "Requires",
  applies_to: "Applies to",
  references: "References",
  defines: "Defines",
  issued_by: "Issued by",
  governs: "Governs",
  implements: "Implements",
  conflicts_with: "Conflicts with",
  related_to: "Related to",
  derived_from: "Derived from"
};

function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString();
}

function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function VerificationPill({
  status
}: {
  status: VerificationStatus;
}) {
  const className = {
    verified: "kg-verification verified",
    reviewed: "kg-verification reviewed",
    rejected: "kg-verification rejected",
    unverified: "kg-verification unverified"
  }[status];

  return (
    <span className={className}>
      <span />
      {titleCase(status)}
    </span>
  );
}

function GraphCanvas({
  nodes,
  edges,
  selectedId,
  rootId,
  onSelect
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedId: string | null;
  rootId: string | null;
  onSelect: (node: GraphNode) => void;
}) {
  const width = 900;
  const height = 540;

  const positions = useMemo(() => {
    const result = new Map<string, { x: number; y: number }>();

    if (!nodes.length) return result;

    const rootIndex = Math.max(
      0,
      nodes.findIndex((node) => node.id === rootId)
    );

    const ordered = [...nodes];
    const [root] = ordered.splice(rootIndex, 1);
    const center = { x: width / 2, y: height / 2 };

    if (root) result.set(root.id, center);

    const radius = Math.min(205, 75 + ordered.length * 11);

    ordered.forEach((node, index) => {
      const angle =
        (Math.PI * 2 * index) / Math.max(ordered.length, 1) -
        Math.PI / 2;

      result.set(node.id, {
        x: center.x + Math.cos(angle) * radius,
        y: center.y + Math.sin(angle) * radius
      });
    });

    return result;
  }, [nodes, rootId]);

  if (!nodes.length) {
    return (
      <div className="kg-canvas-empty">
        <Network size={34} />
        <h3>No graph loaded</h3>
        <p>Search for an entity and select it to explore its connected graph.</p>
      </div>
    );
  }

  return (
    <div className="kg-canvas-scroll">
      <svg
        className="kg-graph-svg"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Interactive knowledge graph"
      >
        <defs>
          <pattern
            id="kg-grid"
            width="28"
            height="28"
            patternUnits="userSpaceOnUse"
          >
            <circle cx="1" cy="1" r="1" fill="#dfe5ef" />
          </pattern>
        </defs>

        <rect
          width={width}
          height={height}
          fill="url(#kg-grid)"
        />

        {edges.map((edge) => {
          const source = positions.get(edge.source_node_id);
          const target = positions.get(edge.target_node_id);

          if (!source || !target) return null;

          const middleX = (source.x + target.x) / 2;
          const middleY = (source.y + target.y) / 2;

          return (
            <g key={edge.id}>
              <line
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke={
                  edge.verification_status === "verified"
                    ? "#8ca1b8"
                    : "#c3ccd8"
                }
                strokeWidth="1.7"
                strokeDasharray={
                  edge.verification_status === "verified"
                    ? undefined
                    : "5 5"
                }
              />
              <rect
                x={middleX - 45}
                y={middleY - 10}
                width="90"
                height="20"
                rx="5"
                fill="#ffffff"
                stroke="#e4e9f0"
              />
              <text
                x={middleX}
                y={middleY + 3}
                textAnchor="middle"
                fontSize="9"
                fill="#667085"
              >
                {RELATION_LABELS[edge.relation_type] ?? edge.relation_type}
              </text>
            </g>
          );
        })}

        {nodes.map((node) => {
          const position = positions.get(node.id);
          if (!position) return null;

          const selected = selectedId === node.id;
          const root = rootId === node.id;
          const color = NODE_COLORS[node.node_type];

          return (
            <g
              key={node.id}
              transform={`translate(${position.x}, ${position.y})`}
              className="kg-graph-node"
              role="button"
              tabIndex={0}
              aria-label={`Select ${node.name}`}
              onClick={() => onSelect(node)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(node);
                }
              }}
            >
              {(selected || root) && (
                <circle
                  r="34"
                  fill={color}
                  opacity="0.12"
                />
              )}
              <circle
                r={selected ? 25 : 21}
                fill={color}
                stroke={selected ? "#263247" : "#ffffff"}
                strokeWidth={selected ? 3 : 2}
              />
              <circle
                cx="15"
                cy="-15"
                r="5"
                fill={
                  node.verification_status === "verified"
                    ? "#20a477"
                    : node.verification_status === "rejected"
                      ? "#d45a67"
                      : "#e0a34b"
                }
                stroke="#fff"
                strokeWidth="1.5"
              />
              <text
                y="39"
                textAnchor="middle"
                fontSize="11"
                fontWeight={selected ? "700" : "600"}
                fill="#344054"
              >
                {node.name.length > 22
                  ? `${node.name.slice(0, 20)}…`
                  : node.name}
              </text>
              <text
                y="52"
                textAnchor="middle"
                fontSize="9"
                fill="#8a94a5"
              >
                {NODE_LABELS[node.node_type]}
              </text>
              <title>
                {node.name} — {node.node_type}
              </title>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function NodeCreationForm({
  onClose,
  onCreated
}: {
  onClose: () => void;
  onCreated: (node: GraphNode) => void;
}) {
  const [name, setName] = useState("");
  const [nodeType, setNodeType] = useState<NodeType>("regulation");
  const [description, setDescription] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [externalIdentifier, setExternalIdentifier] = useState("");
  const [confidence, setConfidence] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      const node = await knowledgeGraphApi.createNode({
        node_type: nodeType,
        name: name.trim(),
        description: description.trim() || null,
        jurisdiction: jurisdiction.trim() || null,
        external_identifier: externalIdentifier.trim() || null,
        confidence: confidence === "" ? null : Number(confidence),
        aliases: [],
        properties: {}
      });

      onCreated(node);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="kg-modal-backdrop" onMouseDown={onClose}>
      <section
        className="kg-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="kg-create-node-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="kg-modal-heading">
          <div>
            <span className="kg-eyebrow">KNOWLEDGE GRAPH</span>
            <h2 id="kg-create-node-title">Create entity</h2>
          </div>
          <button className="kg-icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={submit} className="kg-form">
          <label>
            Entity name *
            <input
              required
              maxLength={500}
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Data Protection Regulation"
            />
          </label>

          <label>
            Entity type *
            <select
              value={nodeType}
              onChange={(event) => setNodeType(event.target.value as NodeType)}
            >
              {NODE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {NODE_LABELS[type]}
                </option>
              ))}
            </select>
          </label>

          <label>
            Description
            <textarea
              rows={3}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Describe this entity..."
            />
          </label>

          <div className="kg-form-grid">
            <label>
              Jurisdiction
              <input
                value={jurisdiction}
                onChange={(event) => setJurisdiction(event.target.value)}
                placeholder="e.g. India"
              />
            </label>

            <label>
              External identifier
              <input
                value={externalIdentifier}
                onChange={(event) => setExternalIdentifier(event.target.value)}
                placeholder="Optional reference"
              />
            </label>
          </div>

          <label>
            Confidence (0–1)
            <input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={confidence}
              onChange={(event) => setConfidence(event.target.value)}
              placeholder="Optional"
            />
          </label>

          {error && <div className="kg-error">{error}</div>}

          <div className="kg-modal-actions">
            <button type="button" className="kg-button secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="kg-button primary" disabled={saving}>
              {saving ? <LoaderCircle className="spin" size={16} /> : <Plus size={16} />}
              Create entity
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function RelationshipForm({
  nodes,
  defaultSource,
  onClose,
  onCreated
}: {
  nodes: GraphNode[];
  defaultSource: string;
  onClose: () => void;
  onCreated: (edge: GraphEdge) => void;
}) {
  const [sourceId, setSourceId] = useState(defaultSource);
  const [targetId, setTargetId] = useState("");
  const [relation, setRelation] = useState<RelationType>("related_to");
  const [description, setDescription] = useState("");
  const [confidence, setConfidence] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!sourceId || !targetId || sourceId === targetId) {
      setError("Choose two different entities.");
      return;
    }

    setSaving(true);

    try {
      const edge = await knowledgeGraphApi.createEdge({
        source_node_id: sourceId,
        target_node_id: targetId,
        relation_type: relation,
        description: description.trim() || null,
        confidence: confidence === "" ? null : Number(confidence),
        properties: {}
      });

      onCreated(edge);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="kg-modal-backdrop" onMouseDown={onClose}>
      <section
        className="kg-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="kg-create-edge-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="kg-modal-heading">
          <div>
            <span className="kg-eyebrow">KNOWLEDGE GRAPH</span>
            <h2 id="kg-create-edge-title">Create relationship</h2>
          </div>
          <button className="kg-icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={submit} className="kg-form">
          <label>
            Source entity *
            <select value={sourceId} onChange={(event) => setSourceId(event.target.value)}>
              <option value="">Select source</option>
              {nodes.map((node) => (
                <option key={node.id} value={node.id}>{node.name}</option>
              ))}
            </select>
          </label>

          <label>
            Relationship *
            <select
              value={relation}
              onChange={(event) => setRelation(event.target.value as RelationType)}
            >
              {RELATION_TYPES.map((type) => (
                <option key={type} value={type}>
                  {RELATION_LABELS[type]}
                </option>
              ))}
            </select>
          </label>

          <label>
            Target entity *
            <select value={targetId} onChange={(event) => setTargetId(event.target.value)}>
              <option value="">Select target</option>
              {nodes.filter((node) => node.id !== sourceId).map((node) => (
                <option key={node.id} value={node.id}>{node.name}</option>
              ))}
            </select>
          </label>

          <label>
            Description
            <textarea
              rows={2}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Optional relationship context"
            />
          </label>

          <label>
            Confidence (0–1)
            <input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={confidence}
              onChange={(event) => setConfidence(event.target.value)}
              placeholder="Optional"
            />
          </label>

          {error && <div className="kg-error">{error}</div>}

          <div className="kg-modal-actions">
            <button type="button" className="kg-button secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="kg-button primary" disabled={saving}>
              {saving ? <LoaderCircle className="spin" size={16} /> : <GitBranch size={16} />}
              Create relationship
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function EvidenceForm({
  node,
  onClose,
  onCreated
}: {
  node: GraphNode;
  onClose: () => void;
  onCreated: (evidence: GraphEvidence) => void;
}) {
  const [documentId, setDocumentId] = useState("");
  const [versionId, setVersionId] = useState("");
  const [chunkId, setChunkId] = useState("");
  const [pageNumber, setPageNumber] = useState("");
  const [quote, setQuote] = useState("");
  const [role, setRole] = useState<"supports" | "contradicts" | "contextualizes">("supports");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      const evidence = await knowledgeGraphApi.addEvidence({
        node_id: node.id,
        document_id: documentId.trim(),
        version_id: versionId.trim(),
        chunk_id: chunkId.trim() || null,
        page_number: pageNumber ? Number(pageNumber) : null,
        quote: quote.trim(),
        evidence_role: role,
        metadata_json: {}
      });

      onCreated(evidence);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="kg-modal-backdrop" onMouseDown={onClose}>
      <section
        className="kg-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="kg-evidence-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="kg-modal-heading">
          <div>
            <span className="kg-eyebrow">SOURCE TRACEABILITY</span>
            <h2 id="kg-evidence-title">Attach evidence</h2>
            <p className="kg-modal-subtitle">{node.name}</p>
          </div>
          <button className="kg-icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={submit} className="kg-form">
          <div className="kg-notice">
            Enter the existing document and version IDs from this organization.
            The backend validates that they belong to the same document and tenant.
          </div>

          <label>
            Document ID *
            <input required value={documentId} onChange={(event) => setDocumentId(event.target.value)} />
          </label>

          <label>
            Document version ID *
            <input required value={versionId} onChange={(event) => setVersionId(event.target.value)} />
          </label>

          <label>
            Chunk ID
            <input value={chunkId} onChange={(event) => setChunkId(event.target.value)} />
          </label>

          <label>
            Page number
            <input
              type="number"
              min="1"
              value={pageNumber}
              onChange={(event) => setPageNumber(event.target.value)}
            />
          </label>

          <label>
            Evidence role *
            <select value={role} onChange={(event) => setRole(event.target.value as typeof role)}>
              <option value="supports">Supports</option>
              <option value="contradicts">Contradicts</option>
              <option value="contextualizes">Contextualizes</option>
            </select>
          </label>

          <label>
            Extracted quote *
            <textarea
              required
              minLength={1}
              maxLength={12000}
              rows={4}
              value={quote}
              onChange={(event) => setQuote(event.target.value)}
              placeholder="Paste the exact supporting or contradicting passage..."
            />
          </label>

          {error && <div className="kg-error">{error}</div>}

          <div className="kg-modal-actions">
            <button type="button" className="kg-button secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="kg-button primary" disabled={saving}>
              {saving ? <LoaderCircle className="spin" size={16} /> : <FileText size={16} />}
              Attach evidence
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export function KnowledgeGraphPage() {
  const [query, setQuery] = useState("");
  const [nodeType, setNodeType] = useState<NodeType | "">("");
  const [results, setResults] = useState<GraphNode[]>([]);
  const [total, setTotal] = useState(0);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [rootId, setRootId] = useState<string | null>(null);
  const [depth, setDepth] = useState(2);
  const [includeUnverified, setIncludeUnverified] = useState(true);
  const [evidence, setEvidence] = useState<GraphEvidence[]>([]);
  const [tab, setTab] = useState<Tab>("overview");
  const [showNodeForm, setShowNodeForm] = useState(false);
  const [showEdgeForm, setShowEdgeForm] = useState(false);
  const [showEvidenceForm, setShowEvidenceForm] = useState(false);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadSearch = useCallback(async () => {
    setLoadingSearch(true);
    setError("");

    try {
      const response = await knowledgeGraphApi.searchNodes({
        q: query.trim() || undefined,
        node_type: nodeType || undefined,
        limit: 100,
        offset: 0
      });

      setResults(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingSearch(false);
    }
  }, [query, nodeType]);

  useEffect(() => {
    void loadSearch();
  }, [loadSearch]);

  const loadNeighborhood = useCallback(async (
    node: GraphNode,
    selectedDepth = depth,
    showUnverified = includeUnverified
  ) => {
    setLoadingGraph(true);
    setError("");
    setNotice("");

    try {
      const graph = await knowledgeGraphApi.getNeighborhood(
        node.id,
        selectedDepth,
        showUnverified
      );

      setNodes(graph.nodes);
      setEdges(graph.edges);
      setRootId(graph.root.id);
      setSelectedNode(graph.root);
      setTab("overview");
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingGraph(false);
    }
  }, [depth, includeUnverified]);

  const loadEvidence = useCallback(async (nodeId: string) => {
    setLoadingEvidence(true);

    try {
      const records = await knowledgeGraphApi.getNodeEvidence(nodeId);
      setEvidence(records);
    } catch (err) {
      setEvidence([]);
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingEvidence(false);
    }
  }, []);

  useEffect(() => {
    if (selectedNode && tab === "evidence") {
      void loadEvidence(selectedNode.id);
    }
  }, [selectedNode, tab, loadEvidence]);

  async function updateNodeVerification(status: VerificationStatus) {
    if (!selectedNode) return;

    setActionLoading(true);
    setError("");
    setNotice("");

    try {
      const updated = await knowledgeGraphApi.verifyNode(
        selectedNode.id,
        status
      );

      setSelectedNode(updated);
      setNodes((current) =>
        current.map((node) => node.id === updated.id ? updated : node)
      );

      setNotice(`Entity verification updated to ${titleCase(status)}.`);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  }

  async function updateEdgeVerification(
    edge: GraphEdge,
    status: VerificationStatus
  ) {
    setActionLoading(true);
    setError("");
    setNotice("");

    try {
      const updated = await knowledgeGraphApi.verifyEdge(edge.id, status);

      setEdges((current) =>
        current.map((item) => item.id === updated.id ? updated : item)
      );

      setNotice(`Relationship verification updated to ${titleCase(status)}.`);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  }

  function handleNodeCreated(node: GraphNode) {
    setShowNodeForm(false);
    setNotice(`Entity "${node.name}" created or already existed.`);
    void loadSearch();
    void loadNeighborhood(node);
  }

  function handleEdgeCreated(edge: GraphEdge) {
    setShowEdgeForm(false);
    setNotice("Relationship created or already existed.");

    setEdges((current) => {
      if (current.some((item) => item.id === edge.id)) return current;
      return [...current, edge];
    });

    void loadSearch();
  }

  function handleEvidenceCreated(record: GraphEvidence) {
    setShowEvidenceForm(false);
    setEvidence((current) => [record, ...current]);
    setTab("evidence");
    setNotice("Evidence attached successfully.");
  }

  const verifiedNodeCount = nodes.filter(
    (node) => node.verification_status === "verified"
  ).length;

  const verifiedEdgeCount = edges.filter(
    (edge) => edge.verification_status === "verified"
  ).length;

  const selectedNodeEdges = useMemo(() => {
    if (!selectedNode) return [];

    return edges.filter(
      (edge) =>
        edge.source_node_id === selectedNode.id ||
        edge.target_node_id === selectedNode.id
    );
  }, [edges, selectedNode]);

  return (
    <div className="kg-page">
      <PageHeader
        eyebrow="INTELLIGENCE GRAPH"
        title="Knowledge Graph Explorer"
        description="Explore enterprise entities, their relationships, and the evidence supporting them."
      />

      <div className="kg-toolbar">
        <div className="kg-search-box">
          <Search size={17} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void loadSearch();
            }}
            placeholder="Search entities, identifiers, or descriptions..."
            aria-label="Search graph entities"
          />
          {query && (
            <button
              className="kg-clear-search"
              onClick={() => setQuery("")}
              aria-label="Clear search"
            >
              <X size={15} />
            </button>
          )}
        </div>

        <div className="kg-select-wrap">
          <Filter size={15} />
          <select
            value={nodeType}
            onChange={(event) => setNodeType(event.target.value as NodeType | "")}
            aria-label="Filter by entity type"
          >
            <option value="">All entity types</option>
            {NODE_TYPES.map((type) => (
              <option key={type} value={type}>{NODE_LABELS[type]}</option>
            ))}
          </select>
          <ChevronDown size={14} />
        </div>

        <button
          className="kg-button primary"
          onClick={() => setShowNodeForm(true)}
        >
          <Plus size={16} />
          New entity
        </button>
      </div>

      {error && (
        <div className="kg-alert error">
          <AlertCircle size={17} />
          <span>{error}</span>
          <button onClick={() => setError("")} aria-label="Dismiss error">
            <X size={15} />
          </button>
        </div>
      )}

      {notice && (
        <div className="kg-alert success">
          <Check size={17} />
          <span>{notice}</span>
          <button onClick={() => setNotice("")} aria-label="Dismiss message">
            <X size={15} />
          </button>
        </div>
      )}

      <div className="kg-metrics">
        <div className="kg-metric-card">
          <div className="kg-metric-icon blue"><Network size={18} /></div>
          <div>
            <strong>{total.toLocaleString()}</strong>
            <span>Matching entities</span>
          </div>
        </div>
        <div className="kg-metric-card">
          <div className="kg-metric-icon purple"><GitBranch size={18} /></div>
          <div>
            <strong>{nodes.length}</strong>
            <span>Loaded graph nodes</span>
          </div>
        </div>
        <div className="kg-metric-card">
          <div className="kg-metric-icon green"><ShieldCheck size={18} /></div>
          <div>
            <strong>{verifiedNodeCount + verifiedEdgeCount}</strong>
            <span>Verified graph records</span>
          </div>
        </div>
        <div className="kg-metric-card">
          <div className="kg-metric-icon amber"><Activity size={18} /></div>
          <div>
            <strong>{edges.length}</strong>
            <span>Loaded relationships</span>
          </div>
        </div>
      </div>

      <div className="kg-workspace">
        <aside className="kg-entity-sidebar">
          <div className="kg-panel-heading">
            <div>
              <h2>Entities</h2>
              <p>{results.length} shown of {total}</p>
            </div>
            <button
              className="kg-icon-button"
              onClick={() => void loadSearch()}
              aria-label="Refresh entities"
              disabled={loadingSearch}
            >
              {loadingSearch
                ? <LoaderCircle className="spin" size={16} />
                : <RefreshCw size={16} />}
            </button>
          </div>

          <div className="kg-entity-list">
            {loadingSearch ? (
              <div className="kg-list-state">
                <LoaderCircle className="spin" size={22} />
                <span>Searching entities...</span>
              </div>
            ) : results.length === 0 ? (
              <div className="kg-list-state">
                <Layers3 size={25} />
                <strong>No entities found</strong>
                <span>Try another search or create a new entity.</span>
              </div>
            ) : (
              results.map((node) => (
                <button
                  key={node.id}
                  className={`kg-entity-item ${selectedNode?.id === node.id ? "active" : ""}`}
                  onClick={() => void loadNeighborhood(node)}
                >
                  <span
                    className="kg-entity-symbol"
                    style={{ background: NODE_COLORS[node.node_type] }}
                  >
                    <CircleDot size={15} />
                  </span>
                  <span className="kg-entity-copy">
                    <strong>{node.name}</strong>
                    <small>
                      {NODE_LABELS[node.node_type]} · {titleCase(node.verification_status)}
                    </small>
                  </span>
                  <ChevronDown size={14} className="kg-entity-arrow" />
                </button>
              ))
            )}
          </div>
        </aside>

        <main className="kg-graph-panel">
          <div className="kg-panel-heading kg-graph-heading">
            <div>
              <h2>Relationship map</h2>
              <p>
                {rootId
                  ? `Root: ${selectedNode?.name ?? "Selected entity"}`
                  : "Select an entity to load its connected graph"}
              </p>
            </div>

            <div className="kg-graph-controls">
              <label className="kg-inline-select">
                Depth
                <select
                  value={depth}
                  onChange={(event) => {
                    const value = Number(event.target.value);
                    setDepth(value);
                    if (selectedNode) {
                      void loadNeighborhood(selectedNode, value, includeUnverified);
                    }
                  }}
                >
                  <option value={1}>1 level</option>
                  <option value={2}>2 levels</option>
                  <option value={3}>3 levels</option>
                </select>
              </label>

              <label className="kg-check-label">
                <input
                  type="checkbox"
                  checked={includeUnverified}
                  onChange={(event) => {
                    const value = event.target.checked;
                    setIncludeUnverified(value);
                    if (selectedNode) {
                      void loadNeighborhood(selectedNode, depth, value);
                    }
                  }}
                />
                Include unverified
              </label>

              <button
                className="kg-icon-button"
                disabled={!selectedNode || loadingGraph}
                onClick={() => selectedNode && void loadNeighborhood(selectedNode)}
                aria-label="Reload graph"
              >
                {loadingGraph
                  ? <LoaderCircle className="spin" size={16} />
                  : <RefreshCw size={16} />}
              </button>
            </div>
          </div>

          {loadingGraph && (
            <div className="kg-loading-overlay">
              <LoaderCircle className="spin" size={25} />
              Loading neighborhood...
            </div>
          )}

          <GraphCanvas
            nodes={nodes}
            edges={edges}
            selectedId={selectedNode?.id ?? null}
            rootId={rootId}
            onSelect={setSelectedNode}
          />

          <div className="kg-graph-footer">
            <div className="kg-legend">
              <span><i className="verified" /> Verified</span>
              <span><i className="unverified" /> Unverified / reviewed</span>
              <span><i className="rejected" /> Rejected</span>
            </div>
            <span className="kg-graph-count">
              {nodes.length} nodes · {edges.length} relationships
            </span>
          </div>
        </main>
      </div>

      <section className="kg-detail-panel">
        <div className="kg-detail-header">
          <div>
            <span className="kg-eyebrow">ENTITY WORKSPACE</span>
            <h2>{selectedNode?.name ?? "Entity details"}</h2>
            <p>
              {selectedNode
                ? `${NODE_LABELS[selectedNode.node_type]} · Created ${formatDate(selectedNode.created_at)}`
                : "Select an entity from the list or graph to inspect its details."}
            </p>
          </div>

          {selectedNode && (
            <div className="kg-detail-actions">
              <button
                className="kg-button secondary"
                onClick={() => setShowEvidenceForm(true)}
              >
                <FileText size={15} />
                Add evidence
              </button>
              <button
                className="kg-button secondary"
                onClick={() => setShowEdgeForm(true)}
                disabled={results.length < 2}
              >
                <GitBranch size={15} />
                Add relationship
              </button>
            </div>
          )}
        </div>

        {selectedNode ? (
          <>
            <div className="kg-tabs">
              <button
                className={tab === "overview" ? "active" : ""}
                onClick={() => setTab("overview")}
              >
                Overview
              </button>
              <button
                className={tab === "evidence" ? "active" : ""}
                onClick={() => setTab("evidence")}
              >
                Evidence
                <span>{evidence.length}</span>
              </button>
            </div>

            {tab === "overview" ? (
              <div className="kg-detail-content">
                <div className="kg-detail-main">
                  <div className="kg-detail-grid">
                    <div className="kg-detail-field">
                      <span>Entity type</span>
                      <strong>{NODE_LABELS[selectedNode.node_type]}</strong>
                    </div>
                    <div className="kg-detail-field">
                      <span>Verification</span>
                      <VerificationPill status={selectedNode.verification_status} />
                    </div>
                    <div className="kg-detail-field">
                      <span>Jurisdiction</span>
                      <strong>{selectedNode.jurisdiction || "Not specified"}</strong>
                    </div>
                    <div className="kg-detail-field">
                      <span>Confidence</span>
                      <strong>
                        {selectedNode.confidence == null
                          ? "Not provided"
                          : `${(selectedNode.confidence * 100).toFixed(0)}%`}
                      </strong>
                    </div>
                    <div className="kg-detail-field">
                      <span>External identifier</span>
                      <strong>{selectedNode.external_identifier || "—"}</strong>
                    </div>
                    <div className="kg-detail-field">
                      <span>Canonical key</span>
                      <strong className="kg-mono">{selectedNode.canonical_key}</strong>
                    </div>
                  </div>

                  <div className="kg-description-block">
                    <h3>Description</h3>
                    <p>{selectedNode.description || "No description has been added."}</p>
                  </div>

                  {selectedNode.aliases.length > 0 && (
                    <div className="kg-description-block">
                      <h3>Aliases</h3>
                      <div className="kg-chip-list">
                        {selectedNode.aliases.map((alias) => (
                          <span key={alias}>{alias}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="kg-description-block">
                    <h3>Properties</h3>
                    <pre className="kg-json">
                      {JSON.stringify(selectedNode.properties, null, 2)}
                    </pre>
                  </div>
                </div>

                <aside className="kg-review-card">
                  <div className="kg-review-icon"><ShieldCheck size={19} /></div>
                  <h3>Verification workflow</h3>
                  <p>
                    Verification is a human review state. It does not independently
                    establish legal applicability or compliance.
                  </p>
                  <div className="kg-current-status">
                    <span>Current status</span>
                    <VerificationPill status={selectedNode.verification_status} />
                  </div>

                  <div className="kg-review-buttons">
                    <button
                      disabled={actionLoading}
                      onClick={() => void updateNodeVerification("verified")}
                    >
                      <Check size={14} /> Verify
                    </button>
                    <button
                      disabled={actionLoading}
                      onClick={() => void updateNodeVerification("reviewed")}
                    >
                      Mark reviewed
                    </button>
                    <button
                      disabled={actionLoading}
                      onClick={() => void updateNodeVerification("rejected")}
                    >
                      Reject
                    </button>
                    <button
                      disabled={actionLoading}
                      onClick={() => void updateNodeVerification("unverified")}
                    >
                      Reset
                    </button>
                  </div>
                </aside>
              </div>
            ) : (
              <div className="kg-evidence-section">
                <div className="kg-evidence-heading">
                  <div>
                    <h3>Source evidence</h3>
                    <p>Evidence records linked to this entity.</p>
                  </div>
                  <button
                    className="kg-button primary"
                    onClick={() => setShowEvidenceForm(true)}
                  >
                    <Plus size={15} /> Add evidence
                  </button>
                </div>

                {loadingEvidence ? (
                  <div className="kg-list-state">
                    <LoaderCircle className="spin" size={22} />
                    Loading evidence...
                  </div>
                ) : evidence.length === 0 ? (
                  <div className="kg-list-state kg-evidence-empty">
                    <FileText size={27} />
                    <strong>No evidence attached</strong>
                    <span>Attach a document passage to improve traceability.</span>
                  </div>
                ) : (
                  <div className="kg-evidence-list">
                    {evidence.map((item) => (
                      <article className="kg-evidence-card" key={item.id}>
                        <div className="kg-evidence-card-top">
                          <span className={`kg-evidence-role ${item.evidence_role}`}>
                            {titleCase(item.evidence_role)}
                          </span>
                          <span>{formatDate(item.created_at)}</span>
                        </div>
                        <blockquote>{item.quote}</blockquote>
                        <div className="kg-evidence-meta">
                          <span>Document: <code>{item.document_id}</code></span>
                          <span>Version: <code>{item.version_id}</code></span>
                          {item.page_number && <span>Page {item.page_number}</span>}
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="kg-relationships-section">
              <div className="kg-section-title">
                <div>
                  <h3>Connected relationships</h3>
                  <p>Relationships currently loaded around this entity.</p>
                </div>
                <span>{selectedNodeEdges.length} relationships</span>
              </div>

              {selectedNodeEdges.length === 0 ? (
                <p className="kg-muted">No connected relationships in the loaded neighborhood.</p>
              ) : (
                <div className="kg-relationship-list">
                  {selectedNodeEdges.map((edge) => {
                    const isSource = edge.source_node_id === selectedNode.id;
                    const otherId = isSource ? edge.target_node_id : edge.source_node_id;
                    const otherNode = nodes.find((node) => node.id === otherId);

                    return (
                      <article className="kg-relationship-row" key={edge.id}>
                        <div className="kg-relationship-names">
                          <strong>{isSource ? selectedNode.name : otherNode?.name ?? "Unknown entity"}</strong>
                          <ArrowDownUp size={14} />
                          <strong>{isSource ? otherNode?.name ?? "Unknown entity" : selectedNode.name}</strong>
                        </div>
                        <span className="kg-relation-type">
                          {RELATION_LABELS[edge.relation_type]}
                        </span>
                        <VerificationPill status={edge.verification_status} />
                        <div className="kg-edge-actions">
                          <button
                            disabled={actionLoading}
                            onClick={() => void updateEdgeVerification(edge, "verified")}
                          >
                            Verify
                          </button>
                          <button
                            disabled={actionLoading}
                            onClick={() => void updateEdgeVerification(edge, "rejected")}
                          >
                            Reject
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="kg-detail-empty">
            <Network size={28} />
            <strong>No entity selected</strong>
            <span>Select an entity to inspect its metadata, evidence, and relationships.</span>
          </div>
        )}
      </section>

      {showNodeForm && (
        <NodeCreationForm
          onClose={() => setShowNodeForm(false)}
          onCreated={handleNodeCreated}
        />
      )}

      {showEdgeForm && (
        <RelationshipForm
          nodes={results}
          defaultSource={selectedNode?.id ?? ""}
          onClose={() => setShowEdgeForm(false)}
          onCreated={handleEdgeCreated}
        />
      )}

      {showEvidenceForm && selectedNode && (
        <EvidenceForm
          node={selectedNode}
          onClose={() => setShowEvidenceForm(false)}
          onCreated={handleEvidenceCreated}
        />
      )}
    </div>
  );
}

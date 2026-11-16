
import { useState, type FormEvent } from "react";
import {
  Bot,
  Send,
  LoaderCircle,
  FileText,
  Sparkles,
  AlertTriangle,
  BookOpen,
  RotateCcw
} from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import {
  askResearchAssistant,
  type RAGResponse
} from "../../lib/intelligence-api";
import { getApiErrorMessage } from "../../lib/api";

export function ResearchPage() {
  const [question, setQuestion] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [useReranker, setUseReranker] = useState(true);

  const [response, setResponse] = useState<RAGResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedQuestion = question.trim();

    if (normalizedQuestion.length < 5) {
      setError("Please enter a question containing at least 5 characters.");
      return;
    }

    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const result = await askResearchAssistant({
        question: normalizedQuestion,
        top_k: 8,
        candidate_limit: 40,
        document_id: documentId.trim() || undefined,
        use_reranker: useReranker
      });

      setResponse(result);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function resetResearch() {
    setQuestion("");
    setDocumentId("");
    setResponse(null);
    setError("");
  }

  return (
    <div className="intelligence-page">
      <PageHeader
        eyebrow="GENERATIVE INTELLIGENCE"
        title="AI Research Assistant"
        description="Ask questions about your indexed documents and receive answers grounded in retrieved evidence."
      />

      <div className="research-layout">
        <main className="research-main">
          {!response && !loading && (
            <div className="research-welcome">
              <div className="research-avatar">
                <Bot size={28} />
              </div>

              <div className="research-welcome-copy">
                <span className="results-kicker">
                  EVIDENCE-GROUNDED RESEARCH
                </span>
                <h2>What would you like to investigate?</h2>
                <p>
                  Ask a question about your organization's indexed
                  documents. The assistant retrieves relevant passages,
                  generates structured findings and validates evidence
                  references before returning the answer.
                </p>
              </div>

              <div className="suggestion-list">
                {[
                  "What are the key obligations described in the documents?",
                  "Identify the major risks and their supporting evidence.",
                  "Summarize the important policy requirements."
                ].map((suggestion) => (
                  <button
                    type="button"
                    className="suggestion-chip"
                    key={suggestion}
                    onClick={() => setQuestion(suggestion)}
                  >
                    <Sparkles size={15} />
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="intelligence-loading research-loading">
              <LoaderCircle className="spin" size={30} />
              <strong>Researching your question</strong>
              <span>
                Retrieving passages, preparing evidence context and
                validating the generated findings.
              </span>
            </div>
          )}

          {error && (
            <div className="intelligence-alert error-alert" role="alert">
              <AlertTriangle size={18} />
              <div>
                <strong>Unable to complete research</strong>
                <span>{error}</span>
              </div>
            </div>
          )}

          {response && (
            <div className="research-response">
              <div className="research-response-header">
                <div>
                  <div className="results-kicker">RESEARCH RESULT</div>
                  <h2>Research response</h2>
                  <p>{response.question}</p>
                </div>

                <StatusBadge
                  status={
                    response.insufficient_evidence
                      ? "warning"
                      : "success"
                  }
                >
                  {response.insufficient_evidence
                    ? "Insufficient evidence"
                    : "Evidence returned"}
                </StatusBadge>
              </div>

              <section className="answer-panel">
                <div className="answer-panel-heading">
                  <div className="answer-icon">
                    <Bot size={19} />
                  </div>
                  <div>
                    <h3>Answer</h3>
                    <span>Generated from retrieved document evidence</span>
                  </div>
                </div>

                <div className="answer-text">
                  {response.answer}
                </div>
              </section>

              {response.findings.length > 0 && (
                <section className="research-section">
                  <div className="research-section-heading">
                    <div>
                      <h3>Structured findings</h3>
                      <p>
                        Findings returned by the backend with their
                        evidence identifiers.
                      </p>
                    </div>
                    <span className="section-count">
                      {response.findings.length}
                    </span>
                  </div>

                  <div className="finding-list">
                    {response.findings.map((finding, index) => (
                      <article className="finding-card" key={index}>
                        <div className="finding-number">
                          {index + 1}
                        </div>

                        <div className="finding-body">
                          <p>{finding.text}</p>

                          <div className="finding-evidence-ids">
                            {finding.evidence_ids.map((id) => (
                              <span key={id}>{id}</span>
                            ))}
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              )}

              <section className="research-section">
                <div className="research-section-heading">
                  <div>
                    <h3>Source citations</h3>
                    <p>
                      Retrieved passages referenced by the findings.
                    </p>
                  </div>
                  <span className="section-count">
                    {response.citations.length}
                  </span>
                </div>

                {response.citations.length === 0 ? (
                  <div className="citation-empty">
                    No validated citations were returned for this response.
                  </div>
                ) : (
                  <div className="citation-list">
                    {response.citations.map((citation) => (
                      <article
                        className="citation-card"
                        key={citation.evidence_id}
                      >
                        <div className="citation-top">
                          <span className="citation-id">
                            {citation.evidence_id}
                          </span>

                          <a
                            href={`/documents/${citation.document_id}`}
                            className="citation-open"
                          >
                            <FileText size={15} />
                            Open document
                          </a>
                        </div>

                        <h4>{citation.document_title}</h4>

                        <div className="citation-meta">
                          Version {citation.version_number}
                          {" · "}
                          Pages {citation.page_start}–
                          {citation.page_end}
                        </div>

                        <blockquote>
                          {citation.quoted_text}
                        </blockquote>
                      </article>
                    ))}
                  </div>
                )}
              </section>

              {response.limitations.length > 0 && (
                <section className="limitations-panel">
                  <div className="limitations-heading">
                    <AlertTriangle size={17} />
                    <strong>Research limitations</strong>
                  </div>

                  <ul>
                    {response.limitations.map((limitation, index) => (
                      <li key={index}>{limitation}</li>
                    ))}
                  </ul>
                </section>
              )}

              <div className="research-provenance">
                <span>
                  <BookOpen size={14} />
                  Retrieved passages: {response.retrieval_count}
                </span>
                <span>Model: {response.model}</span>
              </div>

              <button
                type="button"
                className="secondary-button research-reset"
                onClick={resetResearch}
              >
                <RotateCcw size={15} />
                Start new research
              </button>
            </div>
          )}
        </main>

        <aside className="research-sidebar">
          <div className="research-settings-card">
            <div className="settings-card-title">
              <Sparkles size={17} />
              Research settings
            </div>

            <label className="research-filter">
              <span>Restrict to document ID</span>
              <input
                value={documentId}
                onChange={(event) => setDocumentId(event.target.value)}
                placeholder="Optional document UUID"
              />
            </label>

            <label className="toggle-field research-toggle">
              <input
                type="checkbox"
                checked={useReranker}
                onChange={(event) =>
                  setUseReranker(event.target.checked)
                }
              />
              <span>Use evidence reranking</span>
            </label>

            <div className="research-setting-info">
              <strong>Retrieval configuration</strong>
              <div>Evidence passages: 8</div>
              <div>Candidate passages: 40</div>
              <div>Maximum question length: 4,000 characters</div>
            </div>
          </div>

          <div className="research-note-card">
            <div className="research-note-icon">
              <BookOpen size={18} />
            </div>
            <strong>Evidence-first responses</strong>
            <p>
              Answers are based on accessible indexed documents.
              Review source passages and limitations before relying
              on a finding.
            </p>
          </div>
        </aside>
      </div>

      <form className="research-composer" onSubmit={submitQuestion}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about your organization's documents..."
          aria-label="Research question"
          rows={2}
          maxLength={4000}
          disabled={loading}
        />

        <div className="composer-footer">
          <span>
            {question.length.toLocaleString()} / 4,000 characters
          </span>

          <button
            type="submit"
            className="primary-button"
            disabled={loading || question.trim().length < 5}
          >
            {loading ? (
              <LoaderCircle className="spin" size={17} />
            ) : (
              <Send size={16} />
            )}
            <span>{loading ? "Researching..." : "Ask assistant"}</span>
          </button>
        </div>
      </form>
    </div>
  );
}

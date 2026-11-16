
import { useState, type FormEvent } from "react";
import {
  Search,
  SlidersHorizontal,
  FileText,
  ArrowUpRight,
  LoaderCircle,
  RefreshCw
} from "lucide-react";

import { PageHeader } from "../../components/ui/PageHeader";
import { StatusBadge } from "../../components/ui/StatusBadge";
import {
  searchDocuments,
  type SearchResponse
} from "../../lib/intelligence-api";
import { getApiErrorMessage } from "../../lib/api";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [useReranker, setUseReranker] = useState(true);

  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedQuery = query.trim();

    if (normalizedQuery.length < 2) {
      setError("Enter at least 2 characters to search.");
      return;
    }

    setLoading(true);
    setError("");
    setResults(null);

    try {
      const response = await searchDocuments({
        query: normalizedQuery,
        top_k: 10,
        candidate_limit: 40,
        document_id: documentId.trim() || undefined,
        use_reranker: useReranker
      });

      setResults(response);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function resetSearch() {
    setQuery("");
    setDocumentId("");
    setResults(null);
    setError("");
  }

  return (
    <div className="intelligence-page">
      <PageHeader
        eyebrow="DOCUMENT INTELLIGENCE"
        title="Intelligent Search"
        description="Find relevant evidence across your organization's indexed documents using hybrid retrieval and reranking."
      />

      <section className="search-workspace">
        <form className="search-form" onSubmit={handleSearch}>
          <div className="search-input-wrap">
            <Search size={21} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search documents, policies, regulations or evidence..."
              aria-label="Search query"
              maxLength={4000}
            />

            <button
              type="submit"
              className="primary-button"
              disabled={loading || query.trim().length < 2}
            >
              {loading ? (
                <LoaderCircle className="spin" size={17} />
              ) : (
                <Search size={17} />
              )}
              <span>{loading ? "Searching..." : "Search"}</span>
            </button>
          </div>

          <div className="search-options">
            <div className="search-option-title">
              <SlidersHorizontal size={15} />
              Search options
            </div>

            <label className="filter-field">
              <span>Restrict to document ID (optional)</span>
              <input
                value={documentId}
                onChange={(event) => setDocumentId(event.target.value)}
                placeholder="Paste document UUID"
              />
            </label>

            <label className="toggle-field">
              <input
                type="checkbox"
                checked={useReranker}
                onChange={(event) =>
                  setUseReranker(event.target.checked)
                }
              />
              <span>Enable cross-encoder reranking</span>
            </label>
          </div>
        </form>

        {error && (
          <div className="intelligence-alert error-alert" role="alert">
            <strong>Search failed</strong>
            <span>{error}</span>
          </div>
        )}

        {loading && (
          <div className="intelligence-loading">
            <LoaderCircle className="spin" size={26} />
            <strong>Searching indexed evidence</strong>
            <span>
              Retrieving relevant passages and ranking the results.
            </span>
          </div>
        )}

        {!loading && !results && !error && (
          <div className="intelligence-empty">
            <div className="intelligence-empty-icon">
              <Search size={25} />
            </div>
            <h3>Search your intelligence library</h3>
            <p>
              Enter a question, concept, policy name or phrase.
              Relevant indexed passages will appear here.
            </p>
          </div>
        )}

        {!loading && results && (
          <section className="search-results-section">
            <div className="results-heading">
              <div>
                <div className="results-kicker">SEARCH RESULTS</div>
                <h2>
                  {results.total_results} relevant{" "}
                  {results.total_results === 1 ? "passage" : "passages"}
                </h2>
                <p>
                  Results for: <strong>{results.query}</strong>
                </p>
              </div>

              <div className="results-actions">
                <StatusBadge
                  status={results.reranking_enabled ? "success" : "neutral"}
                >
                  {results.reranking_enabled
                    ? "Reranking active"
                    : "Reranking inactive"}
                </StatusBadge>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={resetSearch}
                >
                  <RefreshCw size={15} />
                  Clear
                </button>
              </div>
            </div>

            {results.results.length === 0 ? (
              <div className="intelligence-empty compact-empty">
                <FileText size={25} />
                <h3>No matching passages found</h3>
                <p>
                  Try a broader phrase or remove the document ID filter.
                  Only indexed documents accessible to your organization
                  are searched.
                </p>
              </div>
            ) : (
              <div className="evidence-list">
                {results.results.map((item, index) => (
                  <article
                    className="evidence-card"
                    key={item.chunk_id}
                  >
                    <div className="evidence-card-top">
                      <div className="evidence-rank">
                        <span>{String(index + 1).padStart(2, "0")}</span>
                        <span>RANK</span>
                      </div>

                      <div className="evidence-document">
                        <div className="evidence-document-icon">
                          <FileText size={18} />
                        </div>

                        <div>
                          <h3>{item.document_title}</h3>
                          <p>
                            Version {item.version_number}
                            {" · "}
                            Pages {item.page_start}–{item.page_end}
                          </p>
                        </div>
                      </div>

                      <a
                        className="evidence-open-link"
                        href={`/documents/${item.document_id}`}
                        title="Open document"
                      >
                        <ArrowUpRight size={17} />
                      </a>
                    </div>

                    <div className="evidence-content">
                      {item.content}
                    </div>

                    <div className="evidence-metadata">
                      <span>
                        <strong>Chunk:</strong>{" "}
                        {item.chunk_index}
                      </span>

                      {item.semantic_rank !== null && (
                        <span>
                          <strong>Semantic rank:</strong>{" "}
                          {item.semantic_rank}
                        </span>
                      )}

                      {item.keyword_rank !== null && (
                        <span>
                          <strong>Keyword rank:</strong>{" "}
                          {item.keyword_rank}
                        </span>
                      )}

                      <span>
                        <strong>RRF score:</strong>{" "}
                        {item.rrf_score.toFixed(5)}
                      </span>

                      {item.rerank_score !== null && (
                        <span>
                          <strong>Rerank score:</strong>{" "}
                          {item.rerank_score.toFixed(4)}
                        </span>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
      </section>
    </div>
  );
}

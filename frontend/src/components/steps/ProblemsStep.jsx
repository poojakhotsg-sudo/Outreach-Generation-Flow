import React, { useMemo, useState } from 'react';

const GOOGLE_RATING_THRESHOLD = 4.5;

/**
 * Builds a Google rating problem card from research data.
 * Returns null if no Google data is present or rating is above threshold.
 */
function buildGoogleProblemCard(researchData) {
  const rating = researchData?.google_rating;
  const reviewCount = researchData?.google_review_count;

  if (rating == null || rating >= GOOGLE_RATING_THRESHOLD) return null;

  const confidence = rating < 4.0 ? 'high' : 'medium';
  const reviewNote = reviewCount != null ? ` from ${reviewCount} reviews` : '';

  return {
    _isGoogleCard: true,  // marker so we can identify it later if needed
    title: 'Below-Average Google Review Score',
    confidence,
    evidence: `The business currently holds a ${rating}★ Google rating${reviewNote}, below the ${GOOGLE_RATING_THRESHOLD} benchmark that signals strong local trust.`,
    why: `A sub-${GOOGLE_RATING_THRESHOLD} rating can cause price-sensitive or trust-conscious prospects to choose a competitor before ever reaching the site, especially for local/service businesses where reviews are a primary trust signal.`,
  };
}

export default function ProblemsStep({ problems, researchData, onContinue }) {
  const [selectedIdxs, setSelectedIdxs] = useState([]);

  // Build the full display list: Google card (if applicable) prepended to LLM problems
  const displayProblems = useMemo(() => {
    const googleCard = buildGoogleProblemCard(researchData);
    return googleCard ? [googleCard, ...problems] : problems;
  }, [problems, researchData]);

  function toggle(idx) {
    setSelectedIdxs((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  }

  function handleContinue() {
    const sorted = [...selectedIdxs].sort((a, b) => a - b);
    const selected = sorted.map((idx) => displayProblems[idx]);
    onContinue(selected);
  }

  return (
    <div className="wizard-step">
      <h2>Identify Potential Problems</h2>
      <p className="subtitle">Select one or more problems worth focusing your outreach on.</p>

      <div className="problems-grid">
        {displayProblems.map((prob, idx) => {
          const isSelected = selectedIdxs.includes(idx);
          return (
            <div
              key={idx}
              className={`problem-card ${isSelected ? 'selected' : ''}`.trim()}
              onClick={() => toggle(idx)}
            >
              <div className="problem-card-header">
                <div className="problem-title-row">
                  <span className="problem-checkbox" />
                  <h4>{prob.title}</h4>
                </div>
                <span className={`confidence-badge confidence-${prob.confidence === 'high' ? 'high' : 'medium'}`}>
                  {prob.confidence}
                </span>
              </div>
              <p><strong>Observed issue:</strong><br />{prob.evidence}</p>
              <p><strong>Why it may matter:</strong><br />{prob.why}</p>
              <button
                className={`btn ${isSelected ? 'btn-primary' : 'btn-outline'}`}
                onClick={(e) => {
                  e.stopPropagation();
                  toggle(idx);
                }}
              >
                {isSelected ? '✓ Selected' : 'Select This Problem'}
              </button>
            </div>
          );
        })}
      </div>

      <div className="selection-status-bar">
        <div className="selection-count">
          <strong>{selectedIdxs.length}</strong> Problem(s) Selected
        </div>
        <button
          className="btn btn-primary"
          disabled={selectedIdxs.length === 0}
          onClick={handleContinue}
        >
          Continue to Offer →
        </button>
      </div>
    </div>
  );
}

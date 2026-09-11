import React, { useState } from 'react';

export default function ProblemsStep({ problems, onContinue }) {
  const [selectedIdxs, setSelectedIdxs] = useState([]);

  function toggle(idx) {
    setSelectedIdxs((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  }

  function handleContinue() {
    const sorted = [...selectedIdxs].sort((a, b) => a - b);
    const selected = sorted.map((idx) => problems[idx]);
    onContinue(selected);
  }

  return (
    <div className="wizard-step">
      <h2>Identify Potential Problems</h2>
      <p className="subtitle">Select one or more problems worth focusing your outreach on.</p>

      <div className="problems-grid">
        {problems.map((prob, idx) => {
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

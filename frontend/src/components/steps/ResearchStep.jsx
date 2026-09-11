import React, { useState } from 'react';
import { handleFetchError } from '../../utils/api';

export default function ResearchStep({ researchData, onComplete }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const research = researchData || {};

  async function handleContinue() {
    setError(null);
    setLoading(true);
    try {
      const response = await fetch('/api/problems', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ research }),
      });

      if (!response.ok) {
        throw await handleFetchError(response, 'We couldn\'t generate problems. Please try again.');
      }

      const data = await response.json();
      if (!data.problems || data.problems.length === 0) {
        throw new Error('No problems were identified. Please try again.');
      }

      onComplete(data.problems);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="wizard-step">
      <h2>Business Research</h2>
      <p className="subtitle">Review what we found about this business before identifying problems.</p>

      <div className="card">
        <h3>{research.business_name || 'Unknown Business'}</h3>
        <p><strong>Industry:</strong> {research.industry || 'Not found'}</p>
        <p><strong>Target Audience:</strong> {research.target_audience || 'Not found'}</p>
        <p><strong>Messaging:</strong> {research.messaging || 'Not found'}</p>

        {research.products_services && research.products_services.length > 0 && (
          <>
            <p><strong>Products / Services:</strong></p>
            <ul>
              {research.products_services.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </>
        )}

        {research.calls_to_action && research.calls_to_action.length > 0 && (
          <>
            <p><strong>Calls to Action:</strong></p>
            <ul>
              {research.calls_to_action.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </>
        )}
      </div>

      <div className="research-columns">
        <div className="card fact-card">
          <h3>Observed Facts</h3>
          <p className="card-hint">Directly found on the website.</p>
          {research.observed_facts && research.observed_facts.length > 0 ? (
            <ul>
              {research.observed_facts.map((fact, idx) => (
                <li key={idx}>{fact}</li>
              ))}
            </ul>
          ) : (
            <p className="card-hint">No observed facts found.</p>
          )}
        </div>

        <div className="card opportunity-card">
          <h3>Potential Opportunities</h3>
          <p className="card-hint">Inferred gaps — not confirmed facts.</p>
          {research.potential_opportunities && research.potential_opportunities.length > 0 ? (
            <ul>
              {research.potential_opportunities.map((opp, idx) => (
                <li key={idx}>{opp}</li>
              ))}
            </ul>
          ) : (
            <p className="card-hint">No opportunities identified.</p>
          )}
        </div>
      </div>

      <button className="btn btn-primary" onClick={handleContinue} disabled={loading}>
        {loading && <span className="loader" />}
        Continue to Problems
      </button>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

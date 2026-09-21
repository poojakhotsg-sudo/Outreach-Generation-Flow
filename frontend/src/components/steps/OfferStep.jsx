import React, { useEffect, useState } from 'react';
import { handleFetchError } from '../../utils/api';

export default function OfferStep({ selectedProblems, onComplete, researchData, onChangeProblem }) {
  const [initialSolution, setInitialSolution] = useState('');
  const [finalOffer, setFinalOffer] = useState('');
  const [guidance, setGuidance] = useState(null);
  const [additionalContext, setAdditionalContext] = useState('');

  const [loadingSuggestion, setLoadingSuggestion] = useState(false);
  const [loadingGuidance, setLoadingGuidance] = useState(false);
  const [loadingEmail, setLoadingEmail] = useState(false);

  const [error, setError] = useState(null);
  const [suggestionError, setSuggestionError] = useState(null);
  const [guidanceError, setGuidanceError] = useState(null);

  const [editingSolution, setEditingSolution] = useState(false);
  const [editingFinalOffer, setEditingFinalOffer] = useState(false);

  useEffect(() => {
    let cancelled = false;

    setInitialSolution('');
    setFinalOffer('');
    setGuidance(null);
    setError(null);
    setSuggestionError(null);
    setGuidanceError(null);
    setEditingSolution(false);
    setEditingFinalOffer(false);

    async function fetchSuggestion() {
      setLoadingSuggestion(true);
      try {
        const response = await fetch('/api/suggest-solution', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            selected_problems: selectedProblems,
            research: researchData || {},
            additional_context: additionalContext,
          }),
        });

        if (!response.ok) {
          throw await handleFetchError(response, 'We couldn\'t generate a suggestion. Please try again.');
        }

        const data = await response.json();
        if (!cancelled) {
          setInitialSolution(data.suggestion);
        }
      } catch (err) {
        if (!cancelled) {
          setSuggestionError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoadingSuggestion(false);
        }
      }
    }

    if (selectedProblems && selectedProblems.length > 0) {
      fetchSuggestion();
    }

    return () => {
      cancelled = true;
    };
  }, [selectedProblems, researchData]);

  async function fetchSuggestion() {
    setSuggestionError(null);
    setLoadingSuggestion(true);
    try {
      const response = await fetch('/api/suggest-solution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_problems: selectedProblems,
          research: researchData || {},
          additional_context: additionalContext,
        }),
      });

      if (!response.ok) {
        throw await handleFetchError(response, 'We couldn\'t generate a suggestion. Please try again.');
      }

      const data = await response.json();
      setInitialSolution(data.suggestion);
    } catch (err) {
      setSuggestionError(err.message);
    } finally {
      setLoadingSuggestion(false);
    }
  }

  async function handleGetGuidance() {
    setGuidanceError(null);
    setLoadingGuidance(true);
    try {
      const response = await fetch('/api/offer-guide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_problems: selectedProblems,
          initial_solution: initialSolution,
          research: researchData || {},
          additional_context: additionalContext,
        }),
      });

      if (!response.ok) {
        throw await handleFetchError(response, 'We couldn\'t generate offer guidance. Please try again.');
      }

      const data = await response.json();
      setGuidance(data.guidance);
      setFinalOffer(data.suggested_final_offer);
    } catch (err) {
      setGuidanceError(err.message);
    } finally {
      setLoadingGuidance(false);
    }
  }

  async function handleConfirm() {
    setError(null);
    setLoadingEmail(true);
    try {
      const response = await fetch('/api/generate-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_research: researchData || {},
          selected_problems: selectedProblems,
          final_solution_offer: finalOffer,
          additional_instructions: '',
          additional_context: additionalContext,
        }),
      });

      if (!response.ok) {
        throw await handleFetchError(response, 'We couldn\'t generate the email. Please try again.');
      }

      const data = await response.json();
      onComplete(finalOffer, data, additionalContext);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingEmail(false);
    }
  }

  return (
    <div className="wizard-step">
      <h2>Create a Solution Offer</h2>

      <div className="card selected-problem-summary">
        <div>
          <strong>Selected Problem(s):</strong>{' '}
          {selectedProblems.map((p) => p.title).join(', ')}
        </div>
        <button className="btn btn-outline" onClick={onChangeProblem}>
          Change Problem
        </button>
      </div>

      <div className="offer-block">
        <div className="offer-block-label">
          💡 Suggested Solution
          <span className="ai-generated-tag">AI Generated</span>
        </div>

        {editingSolution ? (
          <textarea
            rows="4"
            autoFocus
            value={initialSolution}
            onChange={(e) => setInitialSolution(e.target.value)}
            disabled={loadingSuggestion}
          />
        ) : suggestionError ? (
          <>
            <div className="error-message">{suggestionError}</div>
            <button className="btn btn-outline" onClick={fetchSuggestion}>Try Again</button>
          </>
        ) : (
          <div className="offer-quote">
            <p className="quote-hint">Suggested Solution</p>
            {initialSolution}
          </div>
        )}

        {loadingSuggestion && (
          <div className="loader-row"><span className="loader" /> Generating suggestion...</div>
        )}

        {!suggestionError && (
          <div className="button-row">
            <button className="btn btn-outline" onClick={() => setEditingSolution((v) => !v)}>
              {editingSolution ? 'Done Editing' : 'Edit Solution'}
            </button>
          </div>
        )}
      </div>

      <div className="offer-block">
        <div className="offer-block-label">Additional Context (optional)</div>
        <p className="field-hint">Add information about your business to make the offer more personalized.</p>
        <textarea
          className="additional-context-textarea"
          rows="6"
          placeholder="Tell us about your business, services, experience, case studies, testimonials, results, or unique selling points…"
          value={additionalContext}
          onChange={(e) => setAdditionalContext(e.target.value)}
        />
      </div>

      <button
        className="btn btn-secondary"
        onClick={handleGetGuidance}
        disabled={loadingSuggestion || loadingGuidance || !initialSolution}
      >
        {loadingGuidance && <span className="loader" />}
        Get Offer Guidance
      </button>

      {loadingGuidance && (
        <div className="loader-row"><span className="loader" /> Generating offer guidance...</div>
      )}
      {guidanceError && <div className="error-message">{guidanceError}</div>}

      {guidance && (
        <div className="guidance-box">
          <strong>Offer Guidance</strong>
          <ul>
            <li><strong>What:</strong> {guidance.what}</li>
            <li><strong>Outcome:</strong> {guidance.outcome}</li>
            <li><strong>Timeframe:</strong> {guidance.timeframe}</li>
            <li><strong>Guarantee:</strong> {guidance.guarantee}</li>
          </ul>
        </div>
      )}

      {guidance && (
        <div className="offer-block">
          <div className="offer-block-label">💡 Suggested Final Offer</div>

          {editingFinalOffer ? (
            <textarea
              rows="4"
              autoFocus
              value={finalOffer}
              onChange={(e) => setFinalOffer(e.target.value)}
            />
          ) : (
            <div className="offer-quote">
              <p className="quote-hint">Final Offer</p>
              {finalOffer || 'No final offer yet.'}
            </div>
          )}

          <div className="button-row">
            <button className="btn btn-outline" onClick={() => setEditingFinalOffer((v) => !v)}>
              {editingFinalOffer ? 'Done Editing' : 'Edit Final Offer'}
            </button>
          </div>
        </div>
      )}

      <p className="subtitle">Review and customize the offer before confirming.</p>

      <div className="button-row">
        <button className="btn btn-outline" onClick={onChangeProblem}>← Back</button>
        <button
          className="btn btn-primary"
          onClick={handleConfirm}
          disabled={!finalOffer || loadingEmail}
        >
          {loadingEmail && <span className="loader" />}
          Confirm Offer & Generate Email →
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

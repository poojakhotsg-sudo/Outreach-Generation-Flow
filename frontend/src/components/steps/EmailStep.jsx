import React, { useState } from 'react';
import { handleFetchError } from '../../utils/api';

export default function EmailStep({
  emailData,
  researchData,
  selectedProblems,
  finalOffer,
  additionalContext,
  onBackToOffer,
  onBackToProblems,
}) {
  const [subject, setSubject] = useState(emailData?.subject || '');
  const [body, setBody] = useState(emailData?.email || '');
  const [instructions, setInstructions] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  async function generateEmail(additionalInstructions = '') {
    setError(null);
    setLoading(true);
    try {
      const response = await fetch('/api/generate-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_research: researchData,
          selected_problems: selectedProblems,
          final_solution_offer: finalOffer,
          additional_instructions: additionalInstructions,
          additional_context: additionalContext || '',
        }),
      });

      if (!response.ok) {
        throw await handleFetchError(response, 'We couldn\'t generate the email. Please try again.');
      }

      const data = await response.json();
      setSubject(data.subject);
      setBody(data.email);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    const text = `Subject: ${subject}\n\n${body}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      setError('Failed to copy to clipboard.');
    }
  }

  return (
    <div className="wizard-step">
      <h2>Review & Edit Outreach</h2>
      <p className="subtitle">Your personalized outreach is ready. Review and adjust it as needed.</p>

      <div className="form-group">
        <label htmlFor="email-subject">Subject</label>
        <input
          id="email-subject"
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label htmlFor="email-body">Email Body</label>
        <textarea
          id="email-body"
          rows="12"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
      </div>

      <div className="button-row">
        <button className="btn btn-outline" onClick={handleCopy}>{copied ? 'Copied!' : 'Copy'}</button>
        <button className="btn btn-outline" onClick={() => generateEmail()} disabled={loading}>Regenerate</button>
        <button className="btn btn-outline" onClick={() => generateEmail('Make it much shorter and punchier.')} disabled={loading}>Make Shorter</button>
        <button className="btn btn-outline" onClick={() => generateEmail('Make the tone highly professional and corporate.')} disabled={loading}>Make More Professional</button>
        <button className="btn btn-outline" onClick={() => generateEmail('Make it very casual, conversational, and friendly.')} disabled={loading}>Make More Conversational</button>
      </div>

      <div className="form-group">
        <label htmlFor="additional-instructions">Additional Instructions</label>
        <input
          id="additional-instructions"
          type="text"
          placeholder="e.g. Mention that we offer a free audit."
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
        />
      </div>

      <button className="btn btn-secondary" onClick={() => generateEmail(instructions)} disabled={loading}>
        {loading && <span className="loader" />}
        Regenerate Email with Instructions
      </button>

      {loading && <div className="loader-row"><span className="loader" /> Generating email...</div>}
      {error && <div className="error-message">{error}</div>}

      <div className="button-row">
        <button className="btn btn-outline" onClick={onBackToOffer}>Change Offer</button>
        <button className="btn btn-outline" onClick={onBackToProblems}>Change Problem</button>
      </div>
    </div>
  );
}

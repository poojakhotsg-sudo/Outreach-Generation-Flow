import React, { useState } from 'react';
import { handleFetchError } from '../../utils/api';

function normalizeAndValidateUrl(raw) {
  let value = raw.trim();
  if (!value) {
    return { error: 'Please enter a website URL.' };
  }
  if (!/^https?:\/\//i.test(value)) {
    value = `https://${value}`;
  }
  try {
    const parsed = new URL(value);
    if (!parsed.hostname.includes('.')) {
      return { error: 'Please enter a valid website URL.' };
    }
    return { url: value };
  } catch (e) {
    return { error: 'Please enter a valid website URL.' };
  }
}

export default function WebsiteStep({ onComplete }) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    const { url: normalizedUrl, error: validationError } = normalizeAndValidateUrl(url);
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ website_url: normalizedUrl }),
      });

      if (!response.ok) {
        throw await handleFetchError(response, 'We couldn\'t research this website. Please try again.');
      }

      const data = await response.json();
      onComplete(normalizedUrl, data.research);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="wizard-step">
      <h2>Research a Business</h2>
      <p className="subtitle">Enter a business website URL to begin.</p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="website-url">Website URL</label>
          <input
            id="website-url"
            type="url"
            placeholder="https://examplebusiness.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading && <span className="loader" />}
          Research Business
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

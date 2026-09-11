import React from 'react';

const STEP_META = {
  1: { title: 'Research a Business', description: 'Enter a business website URL to begin.' },
  2: { title: 'Business Research', description: 'Review what we found about this business before identifying problems.' },
  3: { title: 'Identify Potential Problems', description: 'Select one or more problems worth focusing your outreach on.' },
  4: { title: 'Create a Solution Offer', description: 'Turn the selected business opportunity into a clear, compelling offer.' },
  5: { title: 'Review & Edit Outreach', description: 'Your personalized outreach is ready. Review and adjust it as needed.' },
};

export default function Header({ currentStep, userEmail }) {
  const meta = STEP_META[currentStep] || STEP_META[1];
  const initial = (userEmail && userEmail[0]) ? userEmail[0].toUpperCase() : 'U';
  const name = userEmail ? userEmail.split('@')[0] : 'User';

  return (
    <header className="top-header">
      <div>
        <h1>{meta.title}</h1>
        <p>{meta.description}</p>
      </div>
      <div className="user-menu">
        <div className="user-avatar">{initial}</div>
        <div className="user-name">{name}</div>
      </div>
    </header>
  );
}

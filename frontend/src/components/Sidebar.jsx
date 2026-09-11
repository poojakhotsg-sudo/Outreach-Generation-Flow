import React from 'react';

const WORKFLOW_STEPS = [
  { id: 1, num: '01', label: 'Website' },
  { id: 2, num: '02', label: 'Research' },
  { id: 3, num: '03', label: 'Problems' },
  { id: 4, num: '04', label: 'Offer' },
  { id: 5, num: '05', label: 'Email' },
];

export default function Sidebar({ currentStep }) {
  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-mark">OG</div>
        <div className="logo-text">Outreach Generator</div>
      </div>

      <div className="sidebar-section-label">Workflow</div>
      <ul className="sidebar-nav">
        {WORKFLOW_STEPS.map((step) => {
          const isActive = currentStep === step.id;
          const isDone = currentStep > step.id;
          return (
            <li key={step.id} className={`${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`.trim()}>
              <span className="step-left">
                <span className="step-num">{step.num}</span>
                <span>{step.label}</span>
              </span>
              {isDone && <span className="step-check">✓</span>}
            </li>
          );
        })}
      </ul>

      <div className="sidebar-section-label">Other</div>
      <ul className="sidebar-nav">
        <li className="clickable">
          <span className="step-left">
            <span>⚙</span>
            <span>Settings</span>
          </span>
        </li>
      </ul>
    </aside>
  );
}

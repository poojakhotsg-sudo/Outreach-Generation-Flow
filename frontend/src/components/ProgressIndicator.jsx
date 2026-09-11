import React from 'react';

const STEPS = [
  { id: 1, label: 'Website' },
  { id: 2, label: 'Research' },
  { id: 3, label: 'Problems' },
  { id: 4, label: 'Offer' },
  { id: 5, label: 'Email' },
];

export default function ProgressIndicator({ currentStep }) {
  return (
    <div className="progress-indicator">
      {STEPS.map((step, idx) => {
        const isActive = currentStep === step.id;
        const isDone = currentStep > step.id;
        return (
          <React.Fragment key={step.id}>
            <div className={`progress-step ${isActive ? 'active' : ''}`.trim()}>
              <div className={`progress-dot ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`.trim()}>
                {isDone ? '✓' : step.id}
              </div>
              <div className="progress-label">{step.label}</div>
            </div>
            {idx < STEPS.length - 1 && <div className="step-connector" />}
          </React.Fragment>
        );
      })}
    </div>
  );
}

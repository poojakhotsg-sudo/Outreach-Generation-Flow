import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ProgressIndicator from './components/ProgressIndicator';
import WebsiteStep from './components/steps/WebsiteStep';
import ResearchStep from './components/steps/ResearchStep';
import ProblemsStep from './components/steps/ProblemsStep';
import OfferStep from './components/steps/OfferStep';
import EmailStep from './components/steps/EmailStep';

export default function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [researchData, setResearchData] = useState(null);
  const [problems, setProblems] = useState([]);
  const [selectedProblems, setSelectedProblems] = useState([]);
  const [finalOffer, setFinalOffer] = useState('');
  const [emailData, setEmailData] = useState(null);
  const [additionalContext, setAdditionalContext] = useState('');

  function handleWebsiteComplete(url, research) {
    setWebsiteUrl(url);
    setResearchData(research);
    setCurrentStep(2);
  }

  function handleResearchComplete(problemsList) {
    setProblems(problemsList);
    setCurrentStep(3);
  }

  function handleProblemsComplete(selected) {
    setSelectedProblems(selected);
    setCurrentStep(4);
  }

  function handleOfferComplete(offer, email, context) {
    setFinalOffer(offer);
    setEmailData(email);
    setAdditionalContext(context || '');
    setCurrentStep(5);
  }

  return (
    <div className="dashboard-container">
      <Sidebar currentStep={currentStep} />
      <main className="main-content">
        <Header currentStep={currentStep} userEmail="adrian@engagementsauce.com" />
        <ProgressIndicator currentStep={currentStep} />
        <div className="wizard-container">
          {currentStep === 1 && <WebsiteStep onComplete={handleWebsiteComplete} />}
          {currentStep === 2 && (
            <ResearchStep researchData={researchData} onComplete={handleResearchComplete} />
          )}
          {currentStep === 3 && (
            <ProblemsStep problems={problems} researchData={researchData} onContinue={handleProblemsComplete} />
          )}
          {currentStep === 4 && (
            <OfferStep
              selectedProblems={selectedProblems}
              researchData={researchData}
              onComplete={handleOfferComplete}
              onChangeProblem={() => setCurrentStep(3)}
            />
          )}
          {currentStep === 5 && (
            <EmailStep
              emailData={emailData}
              researchData={researchData}
              selectedProblems={selectedProblems}
              finalOffer={finalOffer}
              additionalContext={additionalContext}
              onBackToOffer={() => setCurrentStep(4)}
              onBackToProblems={() => setCurrentStep(3)}
            />
          )}
        </div>
      </main>
    </div>
  );
}

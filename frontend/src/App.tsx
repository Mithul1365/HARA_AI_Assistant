import { useState } from 'react';



import Header from '@/components/Header';

import Sidebar from '@/components/Sidebar';

import Home from '@/screens/Home';

import ItemDefinition from '@/screens/ItemDefinition';

import HaraAnalysis from '@/screens/HaraAnalysis';

import AsilAssessment from '@/screens/AsilAssessment';

import SafetyGoals from '@/screens/SafetyGoals';

import FunctionalSafetyRequirements from '@/screens/FunctionalSafetyRequirements';

import TechnicalSafetyRequirements from '@/screens/TechnicalSafetyRequirements';

import Placeholder from '@/screens/Placeholder';

import TraceabilityMatrix from '@/screens/TraceabilityMatrix';

import VerificationEvidence from '@/screens/VerificationEvidence';

import ReviewAudit from '@/screens/ReviewAudit';



import { type StepId } from '@/types/workflow';





export interface DocumentData {

  documentId: string;

  documentName: string;

  pdfHash: string;

  pages: number;

  chunks: number;

}





export interface ItemContext {

  systemItem: string;

  intendedFunction: string;

  operationalScenario: string;

  operatingConditions: string;

}





export interface HaraScenario {

  number: number;

  malfunction: string;

  hazard: string;

  event: string;

  rationale: string;

}





export interface HaraEvidence {

  text: string;

  source: string;

  score?: number;

}





export interface AsilResult {
  asil: string;
  rationale: string;
  severity: string;
  exposure: string;
  controllability: string;
}





export interface SafetyGoalResult {

  id?: string;

  safety_goal: string;

  candidate_asil: string;

  hazard: string;

  hazardous_event: string;

  malfunction: string;

  system?: string;

  function?: string;

}





export interface FSRResult {

  id: string;

  requirement: string;

  rationale: string;

  candidate_asil: string;

  review_status: string;

  hazard: string;

  hazardous_event: string;

  system: string;

  function: string;

  malfunction: string;

  safety_goal: string;

}





export interface TSRResult {

  id: string;

  requirement: string;

  rationale: string;

  candidate_asil: string;

  review_status: string;

  system: string;

  function: string;

  malfunction: string;

  hazard: string;

  hazardous_event: string;

  safety_goal: string;

  fsr: string;

}





function App() {



  const [activeStep, setActiveStep] =

    useState<StepId>('home');



  /*

   * Stores only steps that were actually completed

   * by pressing Continue.

   *

   * Going Previous does not remove a completed step.

   */

  const [completedSteps, setCompletedSteps] =

    useState<Set<StepId>>(new Set());



  const [documentData, setDocumentData] =

    useState<DocumentData | null>(null);



  const [itemContext, setItemContext] =

    useState<ItemContext>({

      systemItem: '',

      intendedFunction: '',

      operationalScenario: '',

      operatingConditions: '',

    });



  const [haraScenarios, setHaraScenarios] =

    useState<HaraScenario[]>([]);



  const [haraEvidence, setHaraEvidence] =

    useState<HaraEvidence[]>([]);



  const [selectedHaraScenario, setSelectedHaraScenario] =

    useState<HaraScenario | null>(null);



  const [asilResult, setAsilResult] =

    useState<AsilResult | null>(null);



  const [safetyGoal, setSafetyGoal] =

    useState<SafetyGoalResult | null>(null);


const [fsrResults, setFsrResults] =
  useState<FSRResult[]>([]);

const [tsrResults, setTsrResults] =
  useState<TSRResult[]>([]);
  




  /*

   * Complete current step and move to the next step.

   */

  const completeStepAndGo = (nextStep: StepId) => {



    if (activeStep !== 'home') {



      setCompletedSteps((previous) => {



        const updated = new Set(previous);



        updated.add(activeStep);



        return updated;

      });

    }



    setActiveStep(nextStep);

  };





  const handleItemDefinitionContinue = (

    document: DocumentData,

    context: ItemContext

  ) => {



    setDocumentData(document);

    setItemContext(context);



    completeStepAndGo('hara-analysis');

  };





  const handleHaraContinue = (

    scenario: HaraScenario

  ) => {



    setSelectedHaraScenario(scenario);



    completeStepAndGo('asil-assessment');

  };





  const handleAsilContinue = (

    result: AsilResult

  ) => {



    setAsilResult(result);



    completeStepAndGo('safety-goals');

  };





  const startNewWorkflow = () => {



    setActiveStep('item-definition');



    /*

     * Clear all workflow completion ticks.

     */

    setCompletedSteps(new Set());



    setDocumentData(null);



    setItemContext({

      systemItem: '',

      intendedFunction: '',

      operationalScenario: '',

      operatingConditions: '',

    });



    setHaraScenarios([]);



    setHaraEvidence([]);



    setSelectedHaraScenario(null);



    setAsilResult(null);



    setSafetyGoal(null);



    setFsrResults([]);



    setTsrResults([]);





    // Clear workflow-specific browser persistence.

    try {



      localStorage.removeItem(

        'hara_ai_assistant_selected_hara_scenario'

      );



      localStorage.removeItem(

        'hara_ai_assistant_asil_state'

      );



      localStorage.removeItem(

        'hara_ai_assistant_verification_draft'

      );



    } catch {



      // Ignore localStorage errors.



    }

  };





  const renderStep = () => {



    switch (activeStep) {





      case 'traceability-matrix':



        return (

          <TraceabilityMatrix

            itemContext={itemContext}

            scenario={selectedHaraScenario}

            asilResult={asilResult}

            safetyGoal={safetyGoal}

            fsrResults={fsrResults}

            tsrResults={tsrResults}



            onPrevious={() =>

              setActiveStep(

                'technical-safety-requirements'

              )

            }



            onContinue={() =>

              completeStepAndGo(

                'verification-evidence'

              )

            }

          />

        );





      case 'review-audit':



        return (

          <ReviewAudit

            itemContext={itemContext}

            scenario={selectedHaraScenario}

            asilResult={asilResult}

            safetyGoal={safetyGoal}

            fsrResults={fsrResults}

            tsrResults={tsrResults}



            onPrevious={() =>

              setActiveStep(

                'verification-evidence'

              )

            }



            onComplete={() =>

              completeStepAndGo(

                'hara-analysis'

              )

            }



            onNewWorkflow={

              startNewWorkflow

            }

          />

        );





      case 'verification-evidence':



        return (

          <VerificationEvidence

            itemContext={itemContext}

            scenario={selectedHaraScenario}



            onPrevious={() =>

              setActiveStep(

                'traceability-matrix'

              )

            }



            onContinue={() =>

              completeStepAndGo(

                'review-audit'

              )

            }

          />

        );





      case 'home':



        return (

          <Home
            onStepClick={setActiveStep}
            documentsUploaded={documentData ? 1 : 0}
            haraScenarioCount={haraScenarios.length}
           activeAsil={asilResult?.asil || '—'}
        />

        );





      case 'item-definition':



        return (

          <ItemDefinition

            initialDocumentData={

              documentData

            }



            initialItemContext={

              itemContext

            }



            onContinue={

              handleItemDefinitionContinue

            }

          />

        );





      case 'hara-analysis':



        return (

          <HaraAnalysis

            documentData={

              documentData

            }



            itemContext={

              itemContext

            }



            onPrevious={() =>

              setActiveStep(

                'item-definition'

              )

            }



            onContinue={

              handleHaraContinue

            }



            onScenariosLoaded={

              setHaraScenarios

            }



            initialScenarios={

              haraScenarios

            }



            initialEvidence={

              haraEvidence

            }



            onEvidenceLoaded={

              setHaraEvidence

            }

          />

        );





      case 'asil-assessment':



        return (

          <AsilAssessment

            itemContext={

              itemContext

            }



            scenarios={

              haraScenarios

            }



            selectedScenario={

              selectedHaraScenario

            }



            onPrevious={() =>

              setActiveStep(

                'hara-analysis'

              )

            }



            onResult={(result) =>
              setAsilResult({
                asil: result.asil,
                rationale: result.rationale ?? '',
                severity: result.severity,
                exposure: result.exposure,
                controllability: result.controllability,
              })
            }

            onContinue={(result) =>
              handleAsilContinue({
                asil: result.asil,
                rationale: result.rationale ?? '',
                severity: result.severity,
                exposure: result.exposure,
                controllability: result.controllability,
              })
            }

          />

        );





      case 'safety-goals':



        return (

          <SafetyGoals

            itemContext={

              itemContext

            }



            scenario={

              selectedHaraScenario ||

              haraScenarios[0] ||

              null

            }



            asilResult={

              asilResult

            }



            initialResult={

              safetyGoal

            }



            onPrevious={() =>

              setActiveStep(

                'asil-assessment'

              )

            }



            onGenerated={

              setSafetyGoal

            }



            onContinue={() =>

              completeStepAndGo(

                'functional-safety-requirements'

              )

            }

          />

        );





      case 'functional-safety-requirements':



        return (

          <FunctionalSafetyRequirements

            itemContext={

              itemContext

            }



            scenario={

              selectedHaraScenario ||

              haraScenarios[0] ||

              null

            }



            asilResult={

              asilResult

            }



            safetyGoal={

              safetyGoal

            }



            initialResults={

              fsrResults

            }



            onPrevious={() =>

              setActiveStep(

                'safety-goals'

              )

            }



            onGenerated={

              setFsrResults

            }



            onContinue={() =>

              completeStepAndGo(

                'technical-safety-requirements'

              )

            }

          />

        );





      case 'technical-safety-requirements':



        return (

          <TechnicalSafetyRequirements

            itemContext={

              itemContext

            }



            scenario={

              selectedHaraScenario ||

              haraScenarios[0] ||

              null

            }



            asilResult={

              asilResult

            }



            safetyGoal={

              safetyGoal

            }



            fsrResults={

              fsrResults

            }



            initialResults={

              tsrResults

            }



            onPrevious={() =>

              setActiveStep(

                'functional-safety-requirements'

              )

            }



            onGenerated={

              setTsrResults

            }



            onContinue={() =>

              completeStepAndGo(

                'traceability-matrix'

              )

            }

          />

        );





      default:



        return (

          <Placeholder

            stepId={

              activeStep

            }

          />

        );



    }

  };





  return (

    <div className="h-screen flex flex-col bg-slate-100 overflow-hidden">



      <Header />



      <div className="flex flex-1 overflow-hidden">



        <Sidebar

          activeStep={

            activeStep

          }



          completedSteps={

            completedSteps

          }



          onStepClick={

            setActiveStep

          }

        />



        <main className="flex-1 overflow-y-auto">



          {renderStep()}



        </main>



      </div>



    </div>

  );

}





export default App;
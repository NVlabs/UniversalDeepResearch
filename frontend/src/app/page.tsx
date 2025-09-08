/*
 * SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
'use client';

import { useState, useRef } from 'react';
import PromptBar from '@/components/PromptBar';
import ResearchProgressList, { ResearchEventType } from '@/components/ResearchProgressList';
import ReportViewer from '@/components/ReportViewer';
import ResearchStrategyEditor from '@/components/ResearchStrategyEditor';
import { ApplicationState } from '@/types/ApplicationState';
import { v4 as uuidv4 } from 'uuid';
import config, { getApiEndpoint } from '@/config';

// Define interfaces for API data structures
interface ApiEventData {
  event: {
    type: string;
    description?: string;
    report?: string;
    deltaSearchCount?: number;
    deltaQueryCount?: number;
    hidden?: boolean;
  };
  session_key?: string;
}

interface ApiRequestBody {
  prompt?: string;
  session_key?: string;
  strategy_id?: string;
  strategy_content?: string;
  dry: boolean;
  start_from: 'research' | 'reporting';
}

export default function Home() {
  const [state, setState] = useState<ApplicationState>({
    type: 'idle',
    sessionKey: "",
    researchStartTimestamp: 0,
    researchEndTimestamp: 0,
    searchCount: 0,
    queryCount: 0,
    finalizationStartTimestamp: 0,
    finalizationEndTimestamp: 0,
    events: []
  });
  const [reportContent, setReportContent] = useState<string>('');
  const [editedStrategyId, setEditedStrategyId] = useState('');
  const [strategyContents, setStrategyContents] = useState<Record<string, string>>(initialStrategyContents);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Shared API communication function with proper typing
  const communicateWithAPI = async (
    requestBody: ApiRequestBody,
    initialStateUpdate: (prev: ApplicationState) => ApplicationState,
    eventHandlers: {
      onStarted?: (data: ApiEventData, prev: ApplicationState) => Partial<ApplicationState>,
      onCompleted?: (data: ApiEventData, prev: ApplicationState) => Partial<ApplicationState>,
      onCancelled?: (data: ApiEventData, prev: ApplicationState) => Partial<ApplicationState>,
      onReportBuilding?: (data: ApiEventData, prev: ApplicationState) => Partial<ApplicationState>,
      onReportDone?: (data: ApiEventData, prev: ApplicationState) => Partial<ApplicationState>,
      onOtherEvent?: (data: ApiEventData, prev: ApplicationState) => Partial<ApplicationState>,
      onServerError?: (data: ApiEventData, prev: ApplicationState) => Partial<ApplicationState>,
    }
  ) => {
    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(getApiEndpoint(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to communicate with server');
      }

      if (!response.body) {
        throw new Error('No response body received');
      }

      // Apply initial state update
      setState(initialStateUpdate);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last incomplete line in the buffer

        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line) as ApiEventData;

              if (data.event.type === 'started' && eventHandlers.onStarted) {
                setState(prev => ({
                  ...prev,
                  ...eventHandlers.onStarted?.(data, prev)
                }) as ApplicationState);
              } else if (data.event.type === 'completed' && eventHandlers.onCompleted) {
                setState(prev => ({
                  ...prev,
                  ...eventHandlers.onCompleted?.(data, prev)
                }) as ApplicationState);

                if (abortControllerRef.current) {
                  abortControllerRef.current = null;
                }
                break;
              } else if (data.event.type === 'cancelled' && eventHandlers.onCancelled) {
                setState(prev => ({
                  ...prev,
                  ...eventHandlers.onCancelled?.(data, prev)
                }) as ApplicationState);

                if (abortControllerRef.current) {
                  abortControllerRef.current = null;
                }
                break;
              } else if (data.event.type === 'report_building' && eventHandlers.onReportBuilding) {
                setState(prev => ({
                  ...prev,
                  ...eventHandlers.onReportBuilding?.(data, prev)
                }) as ApplicationState);
              } else if (data.event.type === 'report_done' && eventHandlers.onReportDone) {
                // Save the report content if available
                if (data.event.report) {
                  setReportContent(data.event.report);
                }

                setState(prev => ({
                  ...prev,
                  ...eventHandlers.onReportDone?.(data, prev)
                }) as ApplicationState);

                if (abortControllerRef.current) {
                  abortControllerRef.current = null;
                }
                break;
              } else if (data.event.type === 'error' && eventHandlers.onServerError) {
                console.error('Server error:', data);
                setState(prev => ({
                  ...prev,
                  ...eventHandlers.onServerError?.(data, prev)
                }) as ApplicationState);
                break;
              } else if (eventHandlers.onOtherEvent) {
                setState(prev => ({
                  ...prev,
                  ...eventHandlers.onOtherEvent?.(data, prev)
                }) as ApplicationState);
              }
            } catch (e) {
              console.error('Failed to parse event:', e);
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          console.log('AbortError -- normal interruption');
          return;
        }
        handleError(error.message);
      } else {
        handleError('An unknown error occurred');
      }
    }
  };

  const handleStartResearch = async (query: string, strategyId: string) => {
    if (state.type === 'researching' || state.type === 'finalizing') return;

    await communicateWithAPI(
      {
        prompt: query.trim(),
        strategy_id: strategyId,
        strategy_content: strategyContents[strategyId] || '',
        dry: config.runtime.dryRun,
        start_from: 'research'
      },
      (prev) => ({
        type: 'researching',
        sessionKey: prev.sessionKey,
        researchStartTimestamp: Date.now(),
        researchEndTimestamp: 0,
        searchCount: 0,
        queryCount: 1,
        finalizationStartTimestamp: 0,
        finalizationEndTimestamp: 0,
        events: []
      }),
      {
        onStarted: (data, prev) => ({
          type: 'researching',
          researchStartTimestamp: Date.now(),
          researchEndTimestamp: 0,
          sessionKey: data.session_key || prev.sessionKey || "",
          searchCount: 0,
          queryCount: 0,
          finalizationStartTimestamp: 0,
          finalizationEndTimestamp: 0,
          events: []
        }),
        onCompleted: (data, prev) => ({
          type: 'done',
          sessionKey: data.session_key || prev.sessionKey || "",
          finalizationEndTimestamp: Date.now()
        }),
        onCancelled: (data, prev) => ({
          type: 'stopped',
          sessionKey: data.session_key || prev.sessionKey || "",
          researchEndTimestamp: prev.finalizationStartTimestamp > 0 ? prev.researchEndTimestamp : Date.now(),
          finalizationEndTimestamp: prev.finalizationStartTimestamp > 0 ? Date.now() : 0
        }),
        onReportBuilding: (data, prev) => ({
          type: 'finalizing',
          researchEndTimestamp: prev.researchEndTimestamp > 0 ? prev.researchEndTimestamp : Date.now(),
          finalizationStartTimestamp: Date.now(),
          finalizationEndTimestamp: 0,
          events: data.event.hidden ? prev.events : [
            ...prev.events,
            {
              id: uuidv4(),
              type: (data.event.type || 'search') as ResearchEventType,
              description: data.event.description || 'No description given',
              timestamp: Date.now(),
            },
          ],
          searchCount: prev.searchCount + (data.event.deltaSearchCount || 0),
          queryCount: prev.queryCount + (data.event.deltaQueryCount || 0)
        }),
        onReportDone: (data, prev) => ({
          type: 'done',
          sessionKey: data.session_key || prev.sessionKey || "",
          finalizationEndTimestamp: Date.now()
        }),
        onServerError: (data, prev) => ({
          type: 'error',
          error: data.event.description || 'Unknown error',
          events: data.event.hidden ? prev.events : [
            ...prev.events,
            {
              id: uuidv4(),
              type: 'error',
              description: data.event.description || 'Unknown error',
              timestamp: Date.now(),
            },
          ],
          searchCount: prev.searchCount + (data.event.deltaSearchCount || 0),
          queryCount: prev.queryCount + (data.event.deltaQueryCount || 0)
        }),
        onOtherEvent: (data, prev) => ({
          sessionKey: data.session_key || prev.sessionKey || "",
          events: data.event.hidden ? prev.events : [
            ...prev.events,
            {
              id: uuidv4(),
              type: (data.event.type || 'search') as ResearchEventType,
              description: data.event.description || 'No description given',
              timestamp: Date.now(),
            },
          ],
          searchCount: prev.searchCount + (data.event.deltaSearchCount || 0),
          queryCount: prev.queryCount + (data.event.deltaQueryCount || 0)
        })
      }
    );
  };

  const handleStartFinalizing = async () => {
    if (state.type === 'researching' || state.type === 'finalizing') return;

    await communicateWithAPI(
      {
        session_key: state.sessionKey,
        dry: config.runtime.dryRun,
        start_from: 'reporting'
      },
      (prev) => ({
        ...prev,
        type: 'finalizing',
        sessionKey: prev.sessionKey || "",
        finalizationStartTimestamp: Date.now(),
        finalizationEndTimestamp: 0
      }),
      {
        onCompleted: (data, prev) => ({
          type: 'done',
          sessionKey: data.session_key || prev.sessionKey || "",
          finalizationEndTimestamp: Date.now()
        }),
        onCancelled: (data, prev) => ({
          type: 'stopped',
          sessionKey: data.session_key || prev.sessionKey || "",
          finalizationEndTimestamp: Date.now()
        }),
        onServerError: (data, prev) => ({
          type: 'error',
          error: data.event.description || 'Unknown error',
          events: data.event.hidden ? prev.events : [
            ...prev.events,
            {
              id: uuidv4(),
              type: 'error',
              description: data.event.description || 'Unknown error',
              timestamp: Date.now(),
            },
          ],
        }),
        onOtherEvent: (data, prev) => ({
          events: data.event.hidden || data.event.type === '__final' ? prev.events : [
            ...prev.events,
            {
              id: uuidv4(),
              type: (data.event.type || 'search') as ResearchEventType,
              description: data.event.description || 'No description given',
              timestamp: Date.now(),
              deltaSearchCount: data.event.deltaSearchCount || 0,
              deltaQueryCount: data.event.deltaQueryCount || 0,
            },
          ]
        })
      }
    );
  };

  const handleStop = () => {
    if (state.type !== 'researching' && state.type !== 'finalizing') return;

    // Abort the ongoing request if it exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setState(prev => ({
      type: 'stopped',
      sessionKey: prev.sessionKey,
      researchStartTimestamp: prev.researchStartTimestamp,
      researchEndTimestamp: prev.researchEndTimestamp > 0 ? prev.researchEndTimestamp : Date.now(),
      searchCount: prev.searchCount,
      queryCount: prev.queryCount,
      finalizationStartTimestamp: prev.finalizationStartTimestamp,
      finalizationEndTimestamp: prev.finalizationStartTimestamp > 0 ? Date.now() : 0,
      events: prev.events,
    }));
  };

  const handleClear = () => {
    setReportContent('');
    setState({
      type: 'idle',
      sessionKey: "",
      researchStartTimestamp: 0,
      researchEndTimestamp: 0,
      searchCount: 0,
      queryCount: 0,
      finalizationStartTimestamp: 0,
      finalizationEndTimestamp: 0,
      events: []
    });
  };

  const handleViewError = () => {
    // TODO: Implement scroll to error functionality
    console.log('Scrolling to error...');
  };

  const handleError = (error: string) => {
    setState(prev => ({
      ...prev,
      type: 'error',
      error: error
    }));
  };

  const handleStartEditingStrategy = (strategyId: string) => {
    setEditedStrategyId(strategyId);
  };

  const handleStrategyAccept = (editedStrategyContent: string) => {
    setStrategyContents(prev => ({
      ...prev,
      [editedStrategyId]: editedStrategyContent
    }));
    setEditedStrategyId('');
    console.log('Strategy updated:', editedStrategyId, editedStrategyContent);
  };

  const handleStrategyRevert = () => {
    setEditedStrategyId('');
    console.log('Strategy reverted:', strategyContents[editedStrategyId]);
  };

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="row-start-2 flex flex-col items-center justify-center gap-8 w-full">
        <div className="w-[min(90%,max(200pt,40%))] min-w-[30rem] flex flex-col items-center justify-center gap-8">
          <h1 className="text-4xl font-bold">Groq's Universal Deep Research</h1>
          <PromptBar
            onResearch={handleStartResearch}
            onEditStrategy={handleStartEditingStrategy}
            state={state}
            isAStrategyBeingEdited={editedStrategyId !== ''}
          />
          {editedStrategyId !== '' && (
            <ResearchStrategyEditor
              editedStrategyInitialContent={strategyContents[editedStrategyId] || ''}
              onAccept={handleStrategyAccept}
              onRevert={handleStrategyRevert}
              state={state}
            />
          )}
          <ResearchProgressList
            state={state}
            onStop={handleStop}
            onClear={handleClear}
            onFinalize={handleStartFinalizing}
            onViewError={handleViewError}
          />
        </div>
        {state.type === 'done' && reportContent !== '' && (
          <div className="w-[min(90%,70%)]">
            <ReportViewer report={reportContent} isVisible={true} />
          </div>
        )}
      </main>
    </div>
  );
}

const initialStrategyContents = {
  default: ``,
  minimal: `1. Send a notification of type "prompt_received" with description saying what PROMPT has been received, e.g. "Received research request: {PROMPT}"
2. Send a notification of type "prompt_analysis_started", with description indicating that we are now analyzing the research request.
3. Take the PROMPT and ask a language model to produce 3 search phrases that could help with retrieving results from search engine for the purpose of compiling a report the user asks for in the PROMPT. The search phrases should be simple and objective, e.g. "important events 1972" or "energy consumption composition in India today". Use a long prompt for the model that describes in detail what is supposed to be performed and the expected output format. Instruct the model to return the search phrases on one line each. Tell the model not to output any other text -- just the newline-separated phrases. Then, parse the output of the language model line by line and save the resulting search phrases as "phrases" for further research, skipping over empty lines.
4. Send a notification of type "prompt_analysis_completed", with a description saying as much.
4.1 Send a notification of type "task_analysis_completed", informing the user that the search plan has been completed and informing them how many search phrases will be invoked, e.g.  "Search planning completed. Will be searching through {len(topics)}+ terms."
5. For each phrase in phrases output by step 3., perform the following:
    - Send a notification of type "search_started", with the description indicating what search phrase we are using for the search, e.g. "Searching for phrase '{phrase}'"
    - Perform search with the phrase.
    - Once the search returns some results, append their contents to CONTEXT one by one, separating them by double newlines from what is already present in the CONTEXT.
    - Send a notification of type "search_result_processing_completed", indicating in its description that the search results for term {term} have been processed.
6. Send a notification to the user with type "research_completed", indicating that the "Research phase is now completed.".
7. Send a notification with type "report_building", with the description indicating that the report is being built.
8. Take CONTEXT. Call the language model, instructing it to take CONTEXT (to be appended into the LM call) and produce a deep research report on the topic requested in PROMPT. The resulting report should go into detail wherever possible, rely only on the information available in CONTEXT, address the instruction given in the PROMPT, and be formatted in Markdown. This is to be communicated in the prompt. Do not shy away from using long, detailed and descriptive prompts! Tell the model not to output any other text, just the report. The result produced by the language model is to be called REPORT.
9. Send a notification with type "report_done", indicating that the report has been completed. Add "report" as a field containing the REPORT to be an additional payload to the notification.
`,
  expansive: `1. Send a notification of type "prompt_received" with description saying what PROMPT has been received, e.g. "Received research request: {PROMPT}"
2. Send a notification of type "prompt_analysis_started", with description indicating that we are now analyzing the research request.
3. Take the PROMPT and ask a language model to produce 2 topics that could be useful to investigate in order to produce the report requested in the PROMPT. The topics should be simple and sufficiently different from each other, e.g. "important events of 1972" or "energy consumption composition in India today". Instruct the model to return the topics on one line each. Tell the model not to output any other text. Then, parse the output of the language model line by line and save the resulting topics as "topics" for further research.
4. Send a notification of type "prompt_analysis_completed", with description saying as much.
5. Throughout the search and report generation process, we shall rely on a single storage of context. Lets refer to it just as to "context" from now on. Initially, there is no context.
6. For each topic in topics, perform the following
  6.1. Take the PROMPT and the topic, and ask a language model to produce up to 2 search phrases that could be useful to collect information on the particular topic. Each search phrase should be simple and directly relate to the topic e.g., for topic "important events of 1972", the search phrases could be "what happened in 1972", "1972 events worldwide", "important events 1971-1973". For topic "energy consumption composition in India today", the search phrases could be "renewable energy production in India today", "fossil fuel energy reliance India", "energy security India". Call the returned phrases simply "phrases" from now on.
  6.2. For each phrase in phrases output by step 6.1., perform the following:
    - Send a notification of type "search_started", with the description indicating what search phrase we are using for the search, e.g. "Searching for phrase '{phrase}'"
    - Perform search with the phrase. Once the search returns some results, append their contents to context one by one, separating them by double newlines from what is already present in the context.
    - Send a notification of type "search_result_processing_completed", indicating in its description that the search results for term {term} have been processed.
7. Send a notification with type "report_building", with the description indicating that the report is being built.
8. Take CONTEXT. Call the language model, instructing it to take context (to be appended into the LM call) and produce a deep research report on the topic requested in PROMPT. The resulting report should go into detail wherever possible, rely only on the information available in context, address the instruction given in the PROMPT, and be formatted in Markdown. This is to be communicated in the prompt. Do not shy away from using long, detailed and descriptive prompts! Tell the model not to output any other text, just the report. The result produced by the language model is to be called REPORT.
9. Send a notification with type "report_done", indicating that the report has been completed. Add "report" as a field containing the REPORT to be an additional payload to the notification.
`,
  intensive: `1. Send a notification of type "prompt_received" with description saying what PROMPT has been received, e.g. "Received research request: {PROMPT}"
2. Send a notification of type "prompt_analysis_started", with description indicating that we are now analyzing the research request.
3. Throughout the search and report generation process, we shall rely on two storages of context. One shall be called "supercontext" and contain all contexts of all resources read throughout the search phase. The other one shall be called "subcontext" and pertain to only one interation of the search process. At the beginning, both the supercontext and subcontext are empty.
4. Take the PROMPT and ask a language model to produce 2 search phrases that could help with retrieving results from search engine for the purpose of compiling a report the user asks for in the PROMPT. The search phrases should be simple and objective, e.g. "important events 1972" or "energy consumption composition in India today". Use a long prompt for the model that describes in detail what is supposed to be performed and the expected output format. Instruct the model to return the search phrases on one line each. Tell the model not to output any other text -- just the newline-separated phrases. Then, parse the output of the language model line by line and save the resulting search phrases as "phrases" for further research, skipping over empty lines.
4.1. Send a notification of type "prompt_analysis_completed", with a description saying as much.
5. Perform the following 2 times:
 - Clear the subcontext.
 - For each phrase in phrases, perform the following:
    * Send a notification of type "search_started", with the description indicating what search phrase we are using for the search, e.g. "Searching for phrase '{phrase}'"
    * Perform search with the phrase. Once the search returns some results, append their contents to subcontext one by one, separating them by double newlines from what is already present in the subcontext.
    * Send a notification of type "search_result_processing_completed", indicating in its description that the search results for term {term} have been processed.
 - Once the subcontext has been put together by aggregating the contributions due to all search phrases, ask a language model, given the subcontext and the PROMPT given by the user, to come up with 2 more phrases (distinct to phrases that are already in phrases) on the basis of the new subcontext being available. Again, the search phrases should be simple and objective, e.g. "important events 1972" or "energy consumption composition in India today". Use a long prompt for the model that describes in detail what is supposed to be performed and the expected output format. Instruct the model to return the search phrases on one line each. Tell the model not to output any other text -- just the newline-separated phrases. Then, parse the output of the language model line by line and save the resulting search phrases as "phrases" for further research, skipping over empty lines. Clear all the old phrases and let the newly returned phrases by the phrases for the next iteration of this loop.
6. Send a notification with type "report_building", with the description indicating that the report is being built.
7. Take CONTEXT. Call the language model, instructing it to take CONTEXT (to be appended into the LM call) and produce a deep research report on the topic requested in PROMPT. The resulting report should go into detail wherever possible, rely only on the information available in CONTEXT, address the instruction given in the PROMPT, and be formatted in Markdown. This is to be communicated in the prompt. Do not shy away from using long, detailed and descriptive prompts! Tell the model not to output any other text, just the report. The result produced by the language model is to be called REPORT.
8. Send a notification with type "report_done", indicating that the report has been completed. Add "report" as a field containing the REPORT to be an additional payload to the notification.
`,
}
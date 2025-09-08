# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Universal Deep Research Backend (UDR-B) - FastAPI Application

This module provides the main FastAPI application for the Universal Deep Research Backend,
offering intelligent research and reporting capabilities through streaming APIs.
"""

import asyncio
import json
import os
import random
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uvicorn.config import LOGGING_CONFIG

import items

# Import configuration
from config import get_config
from frame.clients import Client, HuggingFaceClient, OpenAIClient
from frame.harness4 import FrameConfigV4, FrameV4
from frame.trace import Trace
from scan_research import do_reporting as real_reporting
from scan_research import do_research as real_research
from scan_research import generate_session_key
from scan_research_dry import do_reporting as dry_reporting
from scan_research_dry import do_research as dry_research

# Get configuration
config = get_config()

app = FastAPI(
    title="Universal Deep Research Backend API",
    description="Intelligent research and reporting service using LLMs and web search",
    version="1.0.0",
)

# Configure logging
LOGGING_CONFIG["formatters"]["default"][
    "fmt"
] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.cors.frontend_url],  # Frontend URL from config
    allow_credentials=config.cors.allow_credentials,
    allow_methods=config.cors.allow_methods,
    allow_headers=config.cors.allow_headers,
)


class Message(BaseModel):
    text: str


class ResearchRequest(BaseModel):
    dry: bool = False
    session_key: Optional[str] = None
    start_from: str = "research"
    strategy_id: Optional[str] = None
    strategy_content: Optional[str] = None
    prompt: Optional[str] = None
    mock_directory: str = "mock_instances/stocks_24th_3_sections"


@app.get("/")
async def root():
    return {
        "message": "The Deep Research Backend is running. Use the /api/research endpoint to start a new research session."
    }


def build_events_path(session_key: str) -> str:
    return f"instances/{session_key}.events.jsonl"


def make_message(
    event: Dict[str, Any],
    session_key: str | None = None,
    timestamp_the_event: bool = True,
) -> str:
    if timestamp_the_event:
        event = {**event, "timestamp": datetime.now().isoformat()}

    if session_key:
        items.register_item(build_events_path(session_key), event)

    return json.dumps({"event": event, "session_key": session_key}) + "\n"


@app.post("/api/research")
async def start_research(request: ResearchRequest):
    """
    Start or continue a research process and stream the results using JSON streaming.
    
    This endpoint initiates a comprehensive research workflow that includes:
    - Query analysis and topic extraction
    - Web search using Tavily API
    - Content filtering and relevance scoring
    - Report generation using LLMs
    
    The response is streamed as Server-Sent Events (SSE) with real-time progress updates.
    
    Args:
        request (ResearchRequest): The research request containing:
            - dry (bool): Use mock data for testing (default: False)
            - session_key (str, optional): Existing session to continue
            - start_from (str): "research" or "reporting" phase
            - prompt (str): Research query (required for research phase)
            - mock_directory (str): Directory for mock data
    
    Returns:
        StreamingResponse: Server-Sent Events stream with research progress
        
    Raises:
        HTTPException: 400 if request parameters are invalid
        
    Example:
        ```bash
        curl -X POST http://localhost:8000/api/research \\
          -H "Content-Type: application/json" \\
          -d '{
            "prompt": "What are the latest developments in quantum computing?",
            "start_from": "research"
          }'
        ```
    """
    # Validate request parameters
    if request.start_from not in ["research", "reporting"]:
        raise HTTPException(
            status_code=400,
            detail="start_from must be either 'research' or 'reporting'",
        )

    if request.start_from == "reporting" and not request.session_key:
        raise HTTPException(
            status_code=400,
            detail="session_key is required when starting from reporting phase",
        )

    if request.start_from == "research" and not request.prompt:
        raise HTTPException(
            status_code=400,
            detail="prompt is required when starting from research phase",
        )

    # Use configured mock directory
    mock_dir = request.mock_directory or config.research.mock_directory

    # Choose implementation
    research_impl = (
        (lambda session_key, prompt: dry_research(session_key, prompt, mock_dir))
        if request.dry
        else real_research
    )
    reporting_impl = (
        (lambda session_key: dry_reporting(session_key, mock_dir))
        if request.dry
        else real_reporting
    )

    # Generate or use provided session key
    session_key = request.session_key or generate_session_key()

    # Prepare generators
    research_gen = (
        research_impl(session_key, request.prompt)
        if request.start_from == "research"
        else None
    )
    reporting_gen = reporting_impl(session_key)

    return StreamingResponse(
        stream_research_events(
            research_gen, reporting_gen, request.start_from == "research", session_key
        ),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Encoding": "none",
        },
    )


async def stream_research_events(
    research_fn: AsyncGenerator[Dict[str, Any], None],
    reporting_fn: AsyncGenerator[Dict[str, Any], None],
    do_research: bool,
    session_key: str,
) -> AsyncGenerator[str, None]:
    """
    Stream research or reporting events using JSON streaming format.

    Args:
        research_fn: Research phase generator
        reporting_fn: Reporting phase generator
        do_research: Whether to run research phase
        session_key: Session identifier

    Yields:
        JSON formatted event strings, one per line
    """
    try:
        yield make_message(
            {
                "type": "started",
                "description": "Waking up the Deep Research Backend",
            },
            session_key,
        )

        error_event_encountered: bool = False
        if do_research:
            async for event in research_fn:
                if event["type"] == "error":
                    error_event_encountered = True
                yield make_message(event, session_key)

        if not error_event_encountered:
            async for event in reporting_fn:
                yield make_message(event, session_key)

            # Send completion message
            yield make_message(
                {
                    "type": "completed",
                    "description": "Research and reporting completed",
                },
                session_key,
            )
    except asyncio.CancelledError:
        # Send cancellation message before propagating the exception
        yield make_message(
            {
                "type": "cancelled",
                "description": "Research was cancelled",
            },
            session_key,
        )
        raise


@app.post("/api/research2")
async def start_research2(request: ResearchRequest):
    # Validate request parameters
    if request.start_from not in ["research"]:
        raise HTTPException(status_code=400, detail="start_from must be 'research'")

    if request.start_from == "research" and not request.prompt:
        raise HTTPException(
            status_code=400,
            detail="prompt is required when starting from research phase",
        )

    # Generate or use provided session key
    session_key = generate_session_key()

    if request.strategy_id is None or request.strategy_id == "default":
        # Validate request parameters
        if request.start_from not in ["research", "reporting"]:
            raise HTTPException(
                status_code=400,
                detail="start_from must be either 'research' or 'reporting'",
            )

        if request.start_from == "reporting" and not request.session_key:
            raise HTTPException(
                status_code=400,
                detail="session_key is required when starting from reporting phase",
            )

        if request.start_from == "research" and not request.prompt:
            raise HTTPException(
                status_code=400,
                detail="prompt is required when starting from research phase",
            )

        # Choose implementation
        research_impl = (
            (
                lambda session_key, prompt: dry_research(
                    session_key, prompt, "mock_instances/stocks_24th_3_sections"
                )
            )
            if request.dry
            else real_research
        )
        reporting_impl = (
            (
                lambda session_key: dry_reporting(
                    session_key, "mock_instances/stocks_24th_3_sections"
                )
            )
            if request.dry
            else real_reporting
        )

        # Generate or use provided session key
        session_key = request.session_key or generate_session_key()

        # Prepare generators
        research_gen = (
            research_impl(session_key, request.prompt)
            if request.start_from == "research"
            else None
        )
        reporting_gen = reporting_impl(session_key)

        return StreamingResponse(
            stream_research_events(
                research_gen,
                reporting_gen,
                request.start_from == "research",
                session_key,
            ),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Encoding": "none",
            },
        )

    return StreamingResponse(
        stream_research2_events(
            session_key, request.prompt, request.strategy_id, request.strategy_content
        ),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Encoding": "none",
        },
    )


async def stream_research2_events(
    session_key: str, prompt: str, strategy_id: str, strategy_content: str
) -> AsyncGenerator[str, None]:
    try:
        yield make_message(
            {
                "type": "started",
                "description": "Waking up the Universal Deep Research Backend",
            },
            session_key,
        )

        # Set the random seed from configuration
        random.seed(config.research.random_seed)

        # Set trace filename using configuration
        comm_trace_timestamp: str = datetime.now().strftime("%Y%m%d_%H-%M-%S")
        comm_trace_filename = (
            f"{config.logging.log_dir}/comms_{comm_trace_timestamp}.log"
        )
        comm_trace = Trace(
            comm_trace_filename, copy_into_stdout=config.logging.copy_into_stdout
        )

        # Get the configured model settings
        from clients import MODEL_CONFIGS, DEFAULT_MODEL, get_api_key
        model_config = MODEL_CONFIGS[DEFAULT_MODEL]
        api_key = get_api_key(model_config["api_type"])
        
        client: Client = OpenAIClient(
            base_url=model_config["base_url"],
            model=model_config["completion_config"]["model"],
            api_key=api_key,
            trace=comm_trace,
        )

        frame_config = FrameConfigV4(
            long_context_cutoff=config.frame.long_context_cutoff,
            force_long_context=config.frame.force_long_context,
            max_iterations=config.frame.max_iterations,
            interaction_level=config.frame.interaction_level,
        )
        harness = FrameV4(
            client_profile=client,
            errand_profile={},
            compilation_trace=True,
            execution_trace="file_and_stdout",
        )

        messages = []
        preamble_files = [
            "frame/prompts/udr_minimal_generating/0.code_skill.py",
        ]
        for path in preamble_files:
            type = path.split(".")[-2]
            with open(path, "r") as f:
                messages.append(
                    {
                        "mid": len(messages),
                        "role": "user",
                        "content": f.read(),
                        "type": type,
                    }
                )

        messages.append(
            {
                "mid": len(messages),
                "role": "user",
                "content": "The following is the prompt data to be used in later procedures.\n\nPROMPT:\n"
                + prompt,
                "type": "data",
            }
        )

        messages.append(
            {
                "mid": len(messages),
                "role": "user",
                "content": strategy_content,
                "type": "generating_routine",
            }
        )

        for i in range(len(messages)):
            messages_so_far = messages[: i + 1]
            yield make_message(
                {
                    "type": "generic",
                    "description": "Processing agentic instructions: "
                    + str(i + 1)
                    + " of "
                    + str(len(messages)),
                },
                session_key,
            )
            for notification in harness.generate_with_notifications(
                messages=messages_so_far,
                frame_config=frame_config,
            ):
                yield make_message(notification, session_key)

        yield make_message(
            {
                "type": "completed",
                "description": "Research completed",
            },
            session_key,
        )
    except asyncio.CancelledError:
        # Send cancellation message before propagating the exception
        yield make_message(
            {
                "type": "cancelled",
                "description": "Research was cancelled",
            },
            session_key,
        )
        raise

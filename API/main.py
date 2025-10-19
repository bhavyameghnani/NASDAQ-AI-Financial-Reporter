import asyncio
import dotenv

dotenv.load_dotenv()

import os
import uuid
import json
from datetime import datetime, timezone

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

if not os.getenv('GOOGLE_API_KEY'):
    print("WARNING: GOOGLE_API_KEY not found in environment variables")
    print("Please add GOOGLE_API_KEY to your .env file")

from podcast.agent import root_agent, AINewsReport

# Initialize FastAPI app
app = FastAPI(
    title="AI News Podcast Generator API",
    description="Generate AI news podcasts using Google ADK",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---

class PodcastRequest(BaseModel):
    """Request to generate a podcast"""
    pass

class PodcastResponse(BaseModel):
    report: AINewsReport
    audio_file: str
    markdown_file: str
    status: str
    generated_at: str
    session_id: str

class HealthResponse(BaseModel):
    message: str
    status: str
    timestamp: str

# --- Helper Functions ---

async def generate_podcast_with_adk(session_id: str) -> AINewsReport:
    """Generate podcast using the ADK agent"""
    
    start_time = datetime.now(timezone.utc)

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="podcast_generation",
        session_service=session_service
    )

    await session_service.create_session(
        app_name="podcast_generation",
        user_id="api_user",
        session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text="Generate AI news podcast")])

    print(f"Starting ADK podcast generation for session: {session_id}")
    try:
        events = [
            event for event in runner.run(
                user_id="api_user",
                session_id=session_id,
                new_message=content,
            )
        ]

        print(f"Total events received: {len(events)}")
        
        # Find the final response event
        final_event = None
        for event in reversed(events):
            print(f"Event type: {type(event)}, has is_final_response: {hasattr(event, 'is_final_response')}")
            if hasattr(event, 'is_final_response') and event.is_final_response():
                final_event = event
                break
        
        if not final_event:
            # If no final response found, use the last event with content
            for event in reversed(events):
                if hasattr(event, 'content') and event.content and event.content.parts:
                    final_event = event
                    break

        if final_event and hasattr(final_event, 'content') and final_event.content and final_event.content.parts:
            print("Final response received from agent")
            response_text = final_event.content.parts[0].text
            print(f"Agent response length: {len(response_text)}")
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            print(f"ADK podcast generation completed ({duration:.1f}s)")
            
            # Create a podcast report object with the agent's response
            podcast_report = AINewsReport(
                title="AI Research Report",
                report_summary=response_text,
                stories=[]
            )
            return podcast_report
                
        else:
            error_msg = f"No valid final event found. Total events: {len(events)}"
            print(error_msg)
            raise Exception(error_msg)

    except Exception as e:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        print(f"ADK podcast generation failed - {e}")
        raise HTTPException(status_code=500, detail=f"Podcast generation failed: {e}")
    finally:
        print(f"Session cleanup for: {session_id}")
        session_service = None

# --- API Routes ---

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        message="AI News Podcast Generator API is running!",
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.post("/generate", response_model=PodcastResponse)
async def generate_podcast(request: PodcastRequest):
    """
    Generate AI news podcast
    
    - Searches for latest AI news
    - Compiles report
    - Generates podcast audio
    - Returns report with file references
    """
    session_id = f"podcast_{uuid.uuid4().hex[:8]}"
    
    print(f"Generating podcast for session: {session_id}")
    
    try:
        podcast_report = await generate_podcast_with_adk(session_id)
        
        audio_file = "ai_today_podcast.wav"
        markdown_file = "ai_research_report.md"
        
        return PodcastResponse(
            report=podcast_report,
            audio_file=audio_file,
            markdown_file=markdown_file,
            status="completed",
            generated_at=datetime.now(timezone.utc).isoformat(),
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating podcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Run Server ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5006)
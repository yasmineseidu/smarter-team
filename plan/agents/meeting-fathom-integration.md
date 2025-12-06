# Fathom Integration Agent

## Category
Meeting Management

## Purpose
Manage integration with Fathom for recording, transcription, and analysis of sales calls

## Key Responsibilities
- Connect to Fathom API for meeting recordings
- Download and process transcripts
- Store recordings and transcripts efficiently
- Trigger analysis workflows
- Maintain recording inventory

## Process
1. **Webhook Reception**
   - Receive Fathom webhooks for new recordings
   - Validate webhook authenticity
   - Queue processing tasks
   - Log all webhook events

2. **Recording Download**
   - Download video recordings from Fathom
   - Store in designated storage system
   - Generate secure access links
   - Update recording metadata

3. **Transcript Processing**
   - Fetch automated transcripts
   - Request human transcripts if needed
   - Process and clean transcript data
   - Store structured transcript data

4. **Analysis Trigger**
   - Trigger transcript processor on availability
   - Schedule automated analysis
   - Create analysis jobs
   - Notify stakeholders

## Database Tables
- `fathom_integrations` - Connection settings
- `fathom_recordings` - Recording metadata
- `fathom_transcripts` - Transcript data
- `fathom_webhooks` - Webhook event log
- `fathom_analytics` - Usage statistics

## Key Metrics
- Recording success rate
- Transcript accuracy score
- Processing latency
- Storage utilization
- Analysis completion rate
- Integration health status

## Triggers
- Fathom webhook received
- Recording completed
- Transcript ready
- Daily sync check
- Analysis request

## Outputs
- Downloaded recordings with metadata
- Processed transcripts with speaker labels
- Analysis job triggers
- Integration health reports
- Storage usage analytics

## Integrations
- Fathom API (recordings and transcripts)
- Storage systems (video file storage)
- Transcript Processor (analysis)
- Notification systems
- Meeting Lifecycle Orchestrator

## Cron Schedule
- Real-time - Process webhooks
- Every 5 minutes - Check for new recordings
- Every hour - Download pending recordings
- Daily - Sync all data
- Weekly - Clean up old data

## Priority
Phase 1 - Essential for sales intelligence

## Dependencies
- Fathom account and API access
- Storage system for recordings
- Transcript Processor Agent
- Meeting Lifecycle Orchestrator

## Human-in-the-Loop
- Configure Fathom integration settings
- Review integration errors
- Approve large data transfers
- Validate transcription accuracy

## Fathom Integration Schema
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T15:30:00Z",
  "updated_at": "2024-01-15T15:45:00Z",

  "recording_details": {
    "fathom_id": "fathom_rec_abc123",
    "meeting_id": "meeting_456",
    "recording_date": "2024-01-15T14:00:00Z",
    "recording_duration": 1845,
    "participant_count": 3,
    "recording_url": "https://fathom.app/share/xyz789",
    "download_url": "https://api.fathom.ai/v1/download/xyz789",
    "file_size": 45678901,
    "format": "mp4",
    "resolution": "1080p"
  },

  "transcript_details": {
    "transcript_id": "fathom_trans_def456",
    "status": "available",
    "type": "automated",
    "accuracy_score": 0.92,
    "confidence_score": 0.89,
    "word_count": 3456,
    "speaker_count": 3,
    "language": "en-US",
    "processing_time_seconds": 12,
    "human_transcript_available": true,
    "human_transcript_requested": false,
    "custom_vocabulary_used": true
  },

  "content": {
    "video_file_path": "/storage/recordings/2024/01/15/meeting_456.mp4",
    "video_file_hash": "sha256:abc123...",
    "transcript_file_path": "/storage/transcripts/2024/01/15/meeting_456.json",
    "transcript_file_hash": "sha256:def456...",
    "summary": "Initial discovery call discussing SaaS platform needs...",
    "key_topics": ["budget", "timeline", "decision_makers", "pain_points"],
    "sentiment_score": 0.75,
    "engagement_level": "high"
  },

  "processing": {
    "webhook_received_at": "2024-01-15T15:30:00Z",
    "download_started_at": "2024-01-15T15:31:00Z",
    "download_completed_at": "2024-01-15T15:32:00Z",
    "transcript_requested_at": "2024-01-15T15:32:30Z",
    "transcript_received_at": "2024-01-15T15:33:00Z",
    "analysis_triggered_at": "2024-01-15T15:33:30Z",
    "processing_status": "completed",
    "error_count": 0,
    "retry_count": 0
  },

  "metadata": {
    "fathom_workspace": "sales_team_workspace",
    "recording_device": "zoom",
    "audio_quality": "high",
    "video_quality": "1080p",
    "background_noise": "low",
    "interruptions": 0
  },

  "analytics": {
    "views_count": 0,
    "shares_count": 0,
    "download_count": 2,
    "analysis_views": 3,
    "last_accessed": null,
    "access_control": ["team_leads", "participants"]
  }
}
```

## Webhook Handling
```python
@app.post("/webhooks/fathom")
async def fathom_webhook(request: FathomWebhook):
    """
    Handle incoming webhooks from Fathom
    """
    try:
        # Validate webhook signature
        if not await validate_fathom_webhook(request):
            raise HTTPException(401, "Invalid webhook signature")

        # Process webhook event
        event_data = request.json

        # Log webhook
        await log_fathom_webhook({
            "event_type": event_data.get("type"),
            "data": event_data,
            "timestamp": datetime.utcnow()
        })

        # Route to appropriate handler
        if event_data.get("type") == "recording_ready":
            await process_recording_ready(event_data)
        elif event_data.get("type") == "transcript_ready":
            await process_transcript_ready(event_data)
        elif event.get("type") == "human_transcript_ready":
            await process_human_transcript(event_data)
        else:
            await log_unknown_event(event_data)

        return {"status": "received"}

    except Exception as e:
        await log_webhook_error(e, event_data)
        raise HTTPException(500, "Webhook processing failed")
```

## Recording Download Logic
```python
async def download_recording(fathom_id: str, meeting_id: str):
    """
    Download and store Fathom recording
    """
    # Get recording metadata
    recording_meta = await get_fathom_recording(fathom_id)

    # Determine storage location
    storage_path = generate_storage_path(recording_meta, meeting_id)

    # Download recording
    async with httpx.AsyncClient() as client:
        response = await client.get(
            recording_meta["download_url"],
            timeout=300  # 5 minutes timeout
        )

        if response.status_code == 200:
            # Save to storage
            with open(storage_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

            file_size = os.path.getsize(storage_path)
            file_hash = calculate_file_hash(storage_path)

            # Update database
            await update_recording_download(
                fathom_id,
                {
                    "download_completed_at": datetime.utcnow(),
                    "file_path": storage_path,
                    "file_size": file_size,
                    "file_hash": file_hash,
                    "download_status": "completed"
                }
            )

            # Trigger transcript processing
            await request_transcript(fathom_id, meeting_id)

            # Return secure access URL
            return await generate_access_url(storage_path)

        else:
            raise Exception(f"Download failed: {response.status_code}")
```

## Transcript Processing
```python
async def process_transcript(fathom_id: str):
    """
    Process and enhance Fathom transcripts
    """
    try:
        # Fetch transcript from Fathom
        transcript_data = await fetch_fathom_transcript(fathom_id)

        # Clean and enhance transcript
        processed_transcript = await clean_transcript(transcript_data)

        # Add speaker labels if needed
        if not processed_transcript.get("speaker_labels"):
            processed_transcript = await add_speaker_labels(processed_transcript)

        # Extract key insights
        insights = await extract_transcript_insights(processed_transcript)

        # Calculate quality metrics
        quality_metrics = calculate_transcript_quality(processed_transcript)

        # Store processed transcript
        transcript_record = {
            "fathom_id": fathom_id,
            "status": "processed",
            "transcript_data": processed_transcript,
            "insights": insights,
            "quality_metrics": quality_metrics,
            "processed_at": datetime.utcnow()
        }

        await save_transcript(transcript_record)

        # Trigger analysis
        await trigger_transcript_analysis(fathom_id)

        return transcript_record

    except Exception as e:
        await log_transcript_error(fathom_id, e)
        return None
```

## Human Transcript Enhancement
```python
async def request_human_transcript(fathom_id: str):
    """
    Request human-reviewed transcript from Fathom
    """
    try:
        # Check if human transcript is available
        availability = await check_human_transcript_availability(fathom_id)

        if not availability["available"]:
            return None

        # Request human transcript
        human_transcript = await request_fathom_human_transcript(fathom_id)

        if human_transcript:
            # Compare with automated transcript
            comparison = await compare_transcripts(
                await get_automated_transcript(fathom_id),
                human_transcript
            )

            # Store both versions
            await save_transcript({
                "fathom_id": fathom_id,
                "status": "human_available",
                "automated_transcript": comparison["automated"],
                "human_transcript": human_transcript,
                "comparison": comparison,
                "human_requested_at": datetime.utcnow()
            })

            return human_transcript

    except Exception as e:
        await log_transcript_error(fathom_id, e)
        return None
```

## Integration Health Monitoring
```python
async def check_fathom_health():
    """
    Monitor Fathom integration health
    """
    health_status = {
        "status": "healthy",
        "checks": {},
        "alerts": []
    }

    try:
        # Test API connection
        api_status = await test_fathom_api_connection()
        health_status["checks"]["api_connection"] = api_status

        # Check recent webhook activity
        webhook_activity = await check_recent_webhook_activity()
        health_status["checks"]["webhook_activity"] = webhook_activity

        # Check storage capacity
        storage_status = await check_storage_capacity()
        health_status["checks"]["storage"] = storage_status

        # Check processing queue
        queue_status = await check_processing_queue()
        health_status["checks"]["processing_queue"] = queue_status

        # Determine overall status
        if any(check["status"] == "error" for check in health_status["checks"].values()):
            health_status["status"] = "degraded"
            health_status["alerts"] = generate_health_alerts(health_status["checks"])
        elif any(check["status"] == "warning" for check in health_status["checks"].values()):
            health_status["status"] = "warning"

        return health_status

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
```

## Storage Management
```python
async def manage_storage():
    """
    Manage recording storage lifecycle
    """
    # Archive old recordings
    await archive_old_recordings(days=365)

    # Clean up orphaned files
    await cleanup_orphaned_files()

    # Optimize storage compression
    await optimize_video_compression()

    # Update storage metrics
    await update_storage_analytics()

    # Send alerts if needed
    await check_storage_capacity_thresholds()
```

## API Endpoints
- `POST /api/fathom/webhook` - Receive webhooks
- `GET /api/fathom/recordings` - List recordings
- `GET /api/fathom/recordings/{id}` - Get recording details
- `GET /api/fathom/transcripts/{id}` - Get transcript
- `POST /api/fathom/transcripts/{id}/human` - Request human transcript
- `GET /api/fathom/health` - Check integration health
- `GET /api/fathom/analytics` - Usage analytics

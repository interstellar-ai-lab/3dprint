# Asynchronous 3D Generation System

This document explains the new asynchronous 3D generation system that handles long-running Tripo API requests efficiently.

## Overview

The new system addresses the problem of long-running 3D generation requests (which can take several minutes) by implementing an asynchronous approach that:

- ✅ Returns immediately to the client
- ✅ Handles expensive computations safely
- ✅ Provides real-time status updates
- ✅ Survives request timeouts
- ✅ Allows for proper error handling and retries

## Database Schema Requirements

Before using the new system, ensure your `generated_images` table has the required columns. Run the SQL script in your Supabase SQL editor:

```sql
-- Run database_schema_update.sql in your Supabase SQL editor
```

Required columns:
- `status` (text): running, completed, failed, cancelled, timeout
- `task_id` (text): Tripo API task ID
- `created_at` (timestamp): record creation time
- `updated_at` (timestamp): last update time
- `error_message` (text): error details for failed jobs

## API Endpoints

### 1. Submit 3D Generation Job

**Endpoint:** `POST /api/generate-3d`

**Request Body:**
```json
{
  "sessionId": "your-session-id",
  "iteration": 1,
  "targetObject": "Golden Retriever",
  "imageUrl": "https://example.com/image.png"
}
```

**Response:**
```json
{
  "success": true,
  "record_id": 123,
  "status": "running",
  "status_url": "/api/status/123",
  "message": "3D generation job submitted successfully"
}
```

### 2. Check Job Status

**Endpoint:** `GET /api/generation-status/{record_id}`

**Response Examples:**

**Processing:**
```json
{
  "record_id": 123,
  "status": "running",
  "task_id": "tripo_task_abc123",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z",
  "target_object": "Golden Retriever",
  "iteration": 1
}
```

**Completed:**
```json
{
  "record_id": 123,
  "status": "completed",
  "task_id": "tripo_task_abc123",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:10:00Z",
  "target_object": "Golden Retriever",
  "iteration": 1,
  "3d_url": "https://supabase.com/storage/3d-model.glb",
  "image_url": "https://supabase.com/storage/image.png"
}
```

**Failed:**
```json
{
  "record_id": 123,
  "status": "failed",
  "task_id": "tripo_task_abc123",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:05:00Z",
  "target_object": "Golden Retriever",
  "iteration": 1,
  "error_message": "Tripo task failed: API error details"
}
```

## Status Values

The system handles all Tripo API status values:

### Ongoing Statuses:
- `queued`: Task is awaiting processing
- `running`: Task is currently processing

### Finalized Statuses:
- `success`: Task completed successfully
- `failed`: Task failed (report with task_id for support)
- `cancelled`: Task was cancelled
- `unknown`: Task status cannot be determined (system level issue)

## Frontend Integration

### 1. Submit Job and Poll Status

```javascript
// Submit the job
const response = await fetch('/api/generate-3d', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sessionId: 'your-session-id',
    iteration: 1,
    targetObject: 'Golden Retriever',
    imageUrl: 'https://example.com/image.png'
  })
});

const result = await response.json();

if (result.success) {
  // Start polling for status
  pollJobStatus(result.record_id);
}
```

### 2. Polling Function

```javascript
async function pollJobStatus(recordId) {
  const maxAttempts = 60; // 10 minutes
  let attempts = 0;
  
  const poll = async () => {
    try {
      const response = await fetch(`/api/generation-status/${recordId}`);
      const status = await response.json();
      
      switch (status.status) {
        case 'completed':
          console.log('✅ 3D model ready:', status.3d_url);
          // Handle success
          break;
          
        case 'failed':
        case 'cancelled':
        case 'timeout':
          console.error('❌ Job failed:', status.error_message);
          // Handle error
          break;
          
        case 'running':
          // Continue polling
          if (attempts < maxAttempts) {
            attempts++;
            setTimeout(poll, 10000); // Poll every 10 seconds
          } else {
            console.error('❌ Polling timeout');
          }
          break;
      }
    } catch (error) {
      console.error('Error polling status:', error);
    }
  };
  
  poll();
}
```

### 3. Real-time Updates with WebSocket (Optional)

For even better user experience, you can implement WebSocket updates:

```javascript
// Connect to WebSocket for real-time updates
const socket = io();

socket.on('job_completed', (data) => {
  if (data.record_id === currentRecordId) {
    console.log('✅ 3D model ready:', data.result.3d_url);
    // Update UI
  }
});

socket.on('job_failed', (data) => {
  if (data.record_id === currentRecordId) {
    console.error('❌ Job failed:', data.error);
    // Update UI
  }
});
```

## Error Handling

The system handles various error scenarios:

1. **API Errors**: Tripo API errors are captured and stored
2. **Network Timeouts**: Jobs timeout after 10 minutes of polling
3. **System Errors**: Unexpected errors are logged and status updated
4. **Database Errors**: Graceful handling when database is unavailable

## Monitoring and Logging

The system provides comprehensive logging:

- ✅ Job submission and task creation
- ✅ Status updates during processing
- ✅ Successful completions with URLs
- ✅ Error details for failed jobs
- ✅ Timeout handling

Check the application logs for detailed information about job processing.

## Benefits

1. **No Request Timeouts**: Clients don't experience HTTP timeouts
2. **Resource Efficiency**: Server resources aren't tied up in long requests
3. **Better UX**: Users get immediate feedback and can track progress
4. **Reliability**: Jobs continue processing even if client disconnects
5. **Scalability**: Multiple jobs can be processed concurrently
6. **Error Recovery**: Failed jobs are properly tracked and reported

## Migration from Old System

The old synchronous endpoint is still available for backward compatibility, but new implementations should use the asynchronous approach for better reliability and user experience.

# Multi-View Upload Feature Guide

## Overview

The Multi-View Upload feature allows users to upload their own 4-view images (front, left, back, right) and directly generate 3D models without the iterative AI generation process. This provides a faster, more direct path to 3D model creation when users already have the required multi-view images.

## Features

### 🎯 **Direct 3D Generation**
- Upload 4 orthogonal views of your 3D object
- Generate 3D models directly without AI iteration
- Faster processing time (typically 5-10 minutes)

### 🖼️ **Intuitive Upload Interface**
- 2x2 grid layout matching the image views
- Drag-and-drop functionality for easy file upload
- Real-time image previews
- Validation to ensure all views are uploaded

### 📊 **Real-time Status Tracking**
- Live progress updates during 3D generation
- Status polling every 5 seconds
- Clear error messages and retry options

### 📦 **Multiple Output Options**
- Download GLB files directly
- View 3D models online using 3D viewer
- Integration with existing Studio management

## How to Use

### 1. **Access the Feature**
- Navigate to the main demo page
- Click the "📤 Upload Multi-View" tab in the mode selector
- The interface will switch to the multi-view upload form

### 2. **Upload Your Images**
- **Front View**: Upload the front-facing image of your object
- **Left View**: Upload the left side view
- **Back View**: Upload the back-facing image
- **Right View**: Upload the right side view

### 3. **Image Requirements**
- **Format**: PNG, JPG, or JPEG
- **Quality**: Clear, well-lit images
- **Consistency**: All views should show the same object from different angles
- **Size**: Recommended 512x512 or larger (will be automatically resized)

### 4. **Generate 3D Model**
- Once all 4 views are uploaded, the "🚀 Generate 3D Model" button will become active
- Click to start the 3D generation process
- The system will upload your images and submit them to the Tripo 3D generation API

### 5. **Monitor Progress**
- Real-time status updates show generation progress
- Progress bar indicates current status
- Task ID and timestamps are displayed for reference

### 6. **Download Results**
- When generation completes, download options appear:
  - **📥 Download GLB**: Download the 3D model file
  - **👁️ View Online**: Open in online 3D viewer

## Technical Implementation

### Frontend Components

#### `MultiViewUploadForm.tsx`
- Main upload interface with 2x2 grid layout
- Drag-and-drop file handling
- Image preview and validation
- Form submission to backend API

#### `MultiViewStatusDisplay.tsx`
- Real-time status monitoring
- Progress visualization
- Download and view options
- Error handling and retry functionality

#### `DemoSection.tsx`
- Mode switching between AI generation and multi-view upload
- Integration of both workflows

### Backend API

#### `/api/upload-multiview` (POST)
- Accepts 4 image files (front, left, back, right)
- Validates file types and presence
- Uploads images to Supabase storage
- Creates database record for tracking
- Initiates background 3D generation process

#### Background Processing
- Downloads uploaded images from Supabase
- Converts to PIL Image objects
- Submits to Tripo API using `create_multiview_task`
- Polls for completion status
- Downloads and uploads final 3D model

### Database Integration
- Uses existing `generated_images` table
- Tracks upload sessions and generation status
- Stores 3D model URLs for download
- Maintains compatibility with existing Studio interface

## API Endpoints

### Upload Multi-View Images
```http
POST /api/upload-multiview
Content-Type: multipart/form-data

front: [image file]
left: [image file]
back: [image file]
right: [image file]
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "record_id": 123,
  "status": "running",
  "status_url": "/api/generation-status/123",
  "message": "Multi-view upload and 3D generation started successfully"
}
```

### Check Generation Status
```http
GET /api/generation-status/{record_id}
```

**Response:**
```json
{
  "status": "completed",
  "task_id": "tripo_task_id",
  "model_3d_url": "https://...",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

## Error Handling

### Common Issues
1. **Missing Views**: All 4 views must be uploaded
2. **Invalid File Types**: Only image files are accepted
3. **Upload Failures**: Network or storage issues
4. **Generation Timeout**: Process takes longer than expected
5. **API Errors**: Tripo API or processing failures

### Error Recovery
- Clear error messages with specific guidance
- Retry options for failed uploads
- Automatic retry for temporary failures
- Manual retry button for completed failures

## Integration with Existing System

### Studio Management
- Multi-view uploads appear in the Studio interface
- Same download and management capabilities
- Compatible with existing 3D viewer components

### Status Tracking
- Uses existing status polling mechanism
- Compatible with current session management
- Integrates with existing error handling

### File Management
- Leverages existing Supabase storage
- Uses same database schema
- Compatible with existing cleanup processes

## Performance Considerations

### Upload Optimization
- Client-side image validation
- Efficient file handling with FormData
- Progress indicators for large files

### Processing Efficiency
- Background processing to avoid blocking
- Efficient image conversion and handling
- Optimized polling intervals

### Storage Management
- Automatic cleanup of temporary files
- Efficient Supabase storage usage
- Proper file naming and organization

## Future Enhancements

### Planned Features
- **Batch Processing**: Upload multiple objects at once
- **Advanced Validation**: AI-powered image quality assessment
- **Custom View Angles**: Support for different view configurations
- **Progress Estimation**: More accurate time estimates
- **Preview Generation**: Real-time 3D preview during upload

### Technical Improvements
- **WebSocket Updates**: Real-time status updates
- **Resumable Uploads**: Handle large file uploads
- **Image Optimization**: Automatic image enhancement
- **Caching**: Faster repeated uploads

## Troubleshooting

### Upload Issues
- Ensure all 4 views are uploaded
- Check file formats (PNG, JPG, JPEG)
- Verify image quality and clarity
- Check network connection

### Generation Issues
- Monitor status updates for specific errors
- Check Tripo API availability
- Verify Supabase storage access
- Review server logs for detailed errors

### Download Issues
- Ensure generation completed successfully
- Check file permissions and access
- Verify 3D viewer compatibility
- Try alternative download methods

## Support

For issues or questions about the Multi-View Upload feature:
- Check the status display for specific error messages
- Review server logs for technical details
- Contact support with session IDs and error details
- Provide sample images for quality assessment

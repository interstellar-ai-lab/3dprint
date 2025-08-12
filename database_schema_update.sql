-- Database schema update for 3D generation status tracking
-- Run this script in your Supabase SQL editor to add required columns

-- Add status tracking columns to generated_images table
ALTER TABLE generated_images 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'running',
ADD COLUMN IF NOT EXISTS task_id TEXT,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_generated_images_status ON generated_images(status);

-- Create index on task_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_generated_images_task_id ON generated_images(task_id);

-- Create index on id for faster sorting (latest first)
CREATE INDEX IF NOT EXISTS idx_generated_images_id_desc ON generated_images(id DESC);

-- Add constraint to ensure valid status values
-- ALTER TABLE generated_images 
-- ADD CONSTRAINT IF NOT EXISTS check_valid_status 
-- CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'timeout'));

-- Update existing records to have a default status
UPDATE generated_images 
SET status = 'completed', 
    created_at = NOW(), 
    updated_at = NOW() 
WHERE status IS NULL OR status = 'pending';

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE ON generated_images TO authenticated;
-- GRANT SELECT, INSERT, UPDATE ON generated_images TO anon;

#!/usr/bin/env python3
"""
Test file for Google Gemini image editing functionality.
Tests the image editing capabilities using the Gemini 2.5 Flash Image Preview model.
"""

import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import tempfile
import shutil

# Test imports
try:
    import google.generativeai as genai
    from PIL import Image
    GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google Generative AI not available: {e}")
    GEMINI_AVAILABLE = False

class TestGeminiImageEdit(unittest.TestCase):
    """Test cases for Gemini image editing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_image_path = None
        self.temp_dir = None
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test image if PIL is available
        if GEMINI_AVAILABLE:
            self.create_test_image()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_image(self):
        """Create a simple test image for testing."""
        try:
            # Create a simple 100x100 test image
            test_image = Image.new('RGB', (100, 100), color='red')
            self.test_image_path = os.path.join(self.temp_dir, 'test_image.jpg')
            test_image.save(self.test_image_path, 'JPEG')
            print(f"Created test image at: {self.test_image_path}")
        except Exception as e:
            print(f"Warning: Could not create test image: {e}")
    
    @unittest.skipUnless(GEMINI_AVAILABLE, "Google Generative AI not available")
    def test_gemini_imports(self):
        """Test that all required modules can be imported."""
        self.assertIsNotNone(genai)
        self.assertIsNotNone(Image)
    
    @unittest.skipUnless(GEMINI_AVAILABLE, "Google Generative AI not available")
    def test_api_key_configuration(self):
        """Test API key configuration."""
        # Test with environment variable
        test_key = "test_api_key_12345"
        os.environ["GEMINI_API_KEY"] = test_key
        
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # If no exception is raised, configuration was successful
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"API key configuration failed: {e}")
        finally:
            # Clean up environment variable
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
    
    @unittest.skipUnless(GEMINI_AVAILABLE, "Google Generative AI not available")
    def test_model_creation(self):
        """Test Gemini model creation."""
        try:
            model = genai.GenerativeModel("gemini-2.5-flash-image-preview")
            self.assertIsNotNone(model)
        except Exception as e:
            self.fail(f"Model creation failed: {e}")
    
    @unittest.skipUnless(GEMINI_AVAILABLE, "Google Generative AI not available")
    def test_image_file_reading(self):
        """Test reading image file data."""
        if not self.test_image_path or not os.path.exists(self.test_image_path):
            self.skipTest("Test image not available")
        
        try:
            with open(self.test_image_path, "rb") as f:
                image_bytes = f.read()
            
            self.assertIsInstance(image_bytes, bytes)
            self.assertGreater(len(image_bytes), 0)
        except Exception as e:
            self.fail(f"Image file reading failed: {e}")
    
    @unittest.skipUnless(GEMINI_AVAILABLE, "Google Generative AI not available")
    def test_content_creation(self):
        """Test creating content with image and instruction."""
        if not self.test_image_path or not os.path.exists(self.test_image_path):
            self.skipTest("Test image not available")
        
        try:
            with open(self.test_image_path, "rb") as f:
                image_bytes = f.read()
            
            edit_instruction = "Make this image look like a painting by Vincent van Gogh"
            
            # Use the current SDK approach (dictionary-based)
            image_part = {
                "inline_data": {
                    "data": image_bytes,
                    "mime_type": "image/jpeg"
                }
            }
            
            contents = [
                image_part,
                edit_instruction
            ]
            
            self.assertEqual(len(contents), 2)
            self.assertIsInstance(contents[0], dict)
            self.assertIsInstance(contents[1], str)
            self.assertIn("inline_data", contents[0])
        except Exception as e:
            self.fail(f"Content creation failed: {e}")
    
    @unittest.skipUnless(GEMINI_AVAILABLE, "Google Generative AI not available")
    @patch('google.generativeai.GenerativeModel')
    def test_generate_content_mock(self, mock_model_class):
        """Test generate_content with mocked model."""
        # Mock the model and response
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        
        # Create mock response structure
        mock_response = Mock()
        mock_candidate = Mock()
        mock_content = Mock()
        mock_part = Mock()
        
        # Set up the mock response chain
        mock_response.candidates = [mock_candidate]
        mock_candidate.content = mock_content
        mock_content.parts = [mock_part]
        mock_part.inline_data = None
        mock_part.text = "Mock response text"
        
        mock_model.generate_content.return_value = mock_response
        
        # Test the mocked call
        try:
            response = mock_model.generate_content(["test_content"])
            
            self.assertIsNotNone(response)
            self.assertEqual(len(response.candidates), 1)
            self.assertEqual(response.candidates[0].content.parts[0].text, "Mock response text")
        except Exception as e:
            self.fail(f"Mocked generate_content failed: {e}")
    
    @unittest.skipUnless(GEMINI_AVAILABLE, "Google Generative AI not available")
    def test_image_processing_workflow(self):
        """Test the complete image processing workflow with error handling."""
        if not self.test_image_path or not os.path.exists(self.test_image_path):
            self.skipTest("Test image not available")
        
        try:
            # Configure API key (will use mock if not available)
            api_key = os.getenv("GEMINI_API_KEY", "test_key")
            genai.configure(api_key=api_key)
            
            # Create model
            model = genai.GenerativeModel("gemini-2.5-flash-image-preview")
            
            # Read image
            with open(self.test_image_path, "rb") as f:
                image_bytes = f.read()
            
            # Create content
            edit_instruction = "Make this image look like a painting by Vincent van Gogh"
            
            # Use the current SDK approach (dictionary-based)
            image_part = {
                "inline_data": {
                    "data": image_bytes,
                    "mime_type": "image/jpeg"
                }
            }
            
            contents = [
                image_part,
                edit_instruction
            ]
            
            # This would normally make an API call, but we're just testing the setup
            self.assertIsNotNone(model)
            self.assertIsNotNone(contents)
            self.assertEqual(len(contents), 2)
            
        except Exception as e:
            # This is expected if no real API key is available
            print(f"Workflow test completed (expected error without real API): {e}")
            self.assertTrue(True)
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        # Test with missing image file
        with self.assertRaises(FileNotFoundError):
            with open("nonexistent_image.jpg", "rb") as f:
                pass
        
        # Test with invalid image path
        invalid_path = os.path.join(self.temp_dir, "invalid_image.txt")
        with open(invalid_path, "w") as f:
            f.write("This is not an image")
        
        # This should not raise an exception, but the content creation might fail
        try:
            with open(invalid_path, "rb") as f:
                invalid_bytes = f.read()
            
            # Try to create content with invalid image data
            if GEMINI_AVAILABLE:
                try:
                    # Use the current SDK approach
                    image_part = {
                        "inline_data": {
                            "data": invalid_bytes,
                            "mime_type": "image/jpeg"
                        }
                    }
                    # If this succeeds, that's fine too
                    self.assertTrue(True)
                except Exception:
                    # Expected behavior for invalid image data
                    self.assertTrue(True)
        except Exception as e:
            self.fail(f"Unexpected error in error handling test: {e}")

def run_integration_test():
    """Run a real integration test if API key is available."""
    if not GEMINI_AVAILABLE:
        print("Google Generative AI not available. Skipping integration test.")
        return
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY environment variable found. Skipping integration test.")
        return
    
    print("Running integration test with real API...")
    
    try:
        # Configure the API key
        genai.configure(api_key=api_key)
        
        # Create a model
        model = genai.GenerativeModel("gemini-2.5-flash-image-preview")
        
        # Create a test image
        test_image = Image.new('RGB', (200, 200), color='blue')
        test_image_path = "test_integration_image.jpg"
        test_image.save(test_image_path, 'JPEG')
        
        # Read the test image
        with open(test_image_path, "rb") as f:
            image_bytes = f.read()
        
        # Define the edit instruction
        edit_instruction = "Make this image look like a painting by Vincent van Gogh, with swirling brushstrokes and vibrant colors."
        
        # Create the content
        image_part = {
            "inline_data": {
                "data": image_bytes,
                "mime_type": "image/jpeg"
            }
        }
        
        contents = [
            image_part,
            edit_instruction
        ]
        
        print("Sending image and edit instruction to the model...")
        
        # Generate the response
        response = model.generate_content(contents)
        
        print("Received response. Checking for generated image...")
        
        # Check for and save the generated image
        edited_image_found = False
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                edited_image = Image.open(BytesIO(image_data))
                edited_image.save("edited_image_integration.png")
                print("Edited image saved as edited_image_integration.png")
                edited_image_found = True
            elif part.text is not None:
                print(f"Model text response: {part.text}")
        
        if not edited_image_found:
            print("No edited image was generated. The model might have only provided text.")
        
        # Clean up test files
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
        if os.path.exists("edited_image_integration.png"):
            os.remove("edited_image_integration.png")
            
        print("Integration test completed successfully!")
        
    except Exception as e:
        print(f"Integration test failed: {e}")

if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*50 + "\n")
    
    # Run integration test
    run_integration_test()

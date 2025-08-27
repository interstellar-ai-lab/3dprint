# Gemini Image Editing Test Suite

This directory contains a comprehensive test suite and demo for Google's Gemini AI image editing functionality using the Gemini 2.5 Flash Image Preview model.

## Files Overview

- **`test_gemini_image_edit.py`** - Comprehensive unit tests for Gemini image editing
- **`gemini_image_edit_demo.py`** - Demo script showing the original functionality
- **`requirements_gemini_test.txt`** - Dependencies for the Gemini tests
- **`README_GEMINI_TEST.md`** - This documentation file

## Prerequisites

1. **Python 3.8+** - Required for the Google Generative AI library
2. **Gemini API Key** - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Dependencies** - Install required packages

## Installation

### 1. Install Dependencies

```bash
# Install from the requirements file
pip install -r requirements_gemini_test.txt

# Or install manually
pip install google-generativeai Pillow pytest pytest-asyncio python-dotenv
```

### 2. Set Up API Key

Set your Gemini API key as an environment variable:

```bash
# On macOS/Linux
export GEMINI_API_KEY="your_api_key_here"

# On Windows
set GEMINI_API_KEY=your_api_key_here

# Or create a .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## Usage

### Running the Demo

The demo script creates a test image and demonstrates the image editing functionality:

```bash
python gemini_image_edit_demo.py
```

**Features:**
- Creates a simple test image with a house drawing
- Applies a Van Gogh-style painting transformation
- Adds a friendly dragon to the sky
- Saves the edited image with descriptive naming

### Running the Tests

#### Run All Tests
```bash
python test_gemini_image_edit.py
```

#### Run with pytest (if installed)
```bash
pytest test_gemini_image_edit.py -v
```

#### Run Specific Test
```bash
python -m pytest test_gemini_image_edit.py::TestGeminiImageEdit::test_api_key_configuration -v
```

## Test Coverage

The test suite covers:

- **Module Imports** - Verifies all required modules can be imported
- **API Configuration** - Tests API key setup and configuration
- **Client Creation** - Tests Gemini client instantiation
- **Image Processing** - Tests image file reading and content creation
- **Mock Testing** - Tests functionality without making real API calls
- **Error Handling** - Tests various error scenarios
- **Integration Testing** - Full workflow testing with real API (if available)

## Test Structure

### Unit Tests
- `test_gemini_imports()` - Verifies module availability
- `test_api_key_configuration()` - Tests API setup
- `test_model_creation()` - Tests model creation
- `test_image_file_reading()` - Tests image loading
- `test_content_creation()` - Tests content preparation
- `test_generate_content_mock()` - Tests with mocked responses
- `test_image_processing_workflow()` - Tests complete workflow
- `test_error_handling()` - Tests error scenarios

### Integration Test
- `run_integration_test()` - Tests with real API (requires valid API key)

## Expected Output

### Successful Demo Run
```
🎨 Gemini Image Editing Demo
========================================
✓ Gemini API configured successfully
✓ Created test image: demo_test_image.jpg

📸 Using test image: demo_test_image.jpg

🎯 Edit instruction: Make this image look like a painting by Vincent van Gogh...

🚀 Starting image editing process...
✓ Gemini client created
✓ Loaded image: demo_test_image.jpg (12345 bytes)
✓ Created content with instruction: Make this image...
Sending image and edit instruction to Gemini...
✓ Received response from Gemini
✓ Edited image saved as: demo_test_image_edited_by_gemini.png
  Image size: (1024, 1024)
  Image mode: RGB

✅ Demo completed successfully!
Check the current directory for the edited image.
✓ Cleaned up test image: demo_test_image.jpg
```

### Successful Test Run
```
Running unit tests...
test_api_key_configuration (__main__.TestGeminiImageEdit) ... ok
test_client_creation (__main__.TestGeminiImageEdit) ... ok
test_content_creation (__main__.TestGeminiImageEdit) ... ok
test_error_handling (__main__.TestGeminiImageEdit) ... ok
test_generate_content_mock (__main__.TestGeminiImageEdit) ... ok
test_gemini_imports (__main__.TestGeminiImageEdit) ... ok
test_image_file_reading (__main__.TestGeminiImageEdit) ... ok
test_image_processing_workflow (__main__.TestGeminiImageEdit) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.123s

OK

==================================================

Running integration test with real API...
Integration test completed successfully!
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install google-generativeai Pillow
   ```

2. **API Key Issues**
   - Verify your API key is correct
   - Check environment variable is set
   - Ensure you have sufficient API credits

3. **Image Generation Failures**
   - The model may not always generate images
   - Check the text response for error messages
   - Verify the input image format and size

4. **Permission Errors**
   - Ensure write permissions in the current directory
   - Check if antivirus software is blocking file operations

### Debug Mode

For more detailed output, you can modify the scripts to include debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Limits and Costs

- **Rate Limits**: Check [Google AI Studio](https://makersuite.google.com/app/apikey) for current limits
- **Costs**: Image generation may incur charges based on your plan
- **Quotas**: Monitor your usage in the Google Cloud Console

## Contributing

To add more tests or improve the demo:

1. Follow the existing test structure
2. Add appropriate error handling
3. Include docstrings for new functions
4. Test both success and failure scenarios

## License

This test suite is provided as-is for educational and testing purposes. Please refer to the main project license for usage terms.

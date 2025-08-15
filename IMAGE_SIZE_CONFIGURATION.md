# Image Size Configuration

## Overview

The application now supports configurable image sizes for GPT-Image-1 generation. This allows you to choose the best aspect ratio for your specific objects to avoid cutting off important details.

## Supported Image Sizes

GPT-Image-1 supports three image sizes:

| Size | Format | Best For | Use Case |
|------|--------|----------|----------|
| `1024x1536` | Portrait | Tall objects | Default choice, good for most objects to avoid cutting off |
| `1024x1024` | Square | Most objects | Good for objects with similar width and height |
| `1536x1024` | Landscape | Wide objects | Cars, furniture, animals, laptops, tables, etc. |

## Configuration Options

### 1. Environment Variable (Backend)

Set the default image size in your `.env` file:

```env
DEFAULT_IMAGE_SIZE=1024x1536
```

### 2. Frontend Selection (User Interface)

Users can now select the image size from the generation form:

- **Portrait (1024×1536)**: Better for tall objects (default)
- **Square (1024×1024)**: Good for most objects
- **Landscape (1536×1024)**: Better for wide objects

### 3. API Parameter

You can also specify the image size directly in API calls:

```json
{
  "target_object": "Golden Retriever",
  "mode": "quick",
  "image_size": "1024x1536"
}
```

## API Endpoints

### Get Supported Image Sizes

```http
GET /api/image-sizes
```

Response:
```json
{
  "supported_sizes": ["1024x1024", "1024x1536", "1536x1024"],
  "default_size": "1024x1536",
  "descriptions": {
    "1024x1024": "Square format - good for objects with similar width and height",
    "1024x1536": "Portrait format - better for tall objects (e.g., people, buildings, trees)",
    "1536x1024": "Landscape format - better for wide objects (e.g., cars, furniture, animals)"
  }
}
```
```

## When to Use Different Sizes

### Use Square (1024×1024) for:
- Coffee mugs, cups, bowls
- Balls, spheres, cubes
- Small objects with similar dimensions
- Objects that fit well in a square format

### Use Portrait (1024×1536) for:
- People, human figures
- Buildings, skyscrapers
- Trees, plants, flowers
- Bottles, vases, tall containers
- Any object that is significantly taller than it is wide

### Use Landscape (1536×1024) for:
- Cars, vehicles
- Furniture (tables, chairs, sofas)
- Animals (dogs, cats, horses)
- Laptops, computers
- Any object that is significantly wider than it is tall

## Implementation Details

### Backend Changes

1. **Environment Variable Support**: Added `DEFAULT_IMAGE_SIZE` environment variable
2. **API Validation**: Added validation for supported image sizes
3. **Session Storage**: Image size is stored with each generation session
4. **Function Parameters**: Updated generation functions to accept image size parameter

### Frontend Changes

1. **UI Component**: Added image size selection dropdown
2. **TypeScript Types**: Updated `GenerationRequest` interface
3. **API Integration**: Modified generation API calls to include image size
4. **User Guidance**: Added helpful descriptions for each size option

## Migration Notes

- Existing sessions will use the default image size (1024×1024)
- New sessions will respect the selected image size
- The feature is backward compatible with existing code

## Troubleshooting

### Common Issues

1. **Invalid Image Size Error**: Ensure you're using one of the supported sizes
2. **API Errors**: Check that the image size parameter is being sent correctly
3. **Frontend Issues**: Verify that the TypeScript types are updated

### Validation

The backend validates image sizes against the supported list:
```python
SUPPORTED_IMAGE_SIZES = ["1024x1024", "1024x1536", "1536x1024"]
```

If an invalid size is provided, the API will return a 400 error with the list of supported sizes.

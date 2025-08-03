# 3D Generation Multi-Agent System

A sophisticated multi-agent system for generating 3D CAD models using AI agents. This project implements an iterative workflow that combines image generation, metadata analysis, and evaluation to create high-quality 3D models.

## Features

- 🤖 **Multi-Agent Architecture**: Uses specialized agents for generation and evaluation
- 🎨 **Image Generation**: Creates multi-view images using DALL-E
- 📊 **Metadata Generation**: Produces detailed metadata for 3D CAD reconstruction
- 🔄 **Iterative Improvement**: Continuously refines results based on evaluation feedback

- ⚡ **Multi-API Support**: Test different AI providers (OpenAI, Claude, DeepSeek, Qwen)

## Architecture

### Agents

1. **Generation Agent**: Creates multi-view images and metadata for 3D CAD reconstruction
2. **Evaluation Agent**: Assesses quality and provides improvement suggestions
3. **Mesh Generation Agent**: Converts results into 3D mesh data

### Workflow

1. User provides a query describing the desired 3D object
2. Generation agent creates multi-view images and metadata
3. Evaluation agent assesses quality and provides feedback
4. System iteratively improves results until quality threshold is met
5. Final 3D mesh is generated

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd openai-agents-python
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys:**
   Edit `multiagent.py` and add your API keys:
   ```python
   OPENAI_API_KEY = "your_openai_key"
   CLAUDE_API_KEY = "your_claude_key"
   DEEPSEEK_API_KEY = "your_deepseek_key"
   QWEN_API_KEY = "your_qwen_key"
   ```

## Usage

### Command Line Interface

Run the main script:
```bash
python multiagent.py
```

The system will:
- Ask for your desired 3D object
- Let you choose which AI model to use
- Generate and iteratively improve results
- Save outputs to organized directories



## API Testing

The system supports multiple AI providers for speed and quality testing:

- **OpenAI GPT-4o**: Fast and reliable
- **Claude 3 Sonnet**: High-quality reasoning
- **DeepSeek**: Cost-effective alternative
- **Qwen**: Alibaba's AI model

Switch between models by changing `CURRENT_MODEL` in `multiagent.py` or use the interactive selection.

## Output Structure

```
project/
├── renders/                    # Generated images
├── evaluation_reports_*/       # Evaluation reports per iteration
├── mesh_outputs/              # Final 3D mesh data
└── webapp/                    # Web interface
```

## Configuration

### Model Selection
```python
CURRENT_MODEL = "claude"  # Options: "openai", "claude", "deepseek", "qwen"
```

### Quality Thresholds
```python
# In evaluation agent
if all scores > 6.5:
    suggestions = "well done"
```

## Development

### Adding New AI Providers

1. Add API key to the configuration
2. Create client with appropriate base URL
3. Add to `MODEL_CONFIGS` dictionary
4. Test with `switch_model()` function

### Customizing Prompts

Edit the prompts in:
- `generation_agent()` function
- `PROMPT` variable for evaluation agent
- `generate_mesh_image()` function

## Troubleshooting

- **API Errors**: Check your API keys and quotas
- **Import Errors**: Ensure all dependencies are installed
- **Memory Issues**: Reduce image resolution in generation
- **Slow Performance**: Try different AI providers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on OpenAI's agents framework
- Uses DALL-E for image generation
- Inspired by modern multi-agent architectures

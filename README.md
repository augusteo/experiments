# Experiments

Code experiments accompanying blog posts at [augusteo.com](https://augusteo.com).

## Experiments

| Experiment | Blog Post |
|------------|-----------|
| gemini-3-flash-agentic-vision | [Gemini Stops Hallucinating When You Give It Python](https://augusteo.com/blog/til-gemini-agentic-vision) |

## Experiment Structure

Each experiment gets its own folder:

```
experiments/
└── [experiment-name]/
    ├── code/           # Python scripts
    ├── inputs/         # Test images/data
    ├── outputs/        # API responses, screenshots
    └── .env            # API keys (gitignored)
```

## API Keys

Each experiment's `.env` file should contain required API keys. See `.env.example` files in each experiment folder for the required variables. These `.env` files are gitignored.

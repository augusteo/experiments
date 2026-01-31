# Experiments

Code experiments accompanying blog posts at [augusteo.com](https://augusteo.com).

## Experiments

| Experiment | Blog Post |
|------------|-----------|
| gemini-3-flash-agentic-vision | [Gemini Stops Hallucinating When You Give It Python](https://augusteo.com/blog/til-gemini-agentic-vision) |
| claude-hooks-npm-blocker | [How I Made Claude Code Physically Incapable of Using npm](https://augusteo.com/blog/enforcing-bun-with-hooks) |

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

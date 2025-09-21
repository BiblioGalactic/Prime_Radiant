# 🤖 Local-CROS: Cross-Referential Optimization System

## Description

**Local-CROS** is an advanced cross-evaluation system for local LLaMA models that allows comparing responses between multiple models and generating optimized responses through intelligent synthesis. The system implements a unique mutual evaluation approach where each model evaluates the responses of all others.

## Key Features

### 🔄 Cross-Evaluation
- **Mutual evaluation**: Each model evaluates responses from all others
- **Multiple perspectives**: Get different approaches to the same question
- **Automatic scoring**: Automatic scoring system for each response
- **Complete history**: Detailed record of all interactions

### 🎯 Intelligent Synthesis
- **Automatic content type detection**: Code, lists, poetry, dialogues, etc.
- **Optimized combination**: Merges the best parts of each response
- **Redundancy elimination**: Avoids repeated information
- **Contextual recommendations**: Specific suggestions based on content type

### 📊 Incremental File System
- **Automatic numbering**: `model1.txt`, `model2.txt`, etc.
- **Cumulative history**: All executions in a central file
- **Detailed timestamps**: Temporal record of each operation
- **Complete traceability**: Tracking of all evolution

## System Requirements

- **llama.cpp** compiled and functional
- **2-4 GGUF models** compatible
- **Bash 4.0+**
- **Basic tools**: `find`, `sed`, `sort`, `jq` (optional)
- **Operating System**: macOS, Linux

## Installation

### 1. Download
```bash
# Clone repository
git clone https://github.com/your-user/local-cros.git
cd local-cros

# Make executable
chmod +x local-cros.sh
```

### 2. First Setup
```bash
# Run for first time (interactive configuration)
./local-cros.sh
```

The script will ask for:
- **llama-cli path**: Location of llama.cpp binary
- **Work directory**: Where to save results
- **Model configuration**: Name and path of each model (2-4 models)

### 3. Generated Configuration File
```bash
# local-cros.conf
LLAMA_CLI_PATH="/path/to/llama-cli"
WORK_DIR="./results"

MODEL_1_NAME="mistral"
MODEL_1_PATH="/path/to/mistral.gguf"

MODEL_2_NAME="llama"
MODEL_2_PATH="/path/to/llama.gguf"
# ... etc
```

## Usage

### Interactive Mode
```bash
./local-cros.sh
What do you need?
> Write an epic poem about Python programming
```

### Direct Command Mode
```bash
./local-cros.sh "Explain the differences between React and Vue.js"
```

### Example Output
```
🤖 Starting model comparison for: "Explain functional programming"

==> Consulting mistral...
[mistral] says: Functional programming is a paradigm...
---

==> Consulting llama...
[llama] says: In functional programming, functions are...
---

=== CROSS-EVALUATION BETWEEN MODELS ===
=== EVALUATION WITH MISTRAL ===
Evaluating llama: The response is precise and well-structured...

=== COMBINING BEST RESPONSES ===
💻 Combined response generated and saved!
📋 Complete history in: ./results/complete_history.txt
```

## Generated File Structure

```
results/
├── responses/
│   ├── mistral1.txt, mistral2.txt, mistral3.txt...
│   ├── llama1.txt, llama2.txt, llama3.txt...
│   ├── codellama1.txt, codellama2.txt...
│   └── response_combined_final.txt
└── complete_history.txt
```

## Advanced Features

### Automatic Content Type Detection

The system automatically detects content type and optimizes according to context:

- **Code**: `python`, `javascript`, `bash`, `c++`
- **Lists**: Step-by-step instructions
- **Poetry**: Haikus, verses, stanzas
- **Dialogues**: Conversations, scripts
- **General text**: Explanations, essays

### Evaluation System

Each model evaluates responses using specific criteria:
- **Technical accuracy**
- **Clarity of explanation**
- **Response completeness**
- **Context relevance**

### Contextual Recommendations

```bash
# For code
💻 Recommendation: Run 'python3 final_response.py' to test

# For lists
📋 Recommendation: Save as PDF or share as instructions

# For poetry
🎭 Recommendation: Perfect for literary analysis

# For dialogues
🎬 Recommendation: Ideal for scripts or role-playing
```

## Advanced Configuration

### Model Parameters
```bash
# Edit local-cros.sh to adjust parameters
-n 200           # Maximum number of tokens
--temp 0.7       # Temperature (creativity)
--top-k 40       # Top-k sampling
--top-p 0.9      # Top-p sampling
--repeat-penalty 1.1  # Repetition penalty
```

### Evaluation Customization
```bash
# Modify evaluation prompt in evaluate_response() function
local evaluation_prompt="Evaluate this response using these criteria..."
```

## Use Cases

### 1. Software Development
```bash
./local-cros.sh "Optimize this bubble sort algorithm"
# Get multiple optimization approaches
```

### 2. Creative Writing
```bash
./local-cros.sh "Write a dialogue between Socrates and Steve Jobs about ethics"
# Combine different narrative styles
```

### 3. Technical Analysis
```bash
./local-cros.sh "Explain advantages and disadvantages of microservices"
# Multiple combined technical perspectives
```

### 4. Problem Solving
```bash
./local-cros.sh "How to debug a memory leak in C++"
# Different debugging approaches
```

## Metrics and Analysis

### Complete History
The `complete_history.txt` file contains:
```
#=== EXECUTION 2025-01-21 15:30:15 ===
MODEL: mistral1
QUESTION: What is machine learning?
RESPONSE: Machine learning is a branch of AI...

#=== EVALUATION 2025-01-21 15:30:45 ===
EVALUATOR: llama
EVALUATING: Machine learning is a branch...
RESULT: Precise and well-structured response...

#=== COMBINED RESPONSE 2025-01-21 15:31:00 ===
TYPE: general_text
COMBINATION: Machine learning is a discipline...
```

### Trend Analysis
```bash
# Count responses per model
grep -c "MODEL:" results/complete_history.txt

# View temporal evolution
grep "EXECUTION" results/complete_history.txt | tail -10
```

## Troubleshooting

### Error: "llama-cli not found"
```bash
# Verify installation
which llama-cli

# Update configuration
vim local-cros.conf
```

### Error: "Model execution failed"
```bash
# Verify model
ls -la /path/to/your/model.gguf

# Test manually
/path/to/llama-cli -m /path/to/model.gguf -p "test"
```

### Low Quality Responses
```bash
# Adjust parameters in script
--temp 0.5        # Less creativity, more precision
-n 500            # More tokens for complete responses
```

## Extensions and Plugins

### Adding New Model
1. Edit `local-cros.conf`
2. Add `MODEL_N_NAME` and `MODEL_N_PATH`
3. Restart script

### Integration with External APIs
```bash
# Example: integrate with Claude API for external evaluation
curl -X POST "https://api.anthropic.com/v1/messages" \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-3-sonnet", "messages": [...]}'
```

## Contributing

1. Fork the repository
2. Create branch: `git checkout -b feature/new-functionality`
3. Commit: `git commit -am 'Add functionality X'`
4. Push: `git push origin feature/new-functionality`
5. Pull Request

## License

MIT License

## Author

**Gustavo Silva da Costa**

## Version

**1.0.0** - Cross-evaluation system and intelligent synthesis

---

*Local-CROS: Where multiple artificial minds collaborate to generate superior responses.*

# NexusAI

NexusAI is a framework that leverages large language models (LLMs) to manage and integrate various AI models from the Hugging Face community to solve complex AI tasks. By using LLaMA-3 8B for task planning, model selection, execution of subtasks, and summarizing results, NexusAI addresses tasks across multiple domains like language, vision, and speech.

## Key Features

- **Task Planning:** Decomposes user requests into manageable tasks and plans the execution by identifying appropriate models.
- **Model Selection:** Selects models based on their descriptions available on Hugging Face.
- **Task Execution:** Executes tasks using the selected models.
- **Result Integration:** Summarizes and integrates the outputs from different models to generate a cohesive response.

## Process Flow

1. **User Request Analysis:** LLaMA-3 8B receives and analyzes the user request.
2. **Decomposition into Subtasks:** The request is broken down into smaller tasks.
3. **Model Selection:** Models from Hugging Face are selected to perform these tasks.
4. **Task Execution:** Each subtask is executed by the chosen model.
5. **Response Generation:** LLaMA-3 8B integrates the results from all subtasks to form a final response.

## Example Workflow

For a user query like "In image /exp2.jpg, what is the animal and what is it doing?", NexusAI might:
1. Convert image to text.
2. Perform image classification.
3. Detect objects in the image.
4. Answer the question based on the detected objects and classifications.

## Experimentation and Results

- NexusAI has been tested on various simple and complex tasks.
- It integrates hundreds of models from Hugging Face, covering 24 different tasks including text classification, object detection, semantic segmentation, and more.
- Demonstrated capabilities in processing multimodal information and solving intricate AI tasks.

## Limitations

1. **Efficiency and Latency:** Interaction with LLMs for each stage adds to the processing time.
2. **Context-Length Limitation:** The maximum number of tokens an LLM can handle imposes constraints.
3. **System Stability:** Occasional failures in following instructions or model failures can affect reliability.

NexusAI represents a significant advancement in leveraging LLMs to orchestrate a variety of specialized AI models for comprehensive task-solving, despite some inherent challenges related to efficiency and stability.

## Installation

To install and set up NexusAI, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/nexusai.git
   cd NexusAI

2. **Install dependencies:**

```bash
pip install -r backend/NexusAI/requirements.txt
```
3. **Run the application:**
a. **Run the Backend**
```bash
cd backend/NexusAI
```
```
python main.py
```
b.**Run the Frontend**
```
cd frontEnd/NexusFrontEnd
npm run dev
```

4.**Usage**
To use NexusAI, send a request in the following format:

```json

{
  "request": "In image /exp2.jpg, what is the animal and what is it doing?"
}
```
The response will be a structured answer based on the analysis and integration of results from various AI models.

Contributing
Contributions are welcome! Please open an issue or submit a pull request for any changes.

License
This project is licensed under the MIT License. See the LICENSE file for details.


Feel free to customize the installation and usage sections based on your specific project set

# TalentScout Hiring Assistant

TalentScout Hiring Assistant is an AI-powered screening chatbot for a technology recruitment workflow. It runs as a Streamlit application, collects core candidate details in conversation, generates technical interview questions from the candidate's stated tech stack, and saves structured candidate records locally as JSON Lines for later review.

## Project Overview

The chatbot is designed to simulate an initial recruiter-led screening round. Instead of using a rigid form, it guides the candidate through a conversational flow:

1. Greets the candidate and explains the interview flow.
2. Collects core screening details one item at a time.
3. Uses the candidate's tech stack and experience level to generate tailored technical questions.
4. Accepts candidate responses without scoring them inline.
5. Detects exit intent, closes the session gracefully, and saves extracted candidate details.

### Current capabilities

- Conversational screening via Streamlit chat UI
- Candidate profile collection:
  name, email, phone, years of experience, desired role, location, tech stack
- Technical question generation based on declared technologies
- Structured candidate information extraction from chat transcripts
- Local persistence to `candidates.jsonl`
- Rotating file logging under `logs/`
- Session reset support from the Streamlit sidebar

## Installation Instructions

### Prerequisites

- Python 3.9 or newer
- An OpenAI API key
- `pip` or another Python package manager

Python 3.10+ is a practical choice for local development. The included Docker image uses Python 3.12.

### 1. Clone the repository

```bash
git clone https://github.com/upratham/TalentScout-Hiring-Assistant.git
cd TalentScout-Hiring-Assistant
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Optional editable install:

```bash
pip install -e .
```

### 4. Configure environment variables

Create or update `.env` in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

The application loads environment variables with `python-dotenv`.

### 5. Run the application locally

```bash
streamlit run app.py
```

By default, local Streamlit configuration in `.streamlit/config.toml` sets the server port to `5050`, so the app is typically available at:

```text
http://localhost:5050
```

### 6. Run with Docker

```bash
docker build -t talentscout-hiring-assistant .
docker run --env-file .env -p 10000:10000 -e PORT=10000 talentscout-hiring-assistant
```

Then open:

```text
http://localhost:10000
```

## Deployment

### Current deployment: Render

This project is currently deployed on Render. Render was chosen for the live/demo deployment because it offers a free tier, simple container-based deployment, and a much lower setup overhead for showcasing the project than a full cloud infrastructure setup.

### Why Render was used

- Free tier makes it suitable for student, demo, and portfolio deployment
- Easy to connect directly to a GitHub repository
- Minimal infrastructure management compared to a self-managed cloud VM
- Good fit for a lightweight Streamlit application

### Render deployment approach

The deployed app can be hosted on Render in either of these ways:

1. Connect the GitHub repository to a Render Web Service.
2. Use the included `Dockerfile` as the deployment source.
3. Set `OPENAI_API_KEY` in Render environment variables.
4. Render builds the image and starts the app using the container command.

Because Render is free and fast to configure, it was used as the primary deployment target for this project.

### AWS deployment option: ECR + EC2 + GitHub Actions

For a more production-oriented deployment path, this application can also be deployed on AWS using:

- Amazon ECR for container image storage
- Amazon EC2 for application hosting
- GitHub Actions for CI/CD automation

This approach is more scalable and closer to a real production pipeline than a free-tier hosting platform.

### Suggested AWS deployment flow

1. Create an Amazon ECR repository for the application image.
2. Launch an EC2 instance with Docker installed.
3. Store AWS and server credentials as GitHub repository secrets.
4. On every push to the deployment branch, GitHub Actions builds the Docker image.
5. GitHub Actions authenticates with AWS and pushes the image to ECR.
6. GitHub Actions connects to the EC2 instance through SSH.
7. The EC2 host pulls the latest image from ECR and restarts the container.

### GitHub Actions based AWS deployment method

A typical GitHub Actions pipeline for this project would:

- check out the repository
- configure AWS credentials
- log in to Amazon ECR
- build the Docker image
- push the image to ECR
- SSH into EC2
- pull the latest image
- stop and remove the old container
- run the new container with environment variables

Example workflow:

```yaml
name: Deploy to AWS

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: talentscout-hiring-assistant
          IMAGE_TAG: latest
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

      - name: Deploy on EC2
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            aws ecr get-login-password --region ${{ secrets.AWS_REGION }} | docker login --username AWS --password-stdin ${{ steps.login-ecr.outputs.registry }}
            docker pull ${{ steps.login-ecr.outputs.registry }}/talentscout-hiring-assistant:latest
            docker stop talentscout-app || true
            docker rm talentscout-app || true
            docker run -d --name talentscout-app -p 5050:5050 \
              -e OPENAI_API_KEY='${{ secrets.OPENAI_API_KEY }}' \
              ${{ steps.login-ecr.outputs.registry }}/talentscout-hiring-assistant:latest
```

### GitHub secrets needed for AWS deployment

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`
- `OPENAI_API_KEY`

### When to choose Render vs AWS

- Choose Render when you want the fastest and lowest-cost public deployment for a demo.
- Choose AWS when you want tighter deployment control, private infrastructure, and a CI/CD pipeline that more closely matches production environments.

## Usage Guide

1. Launch the Streamlit app.
2. Read the assistant's opening message.
3. Answer the screening questions in natural language.
4. Provide your tech stack when asked.
5. Review the generated technical questions and respond to them.
6. Type an exit phrase such as `done`, `bye`, `quit`, or `exit` when the interaction is complete.
7. The app extracts candidate details from the conversation and appends them to `candidates.jsonl`.

### What the user sees

- A chat interface for the interview flow
- A sidebar that updates candidate details as information is extracted
- A reset button to start a fresh interview session

### Data produced by the app

- `candidates.jsonl`: one JSON object per completed or partially completed candidate session
- `logs/`: timestamped application logs

## Technical Details

### Libraries and tools used

- `streamlit`: chat-based web UI
- `openai`: LLM access for conversation, extraction, and question generation
- `python-dotenv`: `.env` loading for local secrets
- `setuptools`: packaging support

Note: `gradio` appears in `pyproject.toml`, but the checked-in application flow is implemented with Streamlit and does not currently use Gradio.

### Model details

The project currently uses:

- `gpt-4.1-nano`

This is configured in `src/constants/__init__.py` through the `MODEL` constant and is used for:

- Main interview conversation
- Candidate information extraction
- Technical question generation

### Prompt architecture

The application uses three distinct prompts rather than one overloaded instruction block:

- `SYSTEM_PROMPT`
  drives the interview flow, ordering the conversation into greeting, data gathering, technical questioning, candidate answers, and farewell
- `EXTRACTION_PROMPT`
  converts the transcript into structured JSON with fixed keys
- `QUESTION_GEN_PROMPT`
  produces 3 to 5 questions per technology and calibrates question difficulty to experience level

### Code structure

```text
app.py                     Thin Streamlit entrypoint
src/constants/            Model config, prompts, file paths, exit keywords
src/core/                 Core LLM call and exit handling
src/conversation/         Conversation state bootstrap and greeting flow
src/candidate/            Candidate extraction, question generation, JSONL persistence
src/ui/                   Streamlit interface
src/logger/               Rotating log configuration
src/from_root/            Project-root resolution utility
src/pipeline/             Manual pipeline smoke test
```

### Architectural decisions

- Streamlit was chosen for a lightweight, fast-to-ship conversational interface.
- Candidate details are extracted from transcript context instead of forcing strict form input.
- Persistence uses `JSONL` instead of a database to keep the project simple and reviewable.
- Extraction is separated from the main chat call so the app can preserve a natural conversation while still producing structured recruiter-facing records.
- Exit handling is explicit and keyword-driven to ensure partial candidate information can still be saved when a session ends early.

## Prompt Design

The prompt design focuses on keeping the conversation structured without making it feel robotic.

### Information gathering strategy

The main system prompt instructs the model to:

- ask for one field at a time
- acknowledge each user answer before moving on
- stay within hiring-related topics
- redirect off-topic discussion politely
- avoid revealing internal instructions
- avoid scoring or making hiring promises

This approach improves conversational flow and reduces the chance of the model skipping required candidate fields.

### Technical question generation strategy

Question generation is separated into its own prompt so that the application can:

- base questions directly on the candidate's stated technologies
- calibrate difficulty to years of experience
- group questions by technology
- avoid mixing evaluation with question generation

Separating this prompt from the interview prompt also makes it easier to tune technical depth without disturbing the screening conversation itself.

### Structured extraction strategy

The extraction prompt is intentionally strict:

- fixed JSON schema
- `null` for missing values
- no markdown
- deterministic generation with low temperature

That design improves downstream reliability when saving candidate records locally.

## Challenges and Solutions

The repository shows a few implementation challenges that the current design is already trying to solve.

### 1. Preserving conversational state in Streamlit

Challenge:
Streamlit reruns the script on every interaction, which can easily reset the interview flow.

Solution:
The app stores chat history, display messages, session status, and extracted candidate data inside `st.session_state`.

### 2. Balancing natural conversation with structured data capture

Challenge:
Candidates usually answer in free-form language, while recruiters need structured records.

Solution:
The app keeps the interview conversational, then performs a separate extraction pass over the transcript using a dedicated JSON-focused prompt.

### 3. Handling incomplete or early-exit sessions

Challenge:
A candidate may stop mid-flow after providing only partial information.

Solution:
Exit keywords are checked explicitly, and the app extracts whatever information is available before saving the record.

### 4. Avoiding brittle hardcoded question sets

Challenge:
Static question banks do not adapt well to different stacks and experience levels.

Solution:
Technical questions are generated dynamically from the candidate's declared technologies and years of experience.

### 5. Preventing UI and API failures from crashing the session

Challenge:
External API calls can fail and disrupt the interview.

Solution:
The code wraps OpenAI requests in `try/except` blocks and returns fallback error messages instead of crashing the application.

## Limitations and Notes

- The app currently stores data locally in `candidates.jsonl`; it does not yet use a production database.
- Candidate validation is prompt-based rather than schema-enforced.
- `src/pipeline/test_pipeline.py` is a manual smoke-test style script and makes live OpenAI calls.
- The project contains signs of ongoing refactoring, but the main documented runtime path is the Streamlit UI entrypoint used by `app.py`.

## Future Improvements

- Add stronger validation for email, phone, and experience fields
- Save candidates to a database or ATS backend
- Add recruiter review dashboards
- Add scoring rubrics or interviewer notes as a separate post-processing step
- Add automated tests around extraction quality and exit handling

## Author

Prathamesh Uravane  
upratha,2002@gmail.com

## License

This project is released under the MIT License. See `LICENSE` for details.

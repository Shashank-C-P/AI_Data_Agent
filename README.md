AI Data Agent: Conversational Intelligence Platform
This is an advanced, full-stack AI-powered conversational interface that allows users to gain deep insights from their data simply by asking questions in natural language. The platform supports a wide range of file types, including structured data (Excel, CSV) and unstructured documents (PDF, DOCX), and leverages state-of-the-art Generative AI to provide exceptional analytical capabilities.

Core Features
Multi-Modal Data Handling: Seamlessly analyzes both structured spreadsheets and unstructured text documents.

Chat-First Interface: Users can start a conversation immediately and upload a file at any point to provide context for deeper analysis.

Exceptional Analytical Capabilities:

Data Analysis: For spreadsheets, the agent uses a SQL-powered engine to perform complex calculations, identify trends, and analyze data to answer business questions.

Document Analysis: For documents, it uses a RAG (Retrieval-Augmented Generation) pipeline to read the content and provide detailed answers based only on the provided text.

Dynamic Visualizations: The agent intelligently decides when to generate visualizations, creating Bar, Line, and Pie charts to accompany its analysis when appropriate.

Web-Enhanced Insights: The agent can autonomously search the web to enrich its analysis with external, real-world context and provide practical business strategies, citing its sources.

Polished User Experience: A sleek, full-screen, dark-mode interface with a professional design and clear, organized responses.

Technical Stack
Frontend: React (with Vite)

Backend: Python (with FastAPI)

AI & Orchestration: LangChain

Core LLM: OpenAI GPT-4 Turbo

Web Search: Tavily AI

Charting: Chart.js

How to Run Locally
Prerequisites
Python 3.8+

Node.js & npm

An OpenAI API key

A Tavily AI API key

Backend Setup
Navigate to the backend directory: cd backend

Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

Install the required Python packages:

pip install -r requirements.txt

Create a .env file in the backend directory and add your API keys:

OPENAI_API_KEY="sk-..."
TAVILY_API_KEY="tvly-..."

Start the backend server:

python -m uvicorn main:app --reload

The server will be running at http://localhost:8000.

Frontend Setup
In a new terminal, navigate to the frontend directory: cd frontend

Install the required npm packages:

npm install

Start the frontend development server:

npm run dev

The application will be accessible at http://localhost:5173.

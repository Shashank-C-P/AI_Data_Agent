import os
import json
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
import re

load_dotenv()

def _clean_excel_or_csv(file_path: str) -> pd.DataFrame:
    df = pd.DataFrame()
    try:
        if file_path.endswith((".xls", ".xlsx")):
            df_all = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            if df_all:
                df = next(iter(df_all.values()), pd.DataFrame())
        else:
            df = pd.read_csv(file_path)

        if df.empty: return df
        df.columns = [str(c).strip() if str(c).strip() else f"unnamed_col_{i}" for i, c in enumerate(df.columns)]
        df.columns = df.columns.str.replace(r'[^a-zA-Z0-9_]', '_', regex=True)
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    converted_dates = pd.to_datetime(df[col], errors='coerce')
                    if converted_dates.notna().sum() / df[col].notna().sum() > 0.5:
                         df[col] = converted_dates.dt.strftime('%Y-%m-%d')
                except Exception: pass
    except Exception as e:
        print(f"Error cleaning file: {e}")
    return df

def _validate_chart_data(chart_data):
    if not chart_data or 'labels' not in chart_data or 'datasets' not in chart_data: return None
    if not isinstance(chart_data['labels'], list) or not isinstance(chart_data['datasets'], list): return None
    for dataset in chart_data['datasets']:
        if 'label' not in dataset or 'data' not in dataset: return None
        if not isinstance(dataset['data'], list): return None
    return chart_data

def _handle_general_query(question: str) -> dict:
    print("--- EXECUTING GENERAL CONVERSATION BRAIN ---")
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        tavily_tool = TavilySearchResults(max_results=3)
        llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0.5)
        
        prompt = f"""
        You are a helpful AI assistant. Answer the user's question based on the provided web search results.
        User Question: {question}
        Web Search Results:
        {tavily_tool.invoke(question)}
        """
        
        response = llm.invoke(prompt)
        return {"summary": response.content, "chartType": "NONE", "chartData": None, "tableData": None}
    except Exception as e:
        print(f"Error in general query handler: {e}")
        return {"summary": "Sorry, I encountered an error while trying to answer your question.", "chartType": "NONE", "chartData": None, "tableData": None}

def _handle_structured_data(file_path: str, question: str) -> dict:
    print("--- EXECUTING FINAL AI CONSULTANT (STRUCTURED) ---")
    try:
        df = _clean_excel_or_csv(file_path)
        if df.empty:
            return {"summary": "Could not read or process the provided spreadsheet.", "chartType": "NONE", "chartData": None, "tableData": None}

        engine = create_engine("sqlite:///:memory:")
        df.to_sql("data", engine, index=False, if_exists="replace")
        db = SQLDatabase(engine)

        llm = ChatOpenAI(
            model_name="gpt-4-turbo",
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}},
        )

        table_schema = db.get_table_info()
        sample_rows = pd.read_sql("SELECT * FROM data LIMIT 3", engine).to_markdown()

        prompt = f"""
        You are an elite Business Intelligence Consultant. Your task is to provide an exceptional, data-driven analysis based on the user's question about the data they've uploaded.

        **DATABASE SCHEMA:**
        {table_schema}
        **SAMPLE DATA ROWS:**
        {sample_rows}
        **USER'S QUESTION:**
        "{question}"

        **YOUR MISSION:**
        1.  **Understand the Goal:** Deeply analyze the user's question to understand their core business objective.
        2.  **Formulate a SQL Query:** Write a single, correct SQL query to extract the precise data needed.
        3.  **Execute and Analyze:** Imagine you execute the query. Based on the expected result, write a long-form, consulting-style analysis (minimum 500 words). Be insightful. Identify trends, anomalies, and key takeaways. Interpret the data.
        4.  **Determine Visualization:** Decide the best way to visualize the data. Your options are 'BAR', 'LINE', 'PIE', 'SCATTER', or 'NONE'.
            - Use 'PIE' for compositions (e.g., sales percentage by region).
            - Use 'BAR' for comparing distinct categories.
            - Use 'LINE' for trends over time.
            - Use 'SCATTER' to show correlation between two numeric variables.
        5.  **Construct the Final JSON:** Create a single JSON object containing your full analysis.

        **FINAL OUTPUT (MUST BE A SINGLE, VALID JSON OBJECT):**
        You must respond with a JSON object with the following exact keys: "summary", "chartType", "chartData", "tableData".
        - `summary`: Your full, insightful, consulting-style analysis of the data.
        - `chartType`: Your choice of 'BAR', 'LINE', 'PIE', 'SCATTER', or 'NONE'.
        - `chartData`: A valid Chart.js object with "labels" and "datasets". If a chart is needed, otherwise null. **For PIE charts, the datasets MUST include a `backgroundColor` array with multiple distinct hex color codes.**
        - `tableData`: A table object with "headers" and "rows" containing the data from your SQL query.
        """
        
        response = llm.invoke(prompt)
        json_response = json.loads(response.content)
        
        validated_chart_data = _validate_chart_data(json_response.get('chartData'))
        if not validated_chart_data:
            json_response['chartType'] = 'NONE'
        json_response['chartData'] = validated_chart_data
        
        return json_response

    except Exception as e:
        print(f"Error in structured data handler: {e}")
        return {"summary": f"An error occurred: {e}", "chartType": "NONE", "chartData": None, "tableData": None}


def _handle_unstructured_data(file_path: str, question: str) -> dict:
    print("--- EXECUTING FINAL AI CONSULTANT (UNSTRUCTURED) ---")
    try:
        loader = PyPDFLoader(file_path) if file_path.endswith(".pdf") else Docx2txtLoader(file_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        store = FAISS.from_documents(chunks, OpenAIEmbeddings())

        llm = ChatOpenAI(
            model_name="gpt-4-turbo",
            temperature=0.3,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        
        prompt_template = """
        You are an Expert Business Analyst. Use the following context from a document to answer the user's question. Your task is to provide a comprehensive, detailed analysis (minimum 500 words).

        **Context from Document:**
        {context}
        **User's Question:**
        {question}

        **Your Mission:**
        1. **Analyze the Text:** Read the provided context to find the most relevant information.
        2. **Extract Tabular Data:** If the text contains data that can be structured into a table, you MUST extract it.
        3. **Synthesize a Report:** Write a long-form, consulting-style report that answers the user's question using the context.
        4. **Determine Visualization:** Based on any tabular data you extracted, decide if a 'BAR', 'LINE', 'PIE', 'SCATTER', or 'NONE' chart is appropriate.
        5. **Construct JSON:** Format your entire response into a single JSON object.

        **Final Output (must be a single, valid JSON object with the keys "summary", "chartType", "chartData", and "tableData"):**
        """
        
        from langchain.prompts import PromptTemplate
        QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"], template=prompt_template)
        
        qa_chain = RetrievalQA.from_chain_type(llm, retriever=store.as_retriever(), chain_type_kwargs={"prompt": QA_CHAIN_PROMPT})
        
        raw_response = qa_chain({"query": question})["result"]

        json_response = json.loads(raw_response)
        
        validated_chart_data = _validate_chart_data(json_response.get('chartData'))
        if not validated_chart_data:
            json_response['chartType'] = 'NONE'
        json_response['chartData'] = validated_chart_data
            
        return json_response

    except Exception as e:
        print(f"Error in unstructured data handler: {e}")
        return {"summary": "Error analyzing the document.", "chartType": "NONE", "chartData": None, "tableData": None}


def get_answer(file_path: str, question: str) -> dict:
    if not file_path:
        return _handle_general_query(question)
        
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".xls", ".xlsx", ".csv"]:
        return _handle_structured_data(file_path, question)
    elif ext in [".pdf", ".docx"]:
        return _handle_unstructured_data(file_path, question)
    else:
        return {"summary": "Unsupported file type.", "chartType": "NONE", "chartData": None, "tableData": None}


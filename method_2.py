import json
import openai
import pandas as pd
import os
import sqlite3
import time
from datetime import datetime
from tqdm import tqdm

from config import parameters_for_methods as conf
from utils import *

openai.api_key = conf.api_key


class GPT:
    def __init__(self, model, prompt_templates, max_tokens):
        """Initialize the GPT class with model, prompt templates, and configuration."""
        self.model = model
        self.prompt_templates = prompt_templates
        self.max_tokens = max_tokens

    def get_response(self, input, log_path):
        """Get a response from the model based on the input and type."""
        message = self.create_message(input)
        response = self.query_API(message)
        if log_path:
            with open(log_path, "a") as file:
                file.write(f"Message: {message}\nResponse: {response}\n\n")
        return response

    def create_message(self, input):
        """Create a message based on the input and type."""
        table_columns, question, demo = input
        prompt = self.prompt_templates.format(question=question, table_columns=table_columns, demo=demo)
        message = [{'role': 'user', 'content': prompt}]
        return message

    def query_API(self, messages):
        """Query the OpenAI API and handle exceptions."""
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=0,
                    max_tokens=self.max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                return response['choices'][0]['message']['content']
            except (openai.error.RateLimitError, openai.error.ServiceUnavailableError, 
                    openai.error.Timeout, openai.error.APIError, 
                    openai.error.APIConnectionError) as e:
                print(f'Error: {e}\nRetrying...')
                time.sleep(20)
        raise Exception("Failed to get response from API after several retries.")


class Text2SQL:
    def __init__(self, db_path, model, prompt_path, prompt_version, max_tokens, log_path=None):
        """Initialize the TableQA class with configuration."""
        self.db = db_path
        self.prompt_templates = self.load_prompt_templates(prompt_path, prompt_version)
        self.LLM = GPT(model=model, prompt_templates=self.prompt_templates, max_tokens=max_tokens)
        self.max_serialization_tokens = max_tokens
        self.log_path = log_path

    def forward(self, question, demo=None):
        """Extract column names from the SQLite database and generate SQL query."""
        headers = self.extract_all_column_names(self.db)
        linearized_headers = ', '.join([
            f"{table}({', '.join(columns)})" for table, columns in headers.items()
        ])
        linearized_demo = ""
        for item in demo:
            linearized_demo += f"\n{item['question']}\n{item['sql']}\n"
        sql_query = "SELECT " + self.LLM.get_response((linearized_headers, question, linearized_demo), self.log_path)
        return sql_query
    
    def load_prompt_templates(self, prompt_path, prompt_version):
        """Load prompt templates from a file."""
        with open(prompt_path, "rb") as f:
            prompt_templates = json.load(f)
        return prompt_templates[prompt_version]

    def extract_all_column_names(self, db):
        """ Extract column names from all tables in the SQLite database. """
        with sqlite3.connect(db) as conn:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables = pd.read_sql_query(query, conn)['name'].tolist()
            table_columns = {}
            for table in tables:
                query = "PRAGMA table_info(" + table + ")"
                columns = pd.read_sql_query(query, conn)
                table_columns[table] = columns['name'].tolist()
        return table_columns


if __name__ == '__main__':
    nowtime = datetime.now().strftime("%Y%m%d%H%M%S")
    with open(conf.json_path, "rb") as f:
        tables = json.load(f)
    with open(conf.qa_pairs_path, "rb") as f:
        questions = json.load(f)
    with open(conf.qa_demo_path, "rb") as f:
        demo = json.load(f)
    prediction_path = os.path.join(conf.output_path, f"predictions_{nowtime}.json")
    log_path = os.path.join(conf.output_path, f"log_{nowtime}.txt")
    text2sql = Text2SQL(conf.db_path, conf.model, conf.prompt_path, conf.method, conf.max_tokens, log_path)
    predictions = []

    for question in tqdm(questions):
        try:
            prediction_sql = text2sql.forward(question["question"], demo=demo)
            prediction_answer = sql_to_answer(conf.db_path, prediction_sql)
            predictions.append({
                "id": question["id"],
                "type": question["type"],
                "question": question["question"],
                "tables": question["tables"],
                "sql": prediction_sql,
                "answer": prediction_answer
            })
        except openai.error.InvalidRequestError as e:
            print(e)

    with open(prediction_path, "w") as file:
        json.dump(predictions, file, ensure_ascii=False, indent=4)

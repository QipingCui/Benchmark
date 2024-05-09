import json
import logging
import openai
import os
import time
import re
from datetime import datetime
from tqdm import tqdm

from config import parameters_for_methods as conf

openai.api_key = conf.api_key


class GPT:
    def __init__(self, model, prompt_path, prompt_version, max_tokens):
        # Initialize the GPT class with model, prompt templates, and configuration.
        self.model = model
        self.prompt_templates = self.load_prompt_templates(prompt_path, prompt_version)
        self.max_tokens = max_tokens
        self.history_contents = []
        self.history_messages = []

    def load_prompt_templates(self, prompt_path, prompt_version):
        # Load prompt templates from a file.
        with open(prompt_path, "rb") as f:
            prompt_templates = json.load(f)
        return prompt_templates[prompt_version]

    def reset_history_contents(self):
        # Reset the history of contents.
        self.history_contents = []   

    def reset_history_messages(self):
        # Reset the history of messages.
        self.history_messages = []

    def get_response(self, input, type):
        # Get a response from the model based on the input and type.
        message = self.create_message(input, type)
        self.history_contents.append(message['content'])
        self.history_messages.append(message)
        message = self.query_API(self.history_messages)
        self.history_contents.append(message['content'])
        self.history_messages.append(message)
        response = message['content']
        return response

    def create_message(self, input, type):
        # Create a message based on the input and type.
        if type == "select_columns":
            prompt_template = self.prompt_templates['select_columns']
            columns, question = input
            prompt = prompt_template.format(question=question, columns=columns)
        elif type == 'rows_select':
            prompt_template = self.prompt_templates['select_rows']
            selected_columns, rows, question = input
            prompt = prompt_template.format(selected_columns=selected_columns, rows=rows, question=question)
        elif type == "ask_final_answer_or_next_question":
            question, serialized_table = input
            prompt_template = self.prompt_templates['ask_final_answer_or_next_question']
            prompt = prompt_template.format(table=serialized_table, question=question)
        else:
            raise NotImplementedError
        message = {'role': 'user', 'content': prompt}
        return message

    def query_API(self, messages):
        # Query the OpenAI API and handle exceptions.
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
                return response['choices'][0]['message']
            except (openai.error.RateLimitError, openai.error.ServiceUnavailableError, 
                    openai.error.Timeout, openai.error.APIError, 
                    openai.error.APIConnectionError) as e:
                print(f'Error: {e}\nRetrying...')
                time.sleep(20)
        raise Exception("Failed to get response from API after several retries.")


def extract_column_names(table):
    headers = table['headers']
    return headers


def extract_columns(table, selected_column_list):
    # Clean headers and find indices of selected columns
    headers = [header.replace("\n", " ") for header in table['headers']]
    selected_indices = [idx for idx, header in enumerate(headers) if header in selected_column_list]

    # Extract headers and rows for selected columns
    new_table = {
        'headers': [table['headers'][idx] for idx in selected_indices],
        'rows': [[row[idx] for idx in selected_indices] for row in table['rows']]
    }

    return new_table


def extract_subtable(extracted_columns, selected_rows):
    # Extract row indices from the selected_rows string
    selected_row_list = [int(match) - 1 for match in re.findall(r'\d+', selected_rows)]
    
    # Filter the rows based on the extracted indices
    subtable = {
        'headers': extracted_columns['headers'],
        'rows': [extracted_columns['rows'][rid] for rid in selected_row_list if rid < len(extracted_columns['rows'])]
    }

    return subtable


def linearize_headers(headers):
    headers = [header.replace("\n", " ") for header in headers]
    linearized_headers = ", ".join(headers)
    return linearized_headers


def linearize_rows(table):
    headers = table['headers']
    rows = table['rows']

    # Creating the linearized string for each row
    lines = [
        f"item {idx + 1}: " + "; ".join(f"({head}, {cell})" for head, cell in zip(headers, row)) for idx, row in enumerate(rows)
    ]

    # Joining all lines into a single string
    linearized_rows = "\n".join(lines)

    return linearized_rows


class TableQA:
    def __init__(self, conf):
        """Initialize the TableQA class with configuration."""
        self.conf = conf
        self.LLM = GPT(model=conf.model, prompt_path=conf.prompt_path, 
                       prompt_version="simple_structgpt_tableqa", max_tokens=conf.max_tokens)
        self.max_serialization_tokens = conf.max_input_tokens

    def forward(self, table, question):
        self.LLM.reset_history_contents()
        self.LLM.reset_history_messages()

        """Extract column names (headers)."""
        # Invoke
        headers = extract_column_names(table)
        # Linearize
        linearized_headers = linearize_headers(headers)
        # Generate
        selected_columns = self.LLM.get_response((linearized_headers, question), "select_columns")
        self.LLM.reset_history_messages()
        
        """Extract columns."""
        # Invoke
        selected_column_list = [head for head in headers if head in selected_columns]
        extracted_columns = extract_columns(table, selected_column_list)
        # Linearize
        linearized_selected_columns = linearize_headers(selected_column_list)
        linearized_rows = linearize_rows(extracted_columns)
        # Generate
        selected_rows = self.LLM.get_response((linearized_selected_columns, linearized_rows, question), "rows_select")
        self.LLM.reset_history_messages()
        
        """Extract subtable."""
        # Invoke
        subtable = extract_subtable(extracted_columns, selected_rows)
        # Linearize
        serialized_table = linearize_rows(subtable)
        # Generate
        answer = self.LLM.get_response((question, serialized_table), "ask_final_answer_or_next_question")
        self.LLM.reset_history_messages()

        return answer, self.LLM.history_contents


if __name__ == '__main__':
    with open(conf.json_path, "rb") as f:
        tables = json.load(f)
    with open(conf.qa_pairs_path, "rb") as f:
        questions = json.load(f)
    nowtime = datetime.now().strftime("%Y%m%d%H%M%S")
    prediction_path = os.path.join(conf.output_path, f"predictions_{nowtime}.json")
    predictions = []
    chat_history = []
    table_qa = TableQA(conf)

    for question in tqdm(questions):
        if len(question["tables"]) != 1:
            continue
        try:
            prediction, ch_history = table_qa.forward(tables[question["tables"][0]], question["question"])
            predictions.append({
                "id": question["id"],
                "type": question["type"],
                "question": question["question"],
                "tables": question["tables"],
                "answer": prediction
            })
            chat_history.append(ch_history)
        except openai.error.InvalidRequestError as e:
            print(e)

    with open(prediction_path, "w") as file:
        json.dump(predictions, file, ensure_ascii=False, indent=4)

    chat_history_path = os.path.join(conf.output_path, f"chat_history_{nowtime}.txt")
    try:
        chat = "\n******\n".join("\n------\n".join(sub) for sub in chat_history)
        with open(chat_history_path, "w") as fclog:
            fclog.write(chat)
    except Exception as e:
        print(e)
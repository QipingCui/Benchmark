class parameters_for_dataloader():
    """Parameters for "dataloader.py"."""
    table_id = 1    # 0 for data without date, 1 for data with date
    limit = 100     # Limit the number of rows to read from the excel files, None for no limit
    
    # Paths
    table_idx = f"{table_id}_limit{limit}" if limit else f"{table_id}"
    excel_paths = {
        "Balance_Sheet": f"data/Balance_Sheet_{table_id}.xlsx",
        "Income_Statement": f"data/Income_Statement_{table_id}.xlsx",
        "Cash_Flow_Statement": f"data/Cash_Flow_Statement_{table_id}.xlsx"
    }
    info_path = "data/info.xlsx"
    json_path = f"data/tables_{table_idx}.json"
    db_path = f"data/tables_{table_idx}.db"


class parameters_for_main():
    """Parameters for "main.py"."""
    qa_id = "4_demo_t2"
    table_id = 2    # 0 for data without date, 1 for data with date
    limit = 100     # Limit the number of rows to read from the excel files, None for no limit

    num_one_step_questions = 0
    num_multi_step_questions = 0
    num_multi_table_questions = 0
    num_table_reasoning_questions = 1
    num_fuzzy_questions = 0

    # Paths
    qa_idx = f"{qa_id}_limit{limit}" if limit else f"{qa_id}"
    table_idx = f"{table_id}_limit{limit}" if limit else f"{table_id}"
    db_path = f"data/tables_{table_idx}.db"
    qa_pairs_path = f"data/qa_pairs_{qa_idx}.json"
    json_path = f"data/tables_{table_idx}.json"


class parameters_for_methods():
    """Parameters for methods."""
    method = "CoT_2"    # "baseline", "structgpt_for_tableqa", "structgpt_for_text2sql", "method_x", "CoT"
    table_id = 1    # 0 for data without date, 1 for data with date
    limit = 100     # Limit the number of rows to read from the excel files, None for no limit
    qa_id = 4
    FewShot = True
    qa_demo_id = "4_demo_for_cot"

    # OpenAI API parameters
    api_key = ""
    model = "gpt-3.5-turbo-0125"
    max_tokens = 4096
    max_input_tokens = 16385

    # Paths
    table_idx = f"{table_id}_limit{limit}" if limit else f"{table_id}"
    json_path = f"data/tables_{table_idx}.json"
    db_path = f"data/tables_{table_idx}.db"
    qa_idx = f"{qa_id}_limit{limit}" if limit else f"{qa_id}"
    qa_pairs_path = f"data/qa_pairs_{qa_idx}.json"
    qa_demo_path = f"data/qa_pairs_{qa_demo_id}_limit{limit}.json" if limit else f"data/qa_pairs_{qa_demo_id}.json"
    prompt_path = "./prompts/prompts.json"
    output_path = f"outputs/{method}"


class parameters_for_evaluation():
    """Parameters for "evaluation.py"."""
    method = "CoT_2"    # "baseline", "structgpt_for_tableqa", "structgpt_for_text2sql", "method_x"
    qa_id = 4
    limit = 100     # Limit the number of rows to read from the excel files, None for no limit
    sql = True

    # Paths
    qa_idx = f"{qa_id}_limit{limit}" if limit else f"{qa_id}"
    qa_pairs_path = f"data/qa_pairs_{qa_idx}.json"
    output_path = f"outputs/{method}"

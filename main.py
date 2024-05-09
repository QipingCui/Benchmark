import json
import pandas as pd
import random

from config import parameters_for_main as conf
from utils import *


def generate_one_step_questions(idx, data, num_questions):
    qa_pairs = []
    count = 0

    while count < num_questions:
        # Randomly select a subtable
        table = random.choice(list(data.keys()))
        dataframe = pd.DataFrame(data[table]['rows'], columns=data[table]['headers'])
        row = dataframe.sample().iloc[0]
        col = random.choice([c for c in dataframe.columns if c not in ['股票代码', '股票简称', '截止日期', '年度', '公司全称']])
        value = row[col]

        # Generate answer
        answer = str(value)
        if answer == 'nan':
            continue

        # Generate question and sql
        item = random.choice(['股票代码', '股票简称'])
        if conf.table_id == 0:    # dataset 0 without date
            question = f"{item}为{row[item]}的公司的{col}是多少？"
            sql = f"SELECT `{col}` FROM {table} WHERE `{item}` = '{row[item]}'"
        else:   # dataset 1 with date
            if table == 'Balance_Sheet':
                question = f"截止到{row['截止日期']}，{item}为{row[item]}的公司的{col}是多少？"
                sql = f"SELECT `{col}` FROM {table} WHERE `{item}` = '{row[item]}' AND `截止日期` = '{row['截止日期']}'"
            else:
                question = f"{row['年度']}年度，{item}为{row[item]}的公司的{col}是多少？"
                sql = f"SELECT `{col}` FROM {table} WHERE `{item}` = '{row[item]}' AND `年度` = '{row['年度']}'"

        # Skip duplicate questions
        if any(qa_pair['question'] == question for qa_pair in qa_pairs):
            continue

        # Create a dictionary for the QA pair
        qa_pair = {
            "id": idx + count,
            "type": "numerical reasoning: one step",
            "question": question,
            "tables": [table],
            "sql": sql,
            "answer": answer
        }

        # Check if sql is correct
        try:
            sql_answer = sql_to_answer(conf.db_path, sql)
            if sql_answer != answer:
                print(f"SQL query failed in \n{qa_pair}")
                print(f"SQL query return {sql_answer} != {answer}")
                continue
        except Exception as e:
            print(f"Error while executing SQL in \n{qa_pair}: \n{e}")
            continue

        # Append to the list
        qa_pairs.append(qa_pair)
        count += 1
        print(f"Generating One-step Numerical Questions: {count}/{num_questions}")

    return qa_pairs


def generate_multi_step_questions(idx, data, num_questions):
    qa_pairs = []
    count = 0

    while count < num_questions:
        item = random.choice(['成本收入比', '资产负债率', '净资产负债率', '同比增长率'])

        if item == '成本收入比':    # “营业总成本”除以“营业总收入”
            # Randomly select a subtable
            table = 'Income_Statement'
            dataframe = pd.DataFrame(data[table]['rows'], columns=data[table]['headers'])
            row = dataframe.sample().iloc[0]

            # Generate answer
            if str(row['营业总收入']) == 'nan' or str(row['营业总成本']) == 'nan':
                continue
            answer = str(float(row['营业总成本']) / float(row['营业总收入']))

            # Generate question and sql
            if conf.table_id == 0:
                question = f"股票简称为{row['股票简称']}的公司的成本收入比是多少？"
                sql = f"SELECT 营业总成本 / 营业总收入 AS 成本收入比 FROM {table} WHERE 股票简称 = '{row['股票简称']}'"
            else:
                question = f"{row['年度']}年度，股票简称为{row['股票简称']}的公司的成本收入比是多少？"
                sql = f"SELECT 营业总成本 / 营业总收入 AS 成本收入比 FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 年度 = '{row['年度']}'"

        elif item == '资产负债率':    # “负债合计”除以“资产总计”
            # Randomly select a subtable
            table = 'Balance_Sheet'
            dataframe = pd.DataFrame(data[table]['rows'], columns=data[table]['headers'])
            row = dataframe.sample().iloc[0]

            # Generate answer
            if str(row['资产总计']) == 'nan' or str(row['负债合计']) == 'nan':
                continue
            answer = str(float(row['负债合计']) / float(row['资产总计']))

            # Generate question and sql
            if conf.table_id == 0:
                question = f"股票简称为{row['股票简称']}的公司的资产负债率是多少？"
                sql = f"SELECT 负债合计 / 资产总计 AS 资产负债率 FROM {table} WHERE 股票简称 = '{row['股票简称']}'"
            else:
                question = f"截止到{row['截止日期']}，股票简称为{row['股票简称']}的公司的资产负债率是多少？"
                sql = f"SELECT 负债合计 / 资产总计 AS 资产负债率 FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 截止日期 = '{row['截止日期']}'"
        
        elif item == '净资产负债率':    # “负债合计”除以“所有者权益合计”
            # Select subtable
            table = 'Balance_Sheet'
            dataframe = pd.DataFrame(data[table]['rows'], columns=data[table]['headers'])
            row = dataframe.sample().iloc[0]

            # Generate answer
            if str(row['所有者权益合计']) == 'nan' or str(row['负债合计']) == 'nan':
                continue
            answer = str(float(row['负债合计']) / float(row['所有者权益合计']))

            # Generate question and sql
            if conf.table_id == 0:
                question = f"股票简称为{row['股票简称']}的公司的净资产负债率是多少？"
                sql = f"SELECT 负债合计 / 所有者权益合计 AS 净资产负债率 FROM {table} WHERE 股票简称 = '{row['股票简称']}'"
            else:
                question = f"截止到{row['截止日期']}，股票简称为{row['股票简称']}的公司的净资产负债率是多少？"
                sql = f"SELECT 负债合计 / 所有者权益合计 AS 净资产负债率 FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 截止日期 = '{row['截止日期']}'"
            
        elif item == '同比增长率':
            if conf.table_id == 0:
                continue

            # Randomly select a subtable
            table = random.choice(list(data.keys()))
            dataframe = pd.DataFrame(data[table]['rows'], columns=data[table]['headers'])
            row = dataframe.sample().iloc[0]
            if table == 'Balance_Sheet':
                if row['截止日期'] == '2021-12-31':
                    previous_row = row
                    row = dataframe[(dataframe['股票代码'] == previous_row['股票代码']) & (dataframe['截止日期'] == '2022-12-31')].iloc[0]
                elif row['截止日期'] == '2022-12-31':
                    previous_row = dataframe[(dataframe['股票代码'] == row['股票代码']) & (dataframe['截止日期'] == '2021-12-31')].iloc[0]
            else:
                if row['年度'] == '2021':
                    previous_row = row
                    row = dataframe[(dataframe['股票代码'] == previous_row['股票代码']) & (dataframe['年度'] == '2022')].iloc[0]
                elif row['年度'] == '2022':
                    previous_row = dataframe[(dataframe['股票代码'] == row['股票代码']) & (dataframe['年度'] == '2021')].iloc[0]
            col = random.choice([c for c in dataframe.columns if c not in ['股票代码', '股票简称', '截止日期', '年度', '公司全称']])

            # Generate answer
            if str(row[col]) == 'nan' or str(previous_row[col]) == 'nan':
                continue
            answer = str((float(row[col]) - float(previous_row[col])) / float(previous_row[col]))

            # Generate question and sql
            if table == 'Balance_Sheet':
                question = f"截止到2022-12-31，股票简称为{row['股票简称']}的公司的{col}同比增长率是多少？"
                sql = f"SELECT ((SELECT `{col}` FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 截止日期 = '2022-12-31') - (SELECT `{col}` FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 截止日期 = '2021-12-31')) / (SELECT `{col}` FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 截止日期 = '2021-12-31') AS 同比增长率"
            else:
                question = f"2022年度股票简称为{row['股票简称']}的公司的{col}同比增长率是多少？"
                sql = f"SELECT ((SELECT `{col}` FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 年度 = '2022') - (SELECT `{col}` FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 年度 = '2021')) / (SELECT `{col}` FROM {table} WHERE 股票简称 = '{row['股票简称']}' AND 年度 = '2021') AS 同比增长率"

        # Skip duplicate questions
        if any(qa_pair['question'] == question for qa_pair in qa_pairs):
            continue

        # Create a dictionary for the QA pair
        qa_pair = {
            "id": idx + count,
            "type": "numerical reasoning: multi step",
            "question": question,
            "tables": [table],
            "sql": sql,
            "answer": answer
        }

        # Check if sql is correct
        try:
            sql_answer = sql_to_answer(conf.db_path, sql)
            if sql_answer != answer:
                print(f"SQL query failed in \n{qa_pair}")
                print(f"SQL query return {sql_answer} != {answer}")
                continue
        except Exception as e:
            print(f"Error while executing SQL in \n{qa_pair}: \n{e}")
            continue

        # Append to the list
        qa_pairs.append(qa_pair)
        count += 1
        print(f"Generating Multi-step Numerical Reasoning Questions: {count}/{num_questions}")

    return qa_pairs


def gengrate_multi_table_questions(idx, data, num_questions):
    qa_pairs = []
    count = 0

    while count < num_questions:
        item = random.choice(['总资产收益率', '净资产收益率', '总资产周转率'])

        if item == '总资产收益率':    # “净利润”除以“资产总计”
            # Select subtables
            income_table = 'Income_Statement'
            balance_table = 'Balance_Sheet'
            tables = [income_table, balance_table]
            income_df = pd.DataFrame(data[income_table]['rows'], columns=data[income_table]['headers'])
            balance_df = pd.DataFrame(data[balance_table]['rows'], columns=data[balance_table]['headers'])
            income_row = income_df.sample().iloc[0]
            if conf.table_id == 0:
                balance_row = balance_df[(balance_df['股票代码'] == income_row['股票代码'])].iloc[0]
            else:
                balance_row = balance_df[(balance_df['股票代码'] == income_row['股票代码']) & (balance_df['截止日期'].str.contains(str(income_row['年度'])))].iloc[0]
                    
            # Generate answer
            if str(income_row['净利润']) == 'nan' or str(balance_row['资产总计']) == 'nan':
                continue
            answer = str(float(income_row['净利润']) / float(balance_row['资产总计']))

            # Generate question and sql
            if conf.table_id == 0:
                question = f"股票简称为{income_row['股票简称']}的公司的总资产收益率是多少？"
                sql = f"SELECT (SELECT 净利润 FROM {income_table} WHERE 股票简称 = '{income_row['股票简称']}') / (SELECT 资产总计 FROM {balance_table} WHERE 股票简称 = '{balance_row['股票简称']}') AS 总资产收益率"
            else:
                question = f"{income_row['年度']}年度，股票简称为{income_row['股票简称']}的公司的总资产收益率是多少？"
                sql = f"SELECT (SELECT 净利润 FROM {income_table} WHERE 股票简称 = '{income_row['股票简称']}' AND 年度 = '{income_row['年度']}') / (SELECT 资产总计 FROM {balance_table} WHERE 股票简称 = '{balance_row['股票简称']}' AND 截止日期 LIKE '%{income_row['年度']}%') AS 总资产收益率"
        
        elif item == '净资产收益率':    # “净利润”除以“所有者权益合计”
            # Select subtables
            income_table = 'Income_Statement'
            balance_table = 'Balance_Sheet'
            tables = [income_table, balance_table]
            income_df = pd.DataFrame(data[income_table]['rows'], columns=data[income_table]['headers'])
            balance_df = pd.DataFrame(data[balance_table]['rows'], columns=data[balance_table]['headers'])
            income_row = income_df.sample().iloc[0]
            if conf.table_id == 0:
                balance_row = balance_df[(balance_df['股票代码'] == income_row['股票代码'])].iloc[0]
            else:
                balance_row = balance_df[(balance_df['股票代码'] == income_row['股票代码']) & (balance_df['截止日期'].str.contains(str(income_row['年度'])))].iloc[0]
                    
            # Generate answer
            if str(income_row['净利润']) == 'nan' or str(balance_row['所有者权益合计']) == 'nan':
                continue
            answer = str(float(income_row['净利润']) / float(balance_row['所有者权益合计']))

            # Generate question and sql
            if conf.table_id == 0:
                question = f"股票简称为{income_row['股票简称']}的公司的净资产收益率是多少？"
                sql = f"SELECT (SELECT 净利润 FROM {income_table} WHERE 股票简称 = '{income_row['股票简称']}') / (SELECT 所有者权益合计 FROM {balance_table} WHERE 股票简称 = '{balance_row['股票简称']}') AS 净资产收益率"
            else:
                question = f"{income_row['年度']}年度，股票简称为{income_row['股票简称']}的公司的净资产收益率是多少？"
                sql = f"SELECT (SELECT 净利润 FROM {income_table} WHERE 股票简称 = '{income_row['股票简称']}' AND 年度 = '{income_row['年度']}') / (SELECT 所有者权益合计 FROM {balance_table} WHERE 股票简称 = '{balance_row['股票简称']}' AND 截止日期 LIKE '%{income_row['年度']}%') AS 净资产收益率"

        elif item == '总资产周转率':    # “营业收入”除以“平均资产总计”
            if conf.table_id == 0:
                continue
            
            # Select subtables
            income_table = 'Income_Statement'
            balance_table = 'Balance_Sheet'
            tables = [income_table, balance_table]
            income_df = pd.DataFrame(data[income_table]['rows'], columns=data[income_table]['headers'])
            balance_df = pd.DataFrame(data[balance_table]['rows'], columns=data[balance_table]['headers'])
            income_row = income_df.sample().iloc[0]
            if income_row['年度'] == '2021':
                income_row = income_df[(income_df['股票代码'] == income_row['股票代码']) & (income_df['年度'] == '2022')].iloc[0]
            balance_row = balance_df[(balance_df['股票代码'] == income_row['股票代码']) & (balance_df['截止日期'] == '2022-12-31')].iloc[0]
            previous_balance_row = balance_df[(balance_df['股票代码'] == income_row['股票代码']) & (balance_df['截止日期'] == '2021-12-31')].iloc[0]
            
            # Generate answer
            if str(income_row['营业收入']) == 'nan' or str(balance_row['资产总计']) == 'nan' or str(previous_balance_row['资产总计']) == 'nan':
                continue
            answer = str(float(income_row['营业收入']) / ((float(balance_row['资产总计']) + float(previous_balance_row['资产总计'])) / 2))

            # Generate question and sql
            question = f"股票简称为{income_row['股票简称']}的公司的总资产周转率是多少？"
            sql = f"SELECT (SELECT 营业收入 FROM {income_table} WHERE 股票简称 = '{income_row['股票简称']}' AND 年度 = '2022') / (((SELECT 资产总计 FROM {balance_table} WHERE 股票简称 = '{balance_row['股票简称']}' AND 截止日期 = '2022-12-31') + (SELECT 资产总计 FROM {balance_table} WHERE 股票简称 = '{previous_balance_row['股票简称']}' AND 截止日期 = '2021-12-31')) / 2) AS 总资产周转率"

        # Skip duplicate questions
        if any(qa_pair['question'] == question for qa_pair in qa_pairs):
            continue

        # Create a dictionary for the QA pair
        qa_pair = {
            "id": idx + count,
            "type": "numerical reasoning: multi table",
            "question": question,
            "tables": tables,
            "sql": sql,
            "answer": answer
        }

        # Check if sql is correct
        try:
            sql_answer = sql_to_answer(conf.db_path, sql)
            if sql_answer != answer:
                print(f"SQL query failed in \n{qa_pair}")
                print(f"SQL query return {sql_answer} != {answer}")
                continue
        except Exception as e:
            print(f"Error while executing SQL in \n{qa_pair}: \n{e}")
            continue

        # Append to the list
        qa_pairs.append(qa_pair)
        count += 1
        print(f"Generating Multi-table Numerical Reasoning Questions: {count}/{num_questions}")

    return qa_pairs


def generate_table_reasoning_questions(idx, data, num_questions):
    qa_pairs = []
    count = 0

    while count < num_questions:
        """最值查询"""
        # Randomly select a subtable
        table = random.choice(list(data.keys()))
        dataframe = pd.DataFrame(data[table]['rows'], columns=data[table]['headers'])
        col = random.choice([c for c in dataframe.columns if c not in ['股票代码', '股票简称', '截止日期', '年度', '公司全称']])

        # Randomly decide to query for max or min value
        reasoning_type = random.choice(["MAX", "MIN"])
        ordering = "DESC" if reasoning_type == "MAX" else "ASC"
        reasoning_question = "最大" if reasoning_type == "MAX" else "最小"

        # Generate question and SQL query
        # sql = f"SELECT 公司全称 FROM {table} WHERE {col} = (SELECT {reasoning_type}({col}) FROM {table})"
        if table == 'Balance_Sheet':
            question = f"截止到2022-12-31，哪家公司在{col}上的值是{reasoning_question}的？"
            sql = f"SELECT 公司全称 FROM {table} WHERE 截止日期 = '2022-12-31' ORDER BY {col} {ordering} LIMIT 1"
        else:
            question = f"2022年度，哪家公司在{col}上的值是{reasoning_question}的？"
            sql = f"SELECT 公司全称 FROM {table} WHERE 年度 = '2022' ORDER BY {col} {ordering} LIMIT 1"

        # Assuming sql_to_answer function executes the SQL and returns the result
        answer = sql_to_answer(conf.db_path, sql)
        if answer == 'nan' or answer == 'None':
            continue

        # Skip duplicate questions
        if any(qa_pair['question'] == question for qa_pair in qa_pairs):
            continue

        # Create a dictionary for the QA pair and append to the list
        qa_pair = {
            "id": idx + count,
            "type": "table reasoning",
            "question": question,
            "tables": [table],
            "sql": sql,
            "answer": answer
        }
        qa_pairs.append(qa_pair)
        count += 1
        print(f"Generating Questions with table reasoning: {count}/{num_questions}")

    return qa_pairs


def generate_fuzzy_questions(idx, data, num_questions):
    qa_pairs = []
    count = 0

    while count < num_questions:
        """模糊公司名称查询"""
        # Randomly select a subtable
        table = random.choice(list(data.keys()))
        dataframe = pd.DataFrame(data[table]['rows'], columns=data[table]['headers'])
        row = dataframe.sample().iloc[0]
        col = random.choice([c for c in dataframe.columns if c not in ['股票代码', '股票简称', '截止日期', '年度', '公司全称']])
        value = row[col]

        # Generate answer
        answer = str(value)
        if answer == 'nan':
            continue
        
        # Generate question and sql
        name = row['公司全称'].replace("(集团)", "").replace("股份", "").replace("有限", "").replace("公司", "")
        if conf.table_id == 0:
            question = f"{name}的{col}是多少？"
            sql = f"SELECT `{col}` FROM {table} WHERE `公司全称` LIKE '%{name}%'"
        else:
            year = str(row['截止日期']).split('-')[0] if table == 'Balance_Sheet' else str(row['年度'])
            question = f"{year}年{name}的{col}是多少？"
            sql = f"SELECT `{col}` FROM {table} WHERE `公司全称` LIKE '%{name}%' AND {'截止日期' if table == 'Balance_Sheet' else '年度'} LIKE '%{year}%'"

        # Create a dictionary for the QA pair
        qa_pair = {
            "id": idx + count,
            "type": "fuzzy",
            "question": question,
            "tables": [table],
            "sql": sql,
            "answer": answer
        }

        # Check if sql is correct
        try:
            sql_answer = sql_to_answer(conf.db_path, sql)
            if sql_answer != answer:
                print(f"SQL query failed in \n{qa_pair}")
                print(f"SQL query return {sql_answer} != {answer}")
                continue
        except Exception as e:
            print(f"Error while executing SQL in \n{qa_pair}: \n{e}")
            continue

        # Append to the list
        qa_pairs.append(qa_pair)
        count += 1
        print(f"Generating Fuzzy Questions: {count}/{num_questions}")

    return qa_pairs


if __name__ == "__main__":
    qa_pairs = []
    count_questions = 0

    # Load the tables from the JSON file
    with open(conf.json_path, 'r', encoding='utf-8') as f:
        tables = json.load(f)

    # Generate one-step questions
    one_step_questions = generate_one_step_questions(count_questions, tables, conf.num_one_step_questions)
    count_questions += conf.num_one_step_questions
    qa_pairs.extend(one_step_questions)

    # Generate multi-step questions
    multi_step_questions = generate_multi_step_questions(count_questions, tables, conf.num_multi_step_questions)
    count_questions += conf.num_multi_step_questions
    qa_pairs.extend(multi_step_questions)

    # Generate multi-table questions
    multi_table_questions = gengrate_multi_table_questions(count_questions, tables, conf.num_multi_table_questions)
    count_questions += conf.num_multi_table_questions
    qa_pairs.extend(multi_table_questions)

    # Generate table-reasoning questions
    table_reasoning_questions = generate_table_reasoning_questions(count_questions, tables, conf.num_table_reasoning_questions)
    count_questions += conf.num_table_reasoning_questions
    qa_pairs.extend(table_reasoning_questions)

    # Generate fuzzy questions
    fuzzy_questions = generate_fuzzy_questions(count_questions, tables, conf.num_fuzzy_questions)
    count_questions += conf.num_fuzzy_questions
    qa_pairs.extend(fuzzy_questions)

    # Write the QA pairs to a JSON file
    with open(conf.qa_pairs_path, 'w', encoding='utf-8') as file:
        json.dump(qa_pairs, file, ensure_ascii=False, indent=4)
    
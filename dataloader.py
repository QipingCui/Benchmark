import json
import pandas as pd
import sqlite3

from config import parameters_for_dataloader as conf
from utils import *


def read_company_names(excel_path):
    # 读取包含公司全称的Excel文件
    company_info_df = pd.read_excel(excel_path)
    # 将股票代码和公司全称转换成字典
    company_dict = pd.Series(company_info_df['公司全称'].values, index=company_info_df['股票代码']).to_dict()
    return company_dict


def convert_excel_to_json(excel_paths, info_path, json_path, limit):
    output_json = {}
    company_names = read_company_names(info_path)

    for table_name, excel_path in excel_paths.items():
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        # 限制行数
        if limit:
            df = df.head(limit)
        # 添加公司全称列
        df['公司全称'] = df['股票代码'].map(company_names)
        # 将所有数据转换为字符串类型
        df = df.astype(str)
        print(f"{table_name}\n{df.head()}")
        # 将列名和数据行转换为所需格式并添加到输出JSON
        output_json[table_name] = {
            "headers": list(df.columns),
            "rows": df.values.tolist()
        }

    # 写入JSON文件
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(output_json, ensure_ascii=False, indent=4))

    print(f"文件已成功转换为 '{json_path}'")


def convert_excel_to_sqlite(excel_paths, info_path, db_path, limit):
    """ Convert multiple Excel files to SQLite database. """
    company_names = read_company_names(info_path)
    # 创建SQLite数据库连接
    with sqlite3.connect(db_path) as conn:
        for table_name, excel_path in excel_paths.items():
            # 读取Excel文件
            df = pd.read_excel(excel_path)
            # 限制行数
            if limit:
                df = df.head(limit)
            # 添加公司全称列
            df['公司全称'] = df['股票代码'].map(company_names)
            # 将数据导入SQLite表中
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"Data from '{excel_path}' has been loaded into '{db_path}' in the table '{table_name}'.")
    view_database_structure(db_path)
    

if __name__ == '__main__':
    convert_excel_to_json(conf.excel_paths, conf.info_path, conf.json_path, conf.limit)
    convert_excel_to_sqlite(conf.excel_paths, conf.info_path, conf.db_path, conf.limit)

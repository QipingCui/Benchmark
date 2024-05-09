import json

from config import parameters_for_dataloader as conf


def transform_json(input_path, output_path):
    # 读取原始JSON文件
    with open(input_path, 'rb') as file:
        data = json.load(file)
    
    # 定义文本类型的列
    text_columns = ['股票代码', '股票简称', '截止日期', '年度', '公司全称']

    # 构建新的JSON结构
    transformed_data = {
        "column_names": [],
        "column_names_original": [],
        "column_types": [],
        "db_id": "financial_statements",
        "foreign_keys": [],
        "primary_keys": [],
        "table_names": [],
        "table_names_original": []
    }

    table_index = 0
    column_index = 0

    for key, value in data.items():
        # 添加表名和原始表名
        transformed_data['table_names'].append(key.replace("_", " ").title())
        transformed_data['table_names_original'].append(key)

        # 如果有头信息，则处理列
        if 'headers' in value and value['headers']:
            for header in value['headers']:
                # 假设所有列都是数字类型
                column_type = "text" if header in text_columns else "number"
                transformed_data['column_names'].append([table_index, header.lower()])
                transformed_data['column_names_original'].append([table_index, header])
                transformed_data['column_types'].append(column_type)
                column_index += 1
        transformed_data['primary_keys'].append(table_index)
        table_index += 1

    # 保存转换后的JSON数据
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump([transformed_data], file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    output_file = conf.json_path.replace(".json", "_for_structgpt_for_text2sql.json")
    transform_json(conf.json_path, output_file)

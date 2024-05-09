import pandas as pd
import glob

from config import parameters_for_evaluation as conf
from utils import *


def evaluate_predictions(true_values, predictions, sql_flag):
    # 读取JSON文件
    real_df = pd.read_json(true_values)
    pred_df = pd.read_json(predictions, encoding='gb2312')

    # 应用标准化函数
    if sql_flag:
        pred_df['sql'] = pred_df['sql'].apply(normalize_sql)
        real_df['sql'] = real_df['sql'].apply(normalize_sql)

    # 合并DataFrame，基于'id'字段，只考虑预测JSON文件中的项
    merged_df = pd.merge(pred_df, real_df, on='id', how='left', suffixes=('_pred', '_real'))
    merged_df.drop(columns=['type_real', 'question_real', 'tables_real'], inplace=True)
    merged_df.rename(columns={'type_pred': 'type', 'question_pred': 'question', 'tables_pred': 'tables'}, inplace=True)
    if not sql_flag:
        merged_df.drop(columns=['sql'], inplace=True)

    # 比较答案和SQL
    merged_df['answer_correct'] = merged_df['answer_pred'] == merged_df['answer_real']
    # merged_df['answer_correct'] = merged_df.apply(lambda row: almost_equal(row['answer_pred'], row['answer_real'], get_significant_figures(row['answer_pred'])), axis=1)
    if sql_flag:
        merged_df['sql_correct'] = merged_df['sql_pred'] == merged_df['sql_real']

    # 计算准确率
    answer_accuracy = merged_df['answer_correct'].mean()
    sql_accuracy = merged_df['sql_correct'].mean() if sql_flag else None

    # 计算不同类型的准确率
    if sql_flag:
        accuracy_by_type = merged_df.groupby('type').agg({
            'answer_correct': 'mean',  # 答案准确率
            'sql_correct': 'mean'      # SQL准确率
        }).reset_index()
    else:
        accuracy_by_type = merged_df.groupby('type').agg({
            'answer_correct': 'mean'  # 答案准确率
        }).reset_index()

    # 生成最终的评估结果JSON文件
    if sql_flag:
        new_order = ['id', 'type', 'question', 'tables', 'sql_pred', 'sql_real', 'sql_correct', 'answer_pred', 'answer_real', 'answer_correct']
    else:
        new_order = ['id', 'type', 'question', 'tables', 'answer_pred', 'answer_real', 'answer_correct']
    merged_df = merged_df[new_order]
    output_file = predictions.replace('predictions', 'evaluation')
    merged_df.to_json(output_file, orient='records', force_ascii=False)

    return answer_accuracy, sql_accuracy, accuracy_by_type


if __name__ == '__main__':
    prediction_path = f"{conf.output_path}/predictions_*.json"
    prediction_path = glob.glob(prediction_path)[-1]
    accuracy_answers, accuracy_sql, accuracy_by_type = evaluate_predictions(conf.qa_pairs_path, prediction_path, conf.sql)
    print(f"Answer Accuracy: {accuracy_answers * 100:.2f}%")
    if conf.sql:
        print(f"SQL Accuracy: {accuracy_sql * 100:.2f}%")
    print(f"Accuracy by Question Type:\n{accuracy_by_type}")

    output_file_path = prediction_path.replace('json', 'txt').replace('predictions', 'evaluation')
    with open(output_file_path, 'w') as file:
        file.write(f"Answer Accuracy: {accuracy_answers * 100:.2f}%\n")
        if conf.sql:
            file.write(f"SQL Accuracy: {accuracy_sql * 100:.2f}%\n")
        file.write(f"Accuracy by Question Type:\n{accuracy_by_type}\n")

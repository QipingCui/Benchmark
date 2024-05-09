import decimal
import pandas as pd
import re
import sqlite3


def view_database_structure(db_path):
    """ View the structure of the specified SQLite database. """
    # Connect to the SQLite database
    with sqlite3.connect(db_path) as conn:
        # Retrieve a list of all tables in the database
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Print the structure of each table
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  Column: {col[1]}, Type: {col[2]}")


def sql_to_answer(db, sql):
    """ Execute SQL query on the SQLite database and return results. """
    try:
        with sqlite3.connect(db) as conn:
            answer = str(pd.read_sql_query(sql, conn).iloc[-1, -1])
        return answer
    except Exception as e:
        print(e)
        return "nan"


def normalize_sql(sql):
    """标准化SQL语句，移除多余的空格和换行符，并将所有字符转换为小写"""
    return ' '.join(sql.replace('\n', ' ').split()).lower()


def almost_equal(pred, real, sig_fig):
    # 清除数字中的分隔符
    pred = pred.replace(',', '')
    real = real.replace(',', '')

    # 尝试将输入转换为Decimal类型，这有助于保持精度
    try:
        d_pred = decimal.Decimal(pred)
        d_real = decimal.Decimal(real)
    except decimal.InvalidOperation:
        return False

    # 获取两个数的差的绝对值
    diff = abs(d_pred - d_real)
    if diff == 0:
        return True

    # 设置有效数字的精度
    decimal.getcontext().prec = sig_fig

    # 比较有效数字位数的相等性
    return diff < decimal.Decimal(1) / (decimal.Decimal(10) ** sig_fig)


# 计算预测答案的有效数字位数
def get_significant_figures(num):
    # 移除数字中的无效零和小数点
    if '.' in num:
        return len(num.split('.')[1])  # 返回小数点后的位数
    return 0


def extract_sql(response_text):
    # 使用正则表达式查找以```sql开头至```结束的区块
    match = re.search(r"```sql\n(.*?)\n```", response_text, re.DOTALL)
    if match:
        # 返回找到的SQL查询语句
        return match.group(1)
    else:
        # 如果没有找到匹配项，返回空字符串或适当的错误消息
        return "No SQL statement found."
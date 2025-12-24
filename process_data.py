#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接处理上传的CSV文件并更新latest_data.csv
"""
import pandas as pd
import os
import sys

# 判断是否在SCF环境
def is_scf_environment():
    return 'TENCENTCLOUD_RUNENV' in os.environ

# 数据存储路径处理
if is_scf_environment():
    # SCF环境：使用/tmp目录（可写）
    DATA_DIR = '/tmp/data'
else:
    # 本地环境
    DATA_DIR = 'data'

# 添加当前目录到路径，以便导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor import process_lixingren_csv

def main():
    # 设置文件路径
    uploaded_dir = os.path.join(DATA_DIR, 'uploaded')
    latest_csv = os.path.join(uploaded_dir, '2025-12-24.csv')
    output_file = os.path.join(DATA_DIR, 'latest_data.csv')
    
    # 检查文件是否存在
    if not os.path.exists(latest_csv):
        return 1
    
    # 处理数据
    try:
        result_df = process_lixingren_csv(latest_csv)
        if result_df is not None:
            # 保存处理后的数据
            result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            return 0
        else:
            return 1
    except Exception as e:
        return 1

if __name__ == '__main__':
    sys.exit(main())
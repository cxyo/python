# data_processor.py
import pandas as pd
import numpy as np
from datetime import datetime
import os
from index_categories import get_index_category, is_industry_index

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

def calculate_fund_temperature(pe, pb, pe_hist_high=None, pe_hist_low=None, 
                               pb_hist_high=None, pb_hist_low=None):
    """
    计算基金温度
    算法：温度 = (PE分位点 * 0.5 + PB分位点 * 0.5) * 100
    """
    # 如果CSV里已经有分位点，优先使用
    # 这里假设CSV列名为：'指数名称', 'PE', 'PB', 'PE分位点', 'PB分位点'
    
    # 如果没有分位点，用简单算法估算
    if pd.isna(pe) or pd.isna(pb):
        return 50.0  # 默认值
    
    # 改进的温度算法，基于实际PE和PB值的历史范围
    # PE温度：更合理的映射，考虑到不同指数的PE差异
    # 使用对数缩放使温度变化更平滑
    import math
    
    # PE温度计算
    if pe <= 0:
        pe_temp = 0
    elif pe > 50:
        pe_temp = 95
    else:
        # 使用对数映射，使温度在合理范围内分布
        # log(1) = 0, log(50) ≈ 3.912
        # 将PE映射到0-95的温度范围
        pe_temp = (math.log10(pe + 1) / math.log10(51)) * 95
    
    # PB温度计算
    if pb <= 0:
        pb_temp = 0
    elif pb > 10:
        pb_temp = 95
    else:
        # 同样使用对数映射，PB范围0-10
        # log(1) = 0, log(10) = 1
        pb_temp = (math.log10(pb + 0.5) / math.log10(10.5)) * 95
    
    # 综合温度（PE和PB各50%权重）
    temperature = pe_temp * 0.5 + pb_temp * 0.5
    return round(temperature, 1)

def process_lixingren_csv(file_path):
    """处理理杏仁CSV文件"""
    try:
        # 尝试不同编码读取
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except:
                pass
        
        if df is None:
            return None
        
        # 重命名列，统一格式（根据你的CSV实际列名修改）
        column_mapping = {
            '指数名称': '指数名称',
            '指数': '指数名称',
            'name': '指数名称',
            'PE': 'PE',
            '市盈率': 'PE',
            'pe': 'PE',
            'PE-TTM(当前值)': 'PE',
            'PB': 'PB',
            '市净率': 'PB',
            'pb': 'PB',
            'PE分位点': 'PE分位点',
            'PB分位点': 'PB分位点',
            'PE-TTM(分位点%)': 'PE分位点',
            'PB(分位点%)': 'PB分位点',
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # 计算基金温度
        if 'PE分位点' in df.columns and 'PB分位点' in df.columns:
            # 处理分位点数据，转换为数值
            def process_quantile(quantile):
                if pd.isna(quantile) or quantile == '-' or quantile == '':
                    return 0
                elif isinstance(quantile, str):
                    # 处理前面带等号的情况（如=0.8210）
                    if quantile.startswith('='):
                        quantile = quantile[1:]
                    # 处理百分比的情况（如82.10%）
                    if '%' in quantile:
                        return float(quantile.replace('%', '')) / 100
                    # 处理普通数值字符串
                    try:
                        return float(quantile)
                    except ValueError:
                        return 0
                elif isinstance(quantile, (int, float)):
                    return quantile / 100 if quantile > 1 else quantile
                else:
                    return 0
            
            # 应用分位点处理函数
            df['PE分位点数值'] = df['PE分位点'].apply(process_quantile)
            df['PB分位点数值'] = df['PB分位点'].apply(process_quantile)
            
            # 根据指数类型计算基金温度
            df['基金温度'] = df.apply(lambda row: 
                row['PB分位点数值'] * 100 if is_industry_index(row['指数名称']) 
                else (row['PE分位点数值'] + row['PB分位点数值']) / 2 * 100, axis=1)
            
            df['基金温度'] = df['基金温度'].round(1)
        else:
            # 用自定义函数计算
            df['基金温度'] = df.apply(
                lambda row: calculate_fund_temperature(
                    row.get('PE', 15),  # 默认值15
                    row.get('PB', 1.5)   # 默认值1.5
                ), axis=1
            )
        
        # 添加投资建议
        def get_advice(temp):
            if temp < 30:
                return "低估区域，可考虑定投"
            elif temp < 50:
                return "正常偏低，可继续持有"
            elif temp < 70:
                return "正常偏高，注意风险"
            else:
                return "高估区域，考虑减仓"
        
        df['投资建议'] = df['基金温度'].apply(get_advice)
        
        # 添加更新时间
        df['数据更新时间'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 删除没有数据的行
        # 删除PE分位点和PB分位点没有数据的行
        if 'PE分位点' in df.columns and 'PB分位点' in df.columns:
            # 排除PE分位点或PB分位点为空、为'-'或为0的行
            valid_quantiles = (df['PE分位点'] != '-') & (df['PB分位点'] != '-')
            valid_quantiles &= ~pd.isna(df['PE分位点']) & ~pd.isna(df['PB分位点'])
            
            # 排除'0'或'0%'值
            valid_quantiles &= (df['PE分位点'] != '0') & (df['PE分位点'] != '0%')
            valid_quantiles &= (df['PB分位点'] != '0') & (df['PB分位点'] != '0%')
            
            # 检查是否为数值类型，如果是，排除0值
            if pd.api.types.is_numeric_dtype(df['PE分位点']) and pd.api.types.is_numeric_dtype(df['PB分位点']):
                valid_quantiles &= (df['PE分位点'] != 0) & (df['PB分位点'] != 0)
            
            df = df[valid_quantiles]
        
        # 清除计算报错的行（基金温度为0或为空的行）
        if '基金温度' in df.columns:
            # 检查是否为数值类型
            if pd.api.types.is_numeric_dtype(df['基金温度']):
                # 排除0值和空值
                df = df[(df['基金温度'] != 0) & ~pd.isna(df['基金温度'])]
        
        # 如果过滤后没有数据，返回None
        if df.empty:
            return None
        
        # 处理关注度为数值类型以便排序
        if '关注度' in df.columns:
            def process_attention(x):
                if not isinstance(x, str):
                    return 0
                if x == '-' or x == '':
                    return 0
                # 移除等号
                x = x.replace('=', '')
                # 移除千位分隔符
                x = x.replace(',', '')
                try:
                    return float(x)
                except ValueError:
                    return 0
            
            df['关注度数值'] = df['关注度'].apply(process_attention)
        else:
            df['关注度数值'] = 0
        
        # 定义类别排序顺序
        category_order = ['大盘', '小盘', '策略', '行业', '主题', '海外', '其他']
        
        # 添加类别字段（如果不存在）
        if '类别' not in df.columns and '指数名称' in df.columns:
            df['类别'] = df['指数名称'].apply(get_index_category)
        
        df['类别排序'] = df['类别'].map({cat: idx for idx, cat in enumerate(category_order)})
        
        # 排序：先按关注度降序，再按类别排序，最后按基金温度降序
        df = df.sort_values(by=['关注度数值', '类别排序', '基金温度'], ascending=[False, True, False])
        
        return df
        
    except Exception as e:
        print(f"处理CSV时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_processed_data(df, filename):
    """保存处理后的数据"""
    if df is None or df.empty:
        return False
    
    processed_dir = os.path.join(DATA_DIR, 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    file_path = os.path.join(processed_dir, filename)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"数据已保存: {file_path}")
    return True
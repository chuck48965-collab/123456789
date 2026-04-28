"""
llm_naming.py
Generate sociological cluster names and descriptions using Doubao (ByteDance).
"""

import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv('DOUBAO_MODEL', 'ark-313c37df-5144-4a39-b675-d71e54e48932-d871c')
DEFAULT_MAX_TOKENS = 180
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1
DEFAULT_TIMEOUT_SECONDS = 15.0

SYSTEM_PROMPT = (
    'You are a sociologist and urban planner. Based on the demographic and economic data provided, '
    'give the neighborhood a concise, descriptive name (e.g., "Affluent Suburbs", "Urban Struggling Communities", "Hispanic Working Class") '
    'and a 2-sentence description.'
)


def generate_cluster_names(stats_dict):
    """
    Generate cluster names and descriptions using Doubao.

    Parameters:
        stats_dict (dict): {cluster_id: {'Income': ..., 'Education': ..., 'Employment': ..., 'Diversity': ...}}

    Returns:
        dict: {cluster_id: {'name': ..., 'description': ...}}
    """
    api_key = os.getenv('DOUBAO_API_KEY')

    if not api_key:
        print('DOUBAO_API_KEY 未设置，使用本地回退名称。')
        return _default_names(stats_dict, reason='missing_api_key')

    try:
        client = OpenAI(api_key=api_key, base_url="https://ark.cn-beijing.volces.com/api/v3")
    except Exception as e:
        print(f'Doubao 客户端初始化失败：{e}')
        return _default_names(stats_dict, reason='client_init_failed')

    results = {}
    for cluster_id, stats in stats_dict.items():
        print(f'正在为 Cluster {cluster_id} 生成名称...')
        name, description = _generate_name_description(client, cluster_id, stats)
        if not name or not description:
            results[cluster_id] = _heuristic_name_description(stats, 'api_error')
        else:
            results[cluster_id] = {'name': name, 'description': description}

    return results


def _generate_name_description(client, cluster_id, stats):
    prompt = _build_prompt(cluster_id, stats)
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            name, description = _parse_response(content)
            if name and description:
                return name, description
            raise ValueError('API 返回的内容无法解析为名称和描述。')
        except Exception as e:
            err_msg = str(e)
            if '402' in err_msg or 'Insufficient Balance' in err_msg or 'invalid_request_error' in err_msg:
                print(f'Cluster {cluster_id} DeepSeek 余额不足，已使用默认名称。原因: {e}')
                break
            if attempt == RETRY_ATTEMPTS:
                print(f'Cluster {cluster_id} API 调用失败，已使用默认名称。原因: {e}')
            else:
                time.sleep(RETRY_DELAY_SECONDS)
    return None, None


def _build_prompt(cluster_id, stats):
    return (
        f"Data: Income: ${stats['Income']:.2f}, Education: {stats['Education']:.2f}%, "
        f"Employment: {stats['Employment']:.2f}%, Diversity: {stats['Diversity']:.2f}%. "
        "Provide a name and a 2-sentence description."
    )


def _extract_content(response):
    if isinstance(response, str):
        return response.strip()
    if hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        if hasattr(choice, 'message') and choice.message:
            return choice.message.content.strip()
        if hasattr(choice, 'text'):
            return choice.text.strip()
    raise ValueError('无法从 Doubao 响应中提取内容。')


def _parse_response(content):
    name = ''
    description = ''
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith('name:'):
            name = stripped.split(':', 1)[1].strip()
        elif stripped.lower().startswith('description:'):
            description = stripped.split(':', 1)[1].strip()

    if not name or not description:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if lines:
            if not name:
                name = lines[0]
            if not description:
                description = ' '.join(lines[1:])
    return name, description


def _default_names(stats_dict, reason='api_error'):
    return {
        cluster_id: _heuristic_name_description(stats, reason)
        for cluster_id, stats in stats_dict.items()
    }


def _heuristic_name_description(stats, reason):
    income = stats['Income']
    education = stats['Education']
    employment = stats['Employment']
    diversity = stats['Diversity']

    if income >= 70000:
        income_label = 'Affluent'
    elif income <= 40000:
        income_label = 'Low-income'
    else:
        income_label = 'Middle-income'

    if education >= 60:
        education_label = 'Highly Educated'
    elif education <= 30:
        education_label = 'Lower Education'
    else:
        education_label = 'Moderately Educated'

    employment_label = 'Underemployed' if employment < 50 else 'Employed'

    name = f"{income_label} {education_label} Neighborhoods"
    description = (
        f"This cluster is characterized by {income_label.lower()} households, {education_label.lower()} levels, "
        f"and {employment_label.lower()} rates with approx. {diversity:.0f}% population diversity. "
        f"(本地回退名称，原因：{reason})"
    )

    return {'name': name, 'description': description}


if __name__ == '__main__':
    sample_stats = {
        0: {'Income': 55000, 'Education': 35.5, 'Employment': 5.2, 'Diversity': 39.9},
        1: {'Income': 42000, 'Education': 22.0, 'Employment': 12.5, 'Diversity': 71.7}
    }
    result = generate_cluster_names(sample_stats)
    print('生成结果：')
    for cluster_id, info in result.items():
        print(f'Cluster {cluster_id}: name={info["name"]}, description={info["description"]}')

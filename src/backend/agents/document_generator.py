import os
import json
import subprocess
from .state import AgentState

def document_generator_node(state: AgentState):
    """
    Document Generator Node:
    1. 取 structured_data（来自 analyst）+ scores（来自 scorer）
    2. 调用 Node.js docx 生成脚本
    3. 返回文件路径
    """
    print(f"\n--- [Doc Generator] Generating DOCX for: {state.get('name')} ---")
    
    name = state.get('name', 'Company')
    structured_data = state.get('structured_data', {})
    scores = state.get('scores', {})
    vote_summary = state.get('vote_summary', '')
    final_score = state.get('final_score', 0)
    
    if not structured_data:
        print("⚠️ No structured data available, skipping doc generation")
        return {"docx_output_path": None}
    
    # 合并 scorer 的分数进 structured_data
    structured_data['scorecard'] = [
        {"dimension": "Team DNA",          "score": scores.get('team_dna', 0)},
        {"dimension": "Category Creation", "score": scores.get('category', 0)},
        {"dimension": "Moat Strength",     "score": scores.get('moat', 0)},
        {"dimension": "Economics",         "score": scores.get('economics', 0)},
        {"dimension": "Overall Conviction","score": round(final_score)},
    ]
    structured_data['vote_summary'] = vote_summary
    
    # 写入临时 JSON 文件
    temp_json_path = f"/tmp/{name.replace(' ', '_')}_data.json"
    output_path = f"/tmp/{name.replace(' ', '_')}_memo.docx"
    
    with open(temp_json_path, 'w') as f:
        json.dump(structured_data, f, indent=2)
    
    # 调用 Node.js 脚本生成 docx
    agents_dir = os.path.dirname(__file__)
    script_path = os.path.join(agents_dir, 'generate_memo.js')
    
    result = subprocess.run(
        ['node', 'generate_memo.js', temp_json_path, output_path],
        capture_output=True, 
        text=True,
        cwd=agents_dir  # 确保在 agents 目录下运行，以便找到 node_modules
    )
    
    if result.returncode == 0:
        print(f"✅ DOCX generated: {output_path}")
        return {"docx_output_path": output_path}
    else:
        print(f"❌ DOCX generation failed: {result.stderr}")
        return {"docx_output_path": None}

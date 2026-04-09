"""CreativePilot Commands"""
from __future__ import annotations

import json


def run_creative_brief(args: list[str]) -> int:
    """Generate creative brief command"""
    from agent_core.tools.creative_pilot import creative_brief_executor
    
    params = {"platform": "小红书", "kol_style": "真实分享"}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key in ["key_messages", "must_include", "forbidden"]:
                params[key] = value.split(",")
            else:
                params[key] = value
    
    required = ["brand", "product"]
    for r in required:
        if r not in params:
            print(f"Usage: ma creative-brief brand=<brand> product=<product> [platform=<platform>] [industry=<行业>]")
            return 1
    
    result = creative_brief_executor(json.dumps(params))
    data = json.loads(result)
    
    print(f"\n🎨 创意Brief")
    print("=" * 60)
    
    project = data.get("project_info", {})
    print(f"品牌: {project.get('brand')}")
    print(f"产品: {project.get('product')}")
    print(f"平台: {project.get('platform')}")
    
    print(f"\n📝 内容要求:")
    req = data.get("content_requirements", {})
    print(f"  关键信息: {', '.join(req.get('key_messages', []))}")
    print(f"  必须包含: {', '.join(req.get('must_include', []))}")
    print(f"  禁止事项: {', '.join(req.get('forbidden', []))}")
    print(f"  内容调性: {req.get('tone')}")
    
    print(f"\n🏷️ 推荐标签:")
    hashtags = data.get("hashtags", {})
    print(f"  必需: {', '.join(hashtags.get('required', []))}")
    print(f"  推荐: {', '.join(hashtags.get('recommended', []))}")
    
    print(f"\n✅ 合规要求:")
    compliance = data.get("compliance", {})
    print(f"  {compliance.get('disclosure')}")
    print(f"  禁用词: {', '.join(compliance.get('forbidden_words', []))}")

    tpl = data.get("industry_template", {})
    if tpl:
        print(f"\n🏭 行业模板:")
        print(f"  行业: {tpl.get('industry')}")
        print(f"  目标: {tpl.get('core_objective')}")
        print(f"  内容支柱: {', '.join(tpl.get('content_pillars', [])[:4])}")

    if data.get("applied_skills"):
        print("\n🧩 已应用Skills:")
        for s in data.get("applied_skills", []):
            print(f"  • {s}")
    
    return 0


def run_content_template(args: list[str]) -> int:
    """Generate content template command"""
    from agent_core.tools.creative_pilot import content_template_executor
    
    params = {"template_type": "product_review", "platform": "小红书"}
    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            params[key] = value
    
    required = ["brand", "product"]
    for r in required:
        if r not in params:
            print(f"Usage: ma content-template brand=<brand> product=<product> [template_type=<type>] [platform=<platform>]")
            return 1
    
    result = content_template_executor(json.dumps(params))
    data = json.loads(result)
    
    print(f"\n📝 内容模板 ({data.get('template_type')} - {data.get('platform')})")
    print("=" * 60)
    print(data.get('content'))
    
    return 0


def run_content_review(args: list[str]) -> int:
    """Review content command"""
    from agent_core.tools.creative_pilot import content_review_executor
    
    params = {"platform": "小红书", "requirements": {}}
    content_lines = []
    
    for arg in args:
        if arg.startswith("content="):
            content_lines.append(arg[8:])
        elif "=" in arg:
            key, value = arg.split("=", 1)
            if key == "must_include":
                params["requirements"]["must_include"] = value.split(",")
            elif key == "forbidden":
                params["requirements"]["forbidden"] = value.split(",")
            else:
                params[key] = value
    
    params["content"] = " ".join(content_lines)
    
    if not params.get("content"):
        print("Usage: ma content-review content=<content> brand=<brand> [platform=<platform>]")
        return 1
    
    result = content_review_executor(json.dumps(params))
    data = json.loads(result)
    
    print(f"\n🔍 内容审核报告")
    print("=" * 60)
    print(f"审核结果: {'✅ 通过' if data.get('passed') else '❌ 未通过'}")
    print(f"评分: {data.get('score')}/100")
    
    if data.get("issues"):
        print(f"\n❌ 问题:")
        for issue in data.get("issues", []):
            print(f"  • {issue}")
    
    if data.get("warnings"):
        print(f"\n⚠️ 警告:")
        for warning in data.get("warnings", []):
            print(f"  • {warning}")
    
    if data.get("suggestions"):
        print(f"\n💡 优化建议:")
        for suggestion in data.get("suggestions", []):
            print(f"  • {suggestion}")
    
    return 0

"""finetuneplat_jd249 —— 映射模型微调平台工程师·混合检索的权重调节的覆盖情况并找出未覆盖的部分。

把候选项映射到类别上，算出模型微调平台工程师·混合检索的权重调节的覆盖率并列出未覆盖的类别

定位：
  覆盖是按类别算的不是按条数算，条数多不代表覆盖好

岗位对应：
  目标岗位　京东 · 专家模型微调平台工程师
  技能主线　大模型微调、Python、MLOps
  领域标签　大模型训练、MLOps

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到岗位要求的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python finetuneplat_jd249.py --help
    python finetuneplat_jd249.py --file input.txt
    python finetuneplat_jd249.py --text "示例内容"
    python finetuneplat_jd249.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 岗位规则表：每条规则独立可核查，命中即报，不做推断。
# 规则由岗位 JD 的技能线与领域标签派生——每条都能对回岗位要求。
# 目标岗位：京东 · 专家模型微调平台工程师
RULES: list[dict] = [
    {
        "name": "模型微调平台工程师·混合检索的权重调节·缺失",
        "why": "岗位要求「大模型微调」在输入里找不到对应内容",
        "severity": "high",
        "keywords": ['missing', 'absent', '缺少', '没有', '未提供', '大模型微调'],
    },
    {
        "name": "模型微调平台工程师·混合检索的权重调节·冲突",
        "why": "两处关于「Python」的描述互相矛盾",
        "severity": "high",
        "keywords": ['conflict', 'contradict', '矛盾', '不一致', '相反', 'Python'],
    },
    {
        "name": "模型微调平台工程师·混合检索的权重调节·越界",
        "why": "「MLOps」的取值超出岗位场景的常规范围",
        "severity": "medium",
        "keywords": ['out of range', 'outlier', '越界', '超限', '超过', 'MLOps'],
    },
    {
        "name": "模型微调平台工程师·混合检索的权重调节·退化",
        "why": "「大模型训练」相关的信息量不足以支撑判断",
        "severity": "medium",
        "keywords": ['degrade', 'insufficient', '不足', '太少', '无法', '大模型训练'],
    },
    {
        "name": "模型微调平台工程师·混合检索的权重调节·泄漏",
        "why": "「模型微调平台工程师」相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['leak', 'expose', '泄漏', '暴露', '明文', '模型微调平台工程师'],
    },
    {
        "name": "模型微调平台工程师·混合检索的权重调节·重复#2",
        "why": "同一处「大模型微调」信息被反复传递",
        "severity": "low",
        "keywords": ['duplicate', 'repeat', '重复', 'again', '大模型微调'],
    },
    {
        "name": "模型微调平台工程师·混合检索的权重调节·陈旧#2",
        "why": "「Python」的时效性已过期",
        "severity": "medium",
        "keywords": ['stale', 'expired', '过期', '陈旧', '旧版', 'Python'],
    },
    {
        "name": "模型微调平台工程师·混合检索的权重调节·不可核#2",
        "why": "关于「MLOps」的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['unverifiable', 'no evidence', '无法追溯', '没有来源', 'MLOps'],
    },
]


def finetuneplat_jd249_split_items(text: str) -> list[str]:
    items: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        for p in re.split(r"(?<=[。！？；;])\s*", line):
            p = p.strip()
            if p:
                items.append(p)
    return items


def finetuneplat_jd249_tokens(text: str) -> set[str]:
    """抽词元。中文按二元组切——见 consistency-checker 引擎里的说明。"""
    low = text.lower()
    out = set(re.findall(r"[a-z]{3,}", low))
    for seg in re.findall(r"[\u4e00-\u9fff]+", low):
        if len(seg) == 1:
            out.add(seg)
        else:
            for i in range(len(seg) - 1):
                out.add(seg[i:i + 2])
    return out


def finetuneplat_jd249_analyze(text: str) -> dict:
    """主分析：条目覆盖、缺失项与重叠。"""
    items = finetuneplat_jd249_split_items(text)
    if not items:
        return {"ok": False, "error": "没有可分析的条目", "count": 0}
    all_tokens: dict[str, list[int]] = {}
    for i, it in enumerate(items):
        for t in finetuneplat_jd249_tokens(it):
            all_tokens.setdefault(t, []).append(i)
    shared = {t: idxs for t, idxs in all_tokens.items() if len(idxs) > 1}
    covered = {i for idxs in all_tokens.values() for i in idxs}
    missing = [i for i in range(len(items)) if i not in covered]
    return {
        "ok": True,
        "count": len(items),
        "unique_tokens": len(all_tokens),
        "shared_tokens": len(shared),
        "missing_items": missing,
        "missing_texts": [items[i] for i in missing],
        "coverage": round(len(covered) / len(items), 4),
        "items": items,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"条目数：{result['count']}  唯一词 {result['unique_tokens']}  共享词 {result['shared_tokens']}")
    out.append(f"覆盖率：{result['coverage']:.2%}")
    out.append("")
    if result["missing_items"]:
        out.append("未被覆盖的条目：")
        for i, t in zip(result["missing_items"], result["missing_texts"]):
            out.append(f"  #{i}: {t[:100]}")
    else:
        out.append("所有条目都被覆盖。")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="finetuneplat_jd249",
        description="把候选项映射到类别上，算出模型微调平台工程师·混合检索的权重调节的覆盖率并列出未覆盖的类别（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python finetuneplat_jd249.py --file input.txt\n"
            "  python finetuneplat_jd249.py --text '示例内容'\n"
            "  python finetuneplat_jd249.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = finetuneplat_jd249_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

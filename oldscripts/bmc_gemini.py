"""
Generate a Business Model Canvas using the free Gemini API.

Setup
- Set `GEMINI_API_KEY` in your environment (Google AI Studio key).
- Install deps: `pip install -r requirements.txt`.

Usage
- CLI example:
  python bmc_gemini.py --product "Acme Analytics" --description "Self-serve BI for SMBs" --market "SMBs in retail"
- If no args are provided, the script will prompt interactively.
"""

import os
import argparse
from typing import Optional

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

import google.generativeai as genai


def get_api_key() -> Optional[str]:
    """Fetch GEMINI_API_KEY from env, loading .env if available."""
    if load_dotenv:
        load_dotenv()
    return os.getenv("GEMINI_API_KEY")


def build_prompt(product: str, description: str, market: str, extras: Optional[str] = None) -> str:
    """Create a clear, structured prompt for Business Model Canvas generation."""
    lines = [
        "You are a startup strategist. Create a concise Business Model Canvas.",
        f"Product: {product}",
        f"Description: {description}",
        f"Target Market: {market}",
        f"Additional Context: {extras or 'N/A'}",
        "Return the 9 standard sections with 3–6 bullet points each:",
        "- Customer Segments",
        "- Value Propositions",
        "- Channels",
        "- Customer Relationships",
        "- Revenue Streams",
        "- Key Activities",
        "- Key Resources",
        "- Key Partners",
        "- Cost Structure",
        "Keep outputs practical and specific. Avoid marketing fluff.",
    ]
    return "\n".join(lines)


def _choose_available_model() -> str:
    preferred = (
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro",
    )
    try:
        models = list(genai.list_models())
        supported = [
            m.name for m in models
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]
        # Prefer flash (free-tier friendly) and avoid experimental models
        flash = [n for n in supported if "flash" in n and "exp" not in n]
        if flash:
            return flash[0]
        pro = [n for n in supported if "pro" in n and "exp" not in n]
        if pro:
            return pro[0]
        # Try to match preferred aliases first
        for pref in preferred:
            for name in supported:
                if pref in name:
                    return name
        # Fallback to first supported if no preferred match
        if supported:
            return supported[0]
    except Exception:
        pass
    # Final fallback
    return preferred[0]


def generate_bmc(product: str, description: str, market: str, extras: Optional[str] = None) -> str:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY. Set it in your environment or .env file."
        )

    genai.configure(api_key=api_key)
    model_name = _choose_available_model()
    model = genai.GenerativeModel(model_name)
    prompt = build_prompt(product, description, market, extras)
    resp = model.generate_content(prompt)
    return resp.text or "(No content returned)"


def main():
    parser = argparse.ArgumentParser(description="Generate Business Model Canvas via Gemini")
    parser.add_argument("--product", required=False, help="Product or company name")
    parser.add_argument("--description", required=False, help="One-line product description")
    parser.add_argument("--market", required=False, help="Primary target market")
    parser.add_argument("--extras", required=False, help="Optional extra context, constraints, or goals")
    args = parser.parse_args()

    product = args.product or input("Product name: ").strip()
    description = args.description or input("One-line description: ").strip()
    market = args.market or input("Target market: ").strip()
    extras = args.extras or input("Additional context (optional): ").strip() or None

    try:
        canvas = generate_bmc(product, description, market, extras)
        print("\n=== Business Model Canvas ===\n")
        print(canvas)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
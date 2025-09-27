#!/usr/bin/env python3
"""
Startup Business Idea Evaluation Tool
====================================
This script evaluates business ideas using Google's Gemini AI and generates
a comprehensive report with scores, verdict, and actionable insights.

Features:
- Evaluates business ideas against 12 key criteria
- Provides GO/WAIT/NO-GO verdict
- Exports results to formatted text file
- Colored console output for better readability

Author: Business Evaluation Assistant
Version: 2.0
"""

import os
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Optional colored console output
try:
    from termcolor import colored
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    def colored(text, color=None, attrs=None):
        return text


class StartupEvaluator:
    """Main class for evaluating startup business ideas."""
    
    def __init__(self):
        """Initialize the evaluator with API configuration."""
        self.setup_api()
        self.model = genai.GenerativeModel("models/gemini-2.5-flash")
        self.evaluation_criteria = [
            "MarketNeed", "MarketSize", "ProductFit", "BusinessModel",
            "TeamCredibility", "ExecutionComplexity", "OverallViability",
            "CompetitiveAdvantage", "Scalability", "CustomerAcquisitionPotential",
            "FinancialSustainability", "InnovationLevel"
        ]
    
    def setup_api(self):
        """Load environment variables and configure Gemini API."""
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please check your .env file."
            )
        
        genai.configure(api_key=api_key)
        print(self._colored_print("✅ API configured successfully", "green"))
    
    def _colored_print(self, text, color=None, attrs=None):
        """Helper method for colored printing."""
        if COLORS_AVAILABLE:
            return colored(text, color, attrs)
        return text
    
    def load_business_idea(self, file_path):
        """
        Load business idea from text file.
        
        Args:
            file_path (str): Path to the text file containing the business idea
            
        Returns:
            str: Content of the business idea file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            if not content:
                raise ValueError("The business idea file is empty.")
                
            print(self._colored_print(f"✅ Business idea loaded from: {file_path}", "green"))
            return content
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find file: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def create_evaluation_prompt(self, idea_text):
        """
        Create the evaluation prompt for the AI model.
        
        Args:
            idea_text (str): The business idea to evaluate
            
        Returns:
            str: Formatted prompt for evaluation
        """
        return f"""
You are an expert startup mentor and investor. Evaluate the following business idea using this comprehensive rubric.

EVALUATION CRITERIA (Score 1-10 for each):
- MarketNeed: How pressing is the problem this solves?
- MarketSize: How large is the target market?
- ProductFit: How well does the solution fit the problem?
- BusinessModel: How viable is the revenue model?
- TeamCredibility: How capable does the team appear?
- ExecutionComplexity: How feasible is implementation?
- OverallViability: Overall business potential
- CompetitiveAdvantage: How differentiated is this solution?
- Scalability: How easily can this business scale?
- CustomerAcquisitionPotential: How easy will it be to acquire customers?
- FinancialSustainability: How sustainable are the financials?
- InnovationLevel: How innovative is this approach?

VERDICT OPTIONS:
- GO: Strong potential, recommend proceeding
- WAIT: Needs refinement before proceeding
- NO-GO: Significant concerns, not recommended

OUTPUT FORMAT (JSON only):
{{
    "scores": {{
        "MarketNeed": <score>,
        "MarketSize": <score>,
        ... (all 12 criteria)
    }},
    "verdict": "<GO/WAIT/NO-GO>",
    "strengths": ["strength1", "strength2", ...],
    "risks": ["risk1", "risk2", ...],
    "suggestions": ["suggestion1", "suggestion2", ...]
}}

Business Idea to Evaluate:
{idea_text}
"""
    
    def evaluate_idea(self, idea_text):
        """
        Send the business idea to Gemini for evaluation.
        
        Args:
            idea_text (str): The business idea to evaluate
            
        Returns:
            dict: Parsed evaluation results
        """
        print(self._colored_print("🤖 Generating evaluation...", "yellow"))
        
        prompt = self.create_evaluation_prompt(idea_text)
        response = self.model.generate_content(prompt)
        raw_output = response.text.strip()
        
        # Clean markdown formatting if present
        if raw_output.startswith("```"):
            raw_output = raw_output.lstrip("```").replace("json", "").strip()
        if raw_output.endswith("```"):
            raw_output = raw_output.rstrip("```").strip()
        
        try:
            parsed_result = json.loads(raw_output)
            print(self._colored_print("✅ Evaluation completed successfully", "green"))
            return parsed_result
            
        except json.JSONDecodeError as e:
            print(self._colored_print("⚠️ JSON parsing failed. Raw output:", "red"))
            print(raw_output)
            raise Exception(f"Could not parse AI response as JSON: {str(e)}")
    
    def display_results(self, evaluation_results):
        """
        Display evaluation results in a formatted console output.
        
        Args:
            evaluation_results (dict): The parsed evaluation results
        """
        print(self._colored_print("\n" + "="*70, "green"))
        print(self._colored_print("🚀 STARTUP EVALUATION REPORT", "green", attrs=['bold']))
        print(self._colored_print("="*70 + "\n", "green"))
        
        # Display scores
        self._display_scores(evaluation_results.get("scores", {}))
        
        # Display verdict
        self._display_verdict(evaluation_results.get("verdict", "N/A"))
        
        # Display detailed sections
        sections = [
            ("strengths", "💪 STRENGTHS", "green"),
            ("risks", "⚠️  RISKS", "red"),
            ("suggestions", "💡 SUGGESTIONS", "blue")
        ]
        
        for key, title, color in sections:
            self._display_section(
                evaluation_results.get(key, []), 
                title, 
                color
            )
    
    def _display_scores(self, scores):
        """Display evaluation scores in a formatted table."""
        if not scores:
            print("No scores available")
            return
            
        print(self._colored_print("📊 EVALUATION SCORES:", "cyan", attrs=['bold']))
        print("-" * 70)
        
        # Sort scores by value (highest first)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for criterion, score in sorted_scores:
            # Color coding based on score
            if score >= 8:
                color = "green"
            elif score >= 6:
                color = "yellow"
            elif score >= 4:
                color = "yellow"
            else:
                color = "red"
            
            # Format criterion name for better readability
            formatted_criterion = criterion.replace("_", " ").title()
            
            print(f"  {formatted_criterion:<30}: {self._colored_print(f'{score}/10', color, attrs=['bold'])}")
        
        # Calculate and display average
        avg_score = round(sum(scores.values()) / len(scores), 1)
        print("-" * 70)
        print(f"  {'Average Score':<30}: {self._colored_print(f'{avg_score}/10', 'cyan', attrs=['bold'])}")
        print()
    
    def _display_verdict(self, verdict):
        """Display the final verdict with appropriate styling."""
        verdict_colors = {
            "GO": "green",
            "WAIT": "yellow", 
            "NO-GO": "red"
        }
        
        color = verdict_colors.get(verdict, "white")
        print(self._colored_print(f"🎯 FINAL VERDICT: {verdict}", color, attrs=['bold']))
        print("-" * 70)
        print()
    
    def _display_section(self, items, title, color):
        """Display a section (strengths, risks, or suggestions)."""
        print(self._colored_print(title, color, attrs=['bold']))
        print("-" * 70)
        
        if items:
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item}")
        else:
            print("  None identified")
        
        print()
    
    def save_to_file(self, evaluation_results, idea_text, output_dir="evaluations"):
        """
        Save evaluation results to a formatted text file.
        
        Args:
            evaluation_results (dict): The evaluation results
            idea_text (str): The original business idea text
            output_dir (str): Directory to save the output file
            
        Returns:
            str: Path to the saved file
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"startup_evaluation_{timestamp}.txt"
        filepath = Path(output_dir) / filename
        
        # Format content for file
        content = self._format_file_content(evaluation_results, idea_text)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(self._colored_print(f"💾 Results saved to: {filepath}", "green", attrs=['bold']))
        return str(filepath)
    
    def _format_file_content(self, results, idea_text):
        """Format the evaluation results for file output."""
        content = []
        
        # Header
        content.append("="*80)
        content.append("STARTUP BUSINESS IDEA EVALUATION REPORT")
        content.append("="*80)
        content.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Original idea
        content.append("BUSINESS IDEA:")
        content.append("-" * 40)
        content.append(idea_text[:500] + "..." if len(idea_text) > 500 else idea_text)
        content.append("")
        
        # Scores
        content.append("EVALUATION SCORES:")
        content.append("-" * 40)
        scores = results.get("scores", {})
        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for criterion, score in sorted_scores:
                formatted_criterion = criterion.replace("_", " ").title()
                content.append(f"{formatted_criterion:<30}: {score}/10")
            
            avg_score = round(sum(scores.values()) / len(scores), 1)
            content.append("-" * 40)
            content.append(f"{'Average Score':<30}: {avg_score}/10")
        content.append("")
        
        # Verdict
        verdict = results.get("verdict", "N/A")
        content.append(f"FINAL VERDICT: {verdict}")
        content.append("=" * 40)
        content.append("")
        
        # Detailed sections
        sections = [
            ("strengths", "STRENGTHS"),
            ("risks", "RISKS"), 
            ("suggestions", "SUGGESTIONS")
        ]
        
        for key, title in sections:
            content.append(f"{title}:")
            content.append("-" * 40)
            items = results.get(key, [])
            if items:
                for i, item in enumerate(items, 1):
                    content.append(f"{i}. {item}")
            else:
                content.append("None identified")
            content.append("")
        
        return "\n".join(content)


def main():
    """Main function to run the startup evaluation."""
    try:
        # Initialize evaluator
        evaluator = StartupEvaluator()
        
        # Configuration
        idea_file_path = r"C:\Users\RAHIL\Documents\GitHub\CSI_Hackathon\pdf_text\sample_english_1_extracted_20250927_212527.txt"
        
        # Load business idea
        print("🔄 Loading business idea...")
        idea_text = evaluator.load_business_idea(idea_file_path)
        
        # Evaluate the idea
        evaluation_results = evaluator.evaluate_idea(idea_text)
        
        # Display results
        evaluator.display_results(evaluation_results)
        
        # Save to file
        output_file = evaluator.save_to_file(evaluation_results, idea_text)
        
        print(evaluator._colored_print(f"\n🎉 Evaluation complete! Check {output_file} for full report.", "green", attrs=['bold']))
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
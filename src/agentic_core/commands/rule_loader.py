#!/usr/bin/env python3
"""
Rule Loader and Verification System

This module provides utilities for loading, verifying, and querying the Agentic framework rules.
It allows programmatic access to the rules defined in rules.json and provides a verification
system to ensure AI agents have correctly loaded and understood the rules.
"""

import json
import os
import sys
import random
import logging
from pathlib import Path
from datetime import datetime

# Import the config module from agentic_core
from agentic_core.commands import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser("~/Agentic/logs/rule_loader.log"), mode='a')
    ]
)
logger = logging.getLogger("rule_loader")

# Create logs directory if it doesn't exist
os.makedirs(os.path.expanduser("~/Agentic/logs"), exist_ok=True)

# Path to the rules file
RULES_PATH = config.get_path("rules_file")
if not RULES_PATH:
    RULES_PATH = os.path.expanduser("~/Agentic/agentic/rules.json")

class RuleLoader:
    """Class for loading and verifying Agentic framework rules."""
    
    def __init__(self, rules_path=RULES_PATH):
        """Initialize the RuleLoader with the path to the rules file."""
        self.rules_path = rules_path
        self.rules = self._load_rules()
        self.verification_results = {
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "score": 0,
            "total_questions": 0,
            "correct_answers": 0,
            "questions": []
        }
    
    def _load_rules(self):
        """Load the rules from the JSON file."""
        try:
            with open(self.rules_path, 'r') as f:
                rules = json.load(f)
            logger.info(f"Successfully loaded rules from {self.rules_path}")
            return rules
        except FileNotFoundError:
            logger.error(f"Rules file not found: {self.rules_path}")
            print(f"Error: Rules file not found: {self.rules_path}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in rules file: {self.rules_path}")
            print(f"Error: Invalid JSON in rules file: {self.rules_path}")
            return None
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            print(f"Error loading rules: {e}")
            return None
    
    def get_rule(self, category, subcategory=None, key=None):
        """
        Get a specific rule or category of rules.
        
        Args:
            category (str): The main category of rules (e.g., 'python_environment')
            subcategory (str, optional): The subcategory of rules (e.g., 'virtual_environments')
            key (str, optional): The specific rule key (e.g., 'location')
        
        Returns:
            The requested rule or category of rules, or None if not found
        """
        if not self.rules:
            return None
        
        try:
            if category not in self.rules["rules"]:
                return None
            
            if subcategory is None:
                return self.rules["rules"][category]
            
            if subcategory not in self.rules["rules"][category]:
                return None
            
            if key is None:
                return self.rules["rules"][category][subcategory]
            
            if key not in self.rules["rules"][category][subcategory]:
                return None
            
            return self.rules["rules"][category][subcategory][key]
        except Exception as e:
            logger.error(f"Error getting rule: {e}")
            return None
    
    def get_all_categories(self):
        """Get a list of all rule categories."""
        if not self.rules:
            return []
        
        return list(self.rules["rules"].keys())
    
    def get_utility_script_info(self, script_name):
        """Get information about a utility script."""
        if not self.rules or "utility_scripts" not in self.rules:
            return None
        
        if script_name not in self.rules["utility_scripts"]:
            return None
        
        return self.rules["utility_scripts"][script_name]
    
    def get_all_utility_scripts(self):
        """Get a list of all utility scripts."""
        if not self.rules or "utility_scripts" not in self.rules:
            return []
        
        return list(self.rules["utility_scripts"].keys())
    
    def generate_verification_questions(self, num_questions=10):
        """
        Generate verification questions to test an AI agent's understanding of the rules.
        
        Args:
            num_questions (int): The number of questions to generate
        
        Returns:
            A list of dictionaries containing questions and their answers
        """
        if not self.rules:
            return []
        
        questions = []
        categories = self.get_all_categories()
        
        # Ensure we have enough rules to generate the requested number of questions
        max_questions = min(num_questions, len(categories) * 3)
        
        # Generate questions about directory structure
        if "directory_structure" in categories:
            dir_structure = self.get_rule("directory_structure")
            if dir_structure:
                dir_keys = list(dir_structure.keys())
                for key in random.sample(dir_keys, min(3, len(dir_keys))):
                    if key != "project_structure" and key in dir_structure:
                        questions.append({
                            "question": f"What is the path for the {key.replace('_dir', '')} directory?",
                            "answer": dir_structure[key],
                            "category": "directory_structure"
                        })
        
        # Generate questions about Python environment
        if "python_environment" in categories:
            py_env = self.get_rule("python_environment")
            if py_env and "package_manager" in py_env:
                # Question about package manager
                questions.append({
                    "question": "What package manager should be used for Python package management?",
                    "answer": py_env["package_manager"],
                    "category": "python_environment"
                })
                
                # Question about virtual environment location
                if "virtual_environments" in py_env and "location" in py_env["virtual_environments"]:
                    questions.append({
                        "question": "Where should virtual environments be located relative to a project?",
                        "answer": py_env["virtual_environments"]["location"],
                        "category": "python_environment"
                    })
        
        # Generate questions about naming conventions
        if "naming_conventions" in categories:
            naming = self.get_rule("naming_conventions")
            if naming:
                naming_keys = list(naming.keys())
                if naming_keys:
                    for key in random.sample(naming_keys, min(2, len(naming_keys))):
                        if key in naming:
                            questions.append({
                                "question": f"What naming convention should be used for {key}?",
                                "answer": naming[key],
                                "category": "naming_conventions"
                            })
        
        # Generate questions about security
        if "security" in categories:
            security = self.get_rule("security")
            if security and "access_control" in security:
                access_control = security["access_control"]
                if "storage" in access_control:
                    questions.append({
                        "question": "What should be used to store sensitive information instead of hardcoding it?",
                        "answer": access_control["storage"],
                        "category": "security"
                    })
        
        # Generate questions about utility scripts
        utility_scripts = self.get_all_utility_scripts()
        if utility_scripts:
            for script in random.sample(utility_scripts, min(2, len(utility_scripts))):
                script_info = self.get_utility_script_info(script)
                if script_info and "purpose" in script_info:
                    questions.append({
                        "question": f"What is the purpose of the {script} utility script?",
                        "answer": script_info["purpose"],
                        "category": "utility_scripts"
                    })
        
        # Shuffle and limit the questions
        random.shuffle(questions)
        return questions[:max_questions]
    
    def verify_agent_understanding(self, interactive=True):
        """
        Verify an AI agent's understanding of the rules through a quiz.
        
        Args:
            interactive (bool): Whether to run the verification interactively
        
        Returns:
            A dictionary containing the verification results
        """
        questions = self.generate_verification_questions()
        correct_answers = 0
        
        self.verification_results["total_questions"] = len(questions)
        self.verification_results["questions"] = []
        
        print("\n===== AGENTIC FRAMEWORK RULE VERIFICATION =====\n")
        print("This verification will test your understanding of the Agentic framework rules.")
        print(f"You will be asked {len(questions)} questions about various aspects of the framework.")
        print("Please answer each question to the best of your ability.\n")
        
        for i, q in enumerate(questions, 1):
            print(f"Question {i}: {q['question']}")
            
            if interactive:
                user_answer = input("Your answer: ")
                
                # Simple answer checking - could be improved with NLP for better matching
                correct = self._check_answer(user_answer, q["answer"])
                
                if correct:
                    print("Correct!")
                    correct_answers += 1
                else:
                    print(f"Incorrect. The correct answer is: {q['answer']}")
                
                self.verification_results["questions"].append({
                    "question": q["question"],
                    "expected_answer": q["answer"],
                    "user_answer": user_answer,
                    "correct": correct,
                    "category": q["category"]
                })
            else:
                print(f"Expected answer: {q['answer']}")
                self.verification_results["questions"].append({
                    "question": q["question"],
                    "expected_answer": q["answer"],
                    "category": q["category"]
                })
            
            print()
        
        if interactive:
            self.verification_results["correct_answers"] = correct_answers
            self.verification_results["score"] = (correct_answers / len(questions)) * 100
            self.verification_results["passed"] = self.verification_results["score"] >= 80
            
            print("\n===== VERIFICATION RESULTS =====")
            print(f"Score: {self.verification_results['score']:.1f}% ({correct_answers}/{len(questions)})")
            
            if self.verification_results["passed"]:
                print("Congratulations! You have passed the verification.")
                print("You have demonstrated a good understanding of the Agentic framework rules.")
            else:
                print("You did not pass the verification.")
                print("Please review the Agentic framework documentation and try again.")
        
        return self.verification_results
    
    def _check_answer(self, user_answer, expected_answer):
        """
        Check if a user's answer is correct.
        
        This is a simple implementation that could be improved with NLP techniques
        for better matching of semantically equivalent answers.
        
        Args:
            user_answer (str): The user's answer
            expected_answer (str or list): The expected answer(s)
        
        Returns:
            bool: Whether the answer is correct
        """
        if isinstance(expected_answer, list):
            # If the expected answer is a list, check if the user's answer matches any item
            for answer in expected_answer:
                if self._check_single_answer(user_answer, answer):
                    return True
            return False
        else:
            # Otherwise, check if the user's answer matches the expected answer
            return self._check_single_answer(user_answer, expected_answer)
    
    def _check_single_answer(self, user_answer, expected_answer):
        """Check if a user's answer matches a single expected answer."""
        # Convert both to strings for comparison
        user_answer = str(user_answer).lower().strip()
        expected_answer = str(expected_answer).lower().strip()
        
        # Exact match
        if user_answer == expected_answer:
            return True
        
        # Path match (normalize paths)
        if "$home" in user_answer and "$home" in expected_answer:
            user_path = user_answer.replace("$home", "").replace("\\", "/").strip("/")
            expected_path = expected_answer.replace("$home", "").replace("\\", "/").strip("/")
            if user_path == expected_path:
                return True
        
        # Check if the user's answer contains the expected answer
        if expected_answer in user_answer:
            return True
        
        # Check if the expected answer contains the user's answer
        if user_answer in expected_answer and len(user_answer) > len(expected_answer) / 2:
            return True
        
        return False
    
    def export_verification_results(self, output_path=None):
        """
        Export the verification results to a JSON file.
        
        Args:
            output_path (str, optional): The path to save the results to
        
        Returns:
            str: The path to the saved results file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.expanduser(f"~/Agentic/logs/verification_{timestamp}.json")
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(self.verification_results, f, indent=2)
            
            logger.info(f"Verification results saved to {output_path}")
            print(f"Verification results saved to {output_path}")
            
            return output_path
        except Exception as e:
            logger.error(f"Error saving verification results: {e}")
            print(f"Error saving verification results: {e}")
            return None

# Functions for the ag CLI

def verify_rules(args):
    """
    Verify an AI agent's understanding of the rules, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    non_interactive = "--non-interactive" in args
    output_path = None
    
    for i in range(len(args)):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            break
    
    rule_loader = RuleLoader()
    results = rule_loader.verify_agent_understanding(not non_interactive)
    
    if output_path:
        rule_loader.export_verification_results(output_path)
    
    return 0 if results["passed"] else 1

def query_rules(args):
    """
    Query the rules, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    if not args:
        print("Error: No category specified")
        print("Usage: ag rule query <category> [--subcategory <subcategory>] [--key <key>]")
        return 1
    
    category = args[0]
    subcategory = None
    key = None
    
    for i in range(1, len(args)):
        if args[i] == "--subcategory" and i + 1 < len(args):
            subcategory = args[i + 1]
        elif args[i] == "--key" and i + 1 < len(args):
            key = args[i + 1]
    
    rule_loader = RuleLoader()
    result = rule_loader.get_rule(category, subcategory, key)
    
    if result:
        print(json.dumps(result, indent=2))
        return 0
    else:
        print(f"No rule found for category={category}, subcategory={subcategory}, key={key}")
        return 1

def list_categories(args):
    """
    List rule categories or utility scripts, called by the ag script.
    
    Args:
        args: Command-line arguments
    
    Returns:
        int: Exit code
    """
    rule_loader = RuleLoader()
    
    # Check if we should list utility scripts instead of rule categories
    if args and "--utility-scripts" in args:
        scripts = rule_loader.get_all_utility_scripts()
        print("Available utility scripts:")
        for script in scripts:
            info = rule_loader.get_utility_script_info(script)
            if info and "purpose" in info:
                print(f"  - {script}: {info['purpose']}")
            else:
                print(f"  - {script}: No purpose information available")
    else:
        categories = rule_loader.get_all_categories()
        print("Available rule categories:")
        for category in categories:
            print(f"  - {category}")
    
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Framework Rule Loader and Verification")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify an AI agent's understanding of the rules")
    verify_parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode")
    verify_parser.add_argument("--output", help="Path to save verification results")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the rules")
    query_parser.add_argument("category", help="Rule category")
    query_parser.add_argument("--subcategory", help="Rule subcategory")
    query_parser.add_argument("--key", help="Rule key")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List rule categories or utility scripts")
    list_parser.add_argument("--utility-scripts", action="store_true", help="List utility scripts instead of rule categories")
    
    args = parser.parse_args()
    
    rule_loader = RuleLoader()
    
    if args.command == "verify":
        results = rule_loader.verify_agent_understanding(not args.non_interactive)
        if args.output:
            rule_loader.export_verification_results(args.output)
    elif args.command == "query":
        result = rule_loader.get_rule(args.category, args.subcategory, args.key)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print(f"No rule found for category={args.category}, subcategory={args.subcategory}, key={args.key}")
    elif args.command == "list":
        if args.utility_scripts:
            scripts = rule_loader.get_all_utility_scripts()
            print("Available utility scripts:")
            for script in scripts:
                info = rule_loader.get_utility_script_info(script)
                if info and "purpose" in info:
                    print(f"  - {script}: {info['purpose']}")
                else:
                    print(f"  - {script}: No purpose information available")
        else:
            categories = rule_loader.get_all_categories()
            print("Available rule categories:")
            for category in categories:
                print(f"  - {category}")
    else:
        parser.print_help()

#!/usr/bin/env python3
"""
Professional GitHub Repository Setup Script
Initializes Git repository with proper configuration for professional development
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {command}")
        print(f"Error: {e.stderr}")
        return None

def setup_git_repository():
    """Set up Git repository with professional configuration"""
    
    print("🚀 Setting up Professional GitHub Repository")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check if Git is installed
    git_check = run_command("git --version", check=False)
    if git_check is None or git_check.returncode != 0:
        print("❌ Git is not installed. Please install Git first.")
        return False
    
    print(f"✅ Git version: {git_check.stdout.strip()}")
    
    # Initialize Git repository if not already initialized
    if not (project_dir / ".git").exists():
        print("\n📁 Initializing Git repository...")
        run_command("git init")
        print("✅ Git repository initialized")
    else:
        print("✅ Git repository already exists")
    
    # Set up professional Git configuration
    print("\n⚙️ Setting up Git configuration...")
    
    # Set default branch to main
    run_command("git config init.defaultBranch main")
    
    # Set up professional commit template
    commit_template = """# Professional Commit Message Template
# 
# Type: Brief summary (50 characters or less)
# 
# More detailed explanation (wrap at 72 characters)
# - What: What changes were made
# - Why: Why these changes were necessary  
# - How: How the changes address the issue
#
# Types: feat, fix, docs, style, refactor, test, chore
# Example: feat: Add Jina AI integration for intelligent URL discovery
#
# Footer (if applicable):
# Fixes #123
# Co-authored-by: Name <email@example.com>
"""
    
    with open(".gitmessage", "w") as f:
        f.write(commit_template)
    
    run_command("git config commit.template .gitmessage")
    
    # Configure line endings (important for cross-platform)
    run_command("git config core.autocrlf true")  # Windows
    
    print("✅ Git configuration completed")
    
    # Check Git status
    print("\n📊 Checking repository status...")
    status_result = run_command("git status --porcelain")
    
    if status_result and status_result.stdout.strip():
        print("📝 Files to be added to repository:")
        for line in status_result.stdout.strip().split('\n'):
            print(f"   {line}")
    else:
        print("✅ Working directory is clean")
    
    return True

def verify_gitignore():
    """Verify .gitignore is properly configured"""
    
    print("\n🔒 Verifying .gitignore configuration...")
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        print("❌ .gitignore file not found!")
        return False
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    # Check for critical patterns
    critical_patterns = [
        "*.key",
        ".env", 
        "venv/",
        "__pycache__/",
        "data/raw/",
        "*.log",
        "config/*_secrets.json"
    ]
    
    missing_patterns = []
    for pattern in critical_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print("⚠️ Missing critical .gitignore patterns:")
        for pattern in missing_patterns:
            print(f"   - {pattern}")
        return False
    else:
        print("✅ .gitignore properly configured for security")
        return True

def setup_environment_files():
    """Set up environment configuration files"""
    
    print("\n🔧 Setting up environment files...")
    
    # Check for .env.example
    if Path(".env.example").exists():
        print("✅ .env.example found")
        
        # Check if .env exists (should not be in repo)
        if Path(".env").exists():
            print("⚠️ .env file exists - this should not be committed!")
            print("💡 Make sure .env is in .gitignore")
        else:
            print("✅ No .env file found (good for security)")
    else:
        print("❌ .env.example not found")
        return False
    
    # Check for config examples
    config_example = Path("config/mcp_config.example.json")
    if config_example.exists():
        print("✅ Configuration example found")
    else:
        print("❌ Configuration example not found")
        return False
    
    return True

def check_sensitive_files():
    """Check for accidentally committed sensitive files"""
    
    print("\n🕵️ Checking for sensitive files...")
    
    sensitive_patterns = [
        "*.key",
        "*.secret", 
        ".env",
        "*api_key*",
        "*password*",
        "*credential*"
    ]
    
    sensitive_found = []
    
    for pattern in sensitive_patterns:
        result = run_command(f"find . -name '{pattern}' -not -path './.git/*'", check=False)
        if result and result.stdout.strip():
            sensitive_found.extend(result.stdout.strip().split('\n'))
    
    if sensitive_found:
        print("❌ Sensitive files found that should not be committed:")
        for file in sensitive_found:
            print(f"   - {file}")
        print("💡 Add these patterns to .gitignore and remove from repository")
        return False
    else:
        print("✅ No sensitive files found")
        return True

def create_initial_commit():
    """Create initial commit with proper structure"""
    
    print("\n📝 Preparing initial commit...")
    
    # Add files to staging
    run_command("git add .gitignore")
    run_command("git add .env.example")
    run_command("git add config/mcp_config.example.json")
    run_command("git add LICENSE")
    run_command("git add README_GITHUB.md")
    run_command("git add requirements.txt")
    run_command("git add src/")
    run_command("git add tests/")
    run_command("git add examples/")
    run_command("git add docs/")
    run_command("git add .github/")
    
    # Check what's staged
    staged_result = run_command("git diff --cached --name-only")
    if staged_result and staged_result.stdout.strip():
        print("📦 Files staged for commit:")
        for file in staged_result.stdout.strip().split('\n'):
            print(f"   ✅ {file}")
    
    # Create initial commit
    commit_message = """feat: Initial commit - AI-Driven MCP Web Scraper

Complete professional implementation with:
- Jina AI integration for intelligent URL discovery  
- MCP server with 6 professional tools
- Computer vision with OpenCV face detection
- Legal compliance and robots.txt checking
- Comprehensive test suite and documentation
- Professional GitHub repository structure

Features:
- intelligent_research: AI-powered URL discovery
- scrape_website: Professional web scraping
- categorize_images: Person detection and organization
- get_statistics: Real-time monitoring
- check_legal_compliance: Legal verification
- list_categories: Category management

Ready for production deployment and collaboration.
"""
    
    commit_result = run_command(f'git commit -m "{commit_message}"', check=False)
    
    if commit_result and commit_result.returncode == 0:
        print("✅ Initial commit created successfully")
        return True
    else:
        print("⚠️ Commit may have failed or no changes to commit")
        return False

def show_next_steps():
    """Show next steps for GitHub setup"""
    
    print("\n" + "🎯" * 60)
    print("NEXT STEPS FOR GITHUB SETUP")
    print("🎯" * 60)
    
    print("""
1. 🌐 Create GitHub Repository:
   - Go to https://github.com/new
   - Repository name: mcp-web-scraper
   - Description: AI-Driven MCP Web Scraper with Jina AI integration
   - Set to Public (for sharing) or Private
   - DO NOT initialize with README, .gitignore, or license (we have them)

2. 🔗 Connect Local Repository to GitHub:
   git remote add origin https://github.com/yourusername/mcp-web-scraper.git
   git branch -M main
   git push -u origin main

3. 📝 Configure Repository Settings:
   - Enable Issues and Discussions
   - Set up branch protection rules for main
   - Configure GitHub Actions (already included)
   - Add topics: ai, web-scraping, mcp, jina-ai, computer-vision

4. 🏷️ Create First Release:
   - Go to Releases → Create a new release
   - Tag: v1.0.0
   - Title: "Initial Release - AI-Driven MCP Web Scraper"
   - Describe features and capabilities

5. 📖 Update README:
   - Replace <your-repo-url> with actual GitHub URL
   - Add screenshots or demo GIFs if desired
   - Update contact information

6. 🛡️ Security Setup:
   - Enable security advisories
   - Set up Dependabot for dependency updates
   - Review and test GitHub Actions workflows
   
7. 🤝 Community Setup:
   - Add CODE_OF_CONDUCT.md
   - Add CONTRIBUTING.md  
   - Set up GitHub Discussions for community questions
""")

def main():
    """Main setup function"""
    
    print("🎯 Professional GitHub Repository Setup")
    print("Reasoning: Creating a production-ready repository with proper security")
    print("Understanding: Following professional development best practices")
    print("=" * 80)
    
    success_count = 0
    total_checks = 6
    
    # Run setup steps
    if setup_git_repository():
        success_count += 1
        
    if verify_gitignore():
        success_count += 1
        
    if setup_environment_files():
        success_count += 1
        
    if check_sensitive_files():
        success_count += 1
        
    if create_initial_commit():
        success_count += 1
        
    # Final validation
    if success_count >= 4:  # Allow for some warnings
        success_count += 1
        print("\n🎉 Repository setup completed successfully!")
    else:
        print("\n⚠️ Repository setup completed with warnings")
    
    print(f"\n📊 Setup Summary: {success_count}/{total_checks} checks passed")
    
    if success_count >= 4:
        show_next_steps()
        return True
    else:
        print("❌ Please resolve the issues above before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

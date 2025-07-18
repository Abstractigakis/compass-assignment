#!/usr/bin/env python3
"""
Setup script for Costco Web Scraper with AI capabilities.
Helps users configure environment variables and install dependencies.
"""

import os
import sys
from pathlib import Path


def setup_environment():
    """Set up the environment for the Costco Web Scraper."""

    print("🏪 Costco Web Scraper Setup")
    print("=" * 40)

    # Check if .env file exists
    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        if env_example.exists():
            print("📄 Creating .env file from template...")
            import shutil

            shutil.copy(env_example, env_file)
            print(f"✅ Created .env file")
        else:
            print("⚠️ No .env.example template found")
            # Create basic .env file
            with open(env_file, "w") as f:
                f.write("# Costco Web Scraper Environment Variables\n")
                f.write("GEMINI_API_KEY=your_gemini_api_key_here\n")
            print("✅ Created basic .env file")
    else:
        print("✅ .env file already exists")

    # Check API key
    try:
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key or api_key == "your_gemini_api_key_here":
            print("\n🔑 API Key Setup Required")
            print("1. Get your free Gemini API key at:")
            print("   https://aistudio.google.com/app/apikey")
            print(
                "2. Open .env file and replace 'your_gemini_api_key_here' with your actual key"
            )
            print("3. Save the file and run this setup again")
            return False
        else:
            print("✅ Gemini API key configured")
            return True

    except ImportError:
        print("⚠️ python-dotenv not installed yet")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""

    print("\n📦 Checking Dependencies")
    print("-" * 25)

    required_packages = [
        ("requests", "requests"),
        ("beautifulsoup4", "bs4"),
        ("playwright", "playwright"),
        ("python-dotenv", "dotenv"),
        ("google-generativeai", "google.generativeai"),
    ]

    missing_packages = []

    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} (missing)")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n📋 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        print("or")
        print("pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed")
        return True


def test_ai_functionality():
    """Test if AI functionality is working."""

    print("\n🤖 Testing AI Functionality")
    print("-" * 25)

    try:
        from costco_web_scraper import create_costco_scraper

        scraper = create_costco_scraper()

        if scraper.ai_enabled:
            print("✅ AI-powered extraction enabled")
            print(f"🧠 Using model: {scraper.gemini_model.model_name}")
            return True
        else:
            print("❌ AI features disabled")
            print("Check your GEMINI_API_KEY in .env file")
            return False

    except Exception as e:
        print(f"❌ Error testing AI: {e}")
        return False


def main():
    """Main setup function."""

    print("🚀 Setting up your AI-powered web scraper...\n")

    # Step 1: Dependencies
    deps_ok = check_dependencies()

    # Step 2: Environment
    env_ok = setup_environment()

    # Step 3: AI Test (only if deps and env are OK)
    ai_ok = False
    if deps_ok and env_ok:
        ai_ok = test_ai_functionality()

    # Summary
    print("\n🏁 Setup Summary")
    print("=" * 20)
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"Environment:  {'✅' if env_ok else '❌'}")
    print(f"AI Features:  {'✅' if ai_ok else '❌'}")

    if deps_ok and env_ok and ai_ok:
        print("\n🎉 Setup Complete!")
        print("🚀 Ready to run AI-powered scraping!")
        print("\nNext steps:")
        print("• python demo_ai_scraper.py")
        print("• python test_ai_extraction.py")
    else:
        print("\n⚠️ Setup needs attention")
        print("Please address the issues above and run setup again")


if __name__ == "__main__":
    main()

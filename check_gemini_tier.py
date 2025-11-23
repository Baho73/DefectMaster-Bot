"""
Script to check Gemini API tier and rate limits
Reads from .env and makes test requests to determine current tier
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")
GEMINI_ANALYSIS_MODEL = os.getenv("GEMINI_ANALYSIS_MODEL", "gemini-2.5-pro")

# Known tier limits for reference
TIER_LIMITS = {
    "gemini-2.5-flash": {
        "Free": {"RPM": 10, "TPM": 250000, "RPD": 250},
        "Tier 1": {"RPM": 1000, "TPM": 1000000, "RPD": 10000},
        "Tier 2": {"RPM": 2000, "TPM": 3000000, "RPD": 100000},
        "Tier 3": {"RPM": 10000, "TPM": 8000000, "RPD": "Unlimited"}
    },
    "gemini-2.5-pro": {
        "Free": {"RPM": 2, "TPM": 125000, "RPD": 50},
        "Tier 1": {"RPM": 150, "TPM": 2000000, "RPD": 10000},
        "Tier 2": {"RPM": 1000, "TPM": 5000000, "RPD": 50000},
        "Tier 3": {"RPM": 2000, "TPM": 8000000, "RPD": "Unlimited"}
    }
}


def detect_tier_from_rpm(model_name: str, rpm: int) -> str:
    """Detect tier based on RPM limit"""
    limits = TIER_LIMITS.get(model_name, {})

    for tier_name, tier_limits in limits.items():
        if tier_limits["RPM"] == rpm:
            return tier_name

    return "Unknown"


def check_model(model_name: str):
    """Check tier for a specific model"""
    print(f"\n{'='*60}")
    print(f"Checking: {model_name}")
    print(f"{'='*60}")

    try:
        # Configure API
        genai.configure(api_key=GOOGLE_API_KEY)

        # Create model
        model = genai.GenerativeModel(model_name)

        # Make a simple test request
        print("Making test request...")
        response = model.generate_content("Say hello in one word")

        # Try to access response metadata
        print(f"\n[OK] Request successful!")
        print(f"Response: {response.text}")

        # Try to get usage metadata
        if hasattr(response, 'usage_metadata'):
            print(f"\nUsage metadata:")
            print(f"  Prompt tokens: {response.usage_metadata.prompt_token_count}")
            print(f"  Response tokens: {response.usage_metadata.candidates_token_count}")
            print(f"  Total tokens: {response.usage_metadata.total_token_count}")

        # Note: Response headers are not directly accessible through Python SDK
        # We need to infer tier from behavior or use REST API
        print(f"\n[!] Note: Python SDK doesn't expose rate limit headers directly.")
        print(f"To determine exact tier, try the REST API method below.")

        # Show expected limits for this model
        print(f"\nExpected limits for {model_name}:")
        limits = TIER_LIMITS.get(model_name, {})
        for tier_name, tier_limits in limits.items():
            print(f"\n  {tier_name}:")
            print(f"    RPM: {tier_limits['RPM']}")
            print(f"    TPM: {tier_limits['TPM']:,}")
            print(f"    RPD: {tier_limits['RPD']}")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")

        # Check for quota errors
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("\n[!] Rate limit exceeded! This might indicate:")
            print("  - You're on Free tier (very low limits)")
            print("  - You've exceeded your quota for today")
        elif "403" in str(e) or "API_KEY_INVALID" in str(e):
            print("\n[!] API key issue:")
            print("  - Check if GOOGLE_API_KEY is set correctly in .env")
            print("  - Verify the key is enabled for Gemini API")

        return False


def check_tier_via_rest():
    """Instructions for checking tier via REST API (more reliable)"""
    print(f"\n{'='*60}")
    print("How to check tier via REST API (most accurate)")
    print(f"{'='*60}")

    api_key = GOOGLE_API_KEY

    curl_command = f"""
curl -X POST \\
  'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}' \\
  -H 'Content-Type: application/json' \\
  -d '{{"contents":[{{"parts":[{{"text":"hi"}}]}}]}}' \\
  -v 2>&1 | grep -i "x-goog-quota-user\\|x-ratelimit"
"""

    print("\nRun this command to see rate limit headers:")
    print(curl_command)
    print("\nLook for headers like:")
    print("  x-goog-quota-user: <project-id>")
    print("  x-ratelimit-limit: <your RPM limit>")
    print("\nIf x-ratelimit-limit shows:")
    print("  - 2 -> Free tier (Gemini Pro)")
    print("  - 150 -> Paid Tier 1 (Gemini Pro)")
    print("  - 1000+ -> Paid Tier 2+ (Gemini Pro)")


def main():
    print("="*60)
    print("Gemini API Tier Checker")
    print("="*60)

    # Check if API key is set
    if not GOOGLE_API_KEY:
        print("\n[ERROR] GOOGLE_API_KEY not found in .env")
        print("Please ensure .env file exists and contains GOOGLE_API_KEY")
        return

    print(f"\n[OK] API Key found: {GOOGLE_API_KEY[:20]}...")
    print(f"\nModels to check:")
    print(f"  - Fast Model: {GEMINI_FAST_MODEL}")
    print(f"  - Analysis Model: {GEMINI_ANALYSIS_MODEL}")

    # Check both models
    check_model(GEMINI_FAST_MODEL)
    check_model(GEMINI_ANALYSIS_MODEL)

    # Show REST API method
    check_tier_via_rest()

    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print("\nBased on the test requests above:")
    print("  - If requests succeed without 429 errors -> API key is valid")
    print("  - To determine exact tier, use the curl command above")
    print("  - Or check Google AI Studio: https://aistudio.google.com/")
    print("\nFree tier indicators:")
    print("  [!] Frequent 429 errors when sending multiple requests")
    print("  [!] Very slow processing (quota limits)")
    print("\nPaid tier indicators:")
    print("  [+] High throughput without 429 errors")
    print("  [+] Fast processing")
    print("  [+] Higher daily quotas")

    print("\nTo upgrade to Paid tier:")
    print("  1. Go to https://console.cloud.google.com/billing")
    print("  2. Enable billing for your project")
    print("  3. Tier 1 activates automatically (pay-as-you-go)")
    print("")


if __name__ == "__main__":
    main()

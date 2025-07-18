#!/usr/bin/env python3
"""
Test script to verify the improved ETL generation
"""

import json
import requests
import time

# Test HTML content - simple but realistic
html_content = """
<html>
<head><title>Product Page</title></head>
<body>
    <div class="container">
        <h1>Amazing Widget</h1>
        <div class="price">$29.99</div>
        <div class="description">
            <p>This is an amazing widget that does many things.</p>
            <p>It comes with a 30-day money-back guarantee.</p>
        </div>
        <div class="stock-status">In Stock</div>
        <div class="features">
            <ul>
                <li>Feature 1: Durable construction</li>
                <li>Feature 2: Easy to use</li>
                <li>Feature 3: Eco-friendly</li>
            </ul>
        </div>
        <div class="specs">
            <table>
                <tr><td>Weight</td><td>2.5 lbs</td></tr>
                <tr><td>Dimensions</td><td>10x8x6 inches</td></tr>
                <tr><td>Color</td><td>Blue</td></tr>
            </table>
        </div>
    </div>
</body>
</html>
"""

print("🔄 Testing improved ETL generation")
print(f"HTML content length: {len(html_content)} chars")
print()

# Wait for server to be ready
print("⏳ Waiting for server to be ready...")
time.sleep(3)

# Step 1: Learn ETL
print("1️⃣ Calling learn-etl endpoint...")
learn_payload = {
    "html": html_content,
    "html_compressed": False,
    "goal": "Extract complete product information including name, price, description, stock status, features, and specifications",
}

try:
    learn_response = requests.post(
        "http://localhost:8000/pages/learn-etl", json=learn_payload
    )

    if learn_response.status_code == 200:
        learn_result = learn_response.json()
        print("✅ Learn ETL successful!")
        print(f"Status: {learn_result['status']}")
        print()
        print("📋 Generated Schema:")
        print(json.dumps(learn_result["entities_schema"], indent=2))
        print()
        print("🔧 Generated Function Code:")
        print("=" * 80)
        print(learn_result["etl_function_code"])
        print("=" * 80)

        # Step 2: Execute ETL
        print("\n2️⃣ Calling execute-etl endpoint...")
        execute_payload = {
            "etl_function_code": learn_result["etl_function_code"],
            "html": html_content,
            "html_compressed": False,
        }

        execute_response = requests.post(
            "http://localhost:8000/pages/execute-etl", json=execute_payload
        )

        if execute_response.status_code == 200:
            execute_result = execute_response.json()
            print("✅ Execute ETL successful!")
            print(f"Status: {execute_result['status']}")
            print()
            print("📋 Extracted Data:")
            print(json.dumps(execute_result["extracted_data"], indent=2))

            # Analyze the results
            extracted_data = execute_result["extracted_data"]
            print("\n🔍 Analysis:")
            print(f"- Data structure: {type(extracted_data)}")
            print(
                f"- Keys found: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict'}"
            )

            # Check if we extracted meaningful data
            if isinstance(extracted_data, dict) and extracted_data:
                print("- ✅ ETL function returned structured data")

                # Check for common fields
                found_fields = []
                for key, value in extracted_data.items():
                    if isinstance(value, dict):
                        found_fields.extend(value.keys())
                    elif isinstance(value, list) and value:
                        if isinstance(value[0], dict):
                            found_fields.extend(value[0].keys())

                print(f"- Found fields: {found_fields}")
            else:
                print("- ❌ No meaningful data extracted")
        else:
            print(f"❌ Execute ETL Error: {execute_response.status_code}")
            try:
                error_data = execute_response.json()
                print("Error details:", json.dumps(error_data, indent=2))
            except:
                print("Response text:", execute_response.text)

    else:
        print(f"❌ Learn ETL Error: {learn_response.status_code}")
        try:
            error_data = learn_response.json()
            print("Error details:", json.dumps(error_data, indent=2))
        except:
            print("Response text:", learn_response.text)

except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback

    traceback.print_exc()

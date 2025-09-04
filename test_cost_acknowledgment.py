#!/usr/bin/env python3
"""
Test that verifies the cost acknowledgment section was added correctly
"""
import requests

def test_cost_acknowledgment_in_form():
    # Read the RequestForm.js file to verify the content was added
    try:
        with open('/app/frontend/src/components/RequestForm.js', 'r') as f:
            content = f.read()
        
        # Check for the cost acknowledgment section
        checks = [
            "COST ACKNOWLEDGMENT" in content,
            "deposit of $75" in content,
            "total cost will not exceed $750" in content,
            "Video Records Notice" in content,
            "BWC, dash‑cam, fixed" in content,
            "ORC §149.43 and HB 315" in content,
            "body_cam_footage" in content
        ]
        
        print("🔍 Checking cost acknowledgment section in RequestForm.js:")
        print(f"✅ COST ACKNOWLEDGMENT header: {'✓' if checks[0] else '✗'}")
        print(f"✅ $75 deposit mention: {'✓' if checks[1] else '✗'}")
        print(f"✅ $750 max cost: {'✓' if checks[2] else '✗'}")
        print(f"✅ Video Records Notice: {'✓' if checks[3] else '✗'}")
        print(f"✅ BWC/dash-cam reference: {'✓' if checks[4] else '✗'}")
        print(f"✅ Legal statutes: {'✓' if checks[5] else '✗'}")
        print(f"✅ Body cam trigger: {'✓' if checks[6] else '✗'}")
        
        all_checks_passed = all(checks)
        
        if all_checks_passed:
            print("\n🎉 SUCCESS: All cost acknowledgment components are present!")
            print("\n📄 The section will display when users select 'Body Camera Footage'")
            print("   and includes both the cost information and legal notice.")
        else:
            print("\n❌ ISSUE: Some components are missing")
            
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return False

def show_actual_content():
    """Show the actual content that was added"""
    try:
        with open('/app/frontend/src/components/RequestForm.js', 'r') as f:
            lines = f.readlines()
        
        # Find and show the cost acknowledgment section
        in_cost_section = False
        cost_section_lines = []
        
        for i, line in enumerate(lines):
            if "COST ACKNOWLEDGMENT" in line:
                in_cost_section = True
                # Show context around the section (10 lines before and after)
                start = max(0, i - 3)
                end = min(len(lines), i + 15)
                cost_section_lines = lines[start:end]
                break
        
        if cost_section_lines:
            print("\n📝 ACTUAL CONTENT ADDED:")
            print("=" * 60)
            for line in cost_section_lines:
                print(line.rstrip())
            print("=" * 60)
        else:
            print("\n❌ Could not find cost acknowledgment section")
            
    except Exception as e:
        print(f"❌ Error showing content: {str(e)}")

if __name__ == "__main__":
    success = test_cost_acknowledgment_in_form()
    show_actual_content()
    
    if success:
        print("\n🚀 READY TO TEST: Login to the app and select 'Body Camera Footage'")
        print("   in the request form to see the cost acknowledgment section!")
    else:
        print("\n🔧 NEEDS FIX: Cost acknowledgment section needs to be added correctly")
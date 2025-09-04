#!/usr/bin/env python3
"""
Verify all the requested changes have been implemented
"""

def verify_changes():
    print("🔍 VERIFYING ALL REQUESTED CHANGES")
    print("=" * 50)
    
    # Check RequestForm.js for all changes
    try:
        with open('/app/frontend/src/components/RequestForm.js', 'r') as f:
            request_form_content = f.read()
        
        # Check 1: Contact Information Changes
        contact_checks = [
            "records@Shakerpd.com" in request_form_content,
            "(216) 1220" in request_form_content,
            "5-10 business days" in request_form_content,
            "Contact Information" in request_form_content
        ]
        
        print("📞 1. CONTACT INFORMATION CHANGES:")
        print(f"   ✅ Email updated to records@Shakerpd.com: {'✓' if contact_checks[0] else '✗'}")
        print(f"   ✅ Phone updated to (216) 1220: {'✓' if contact_checks[1] else '✗'}")
        print(f"   ✅ Processing time mentioned: {'✓' if contact_checks[2] else '✗'}")
        print(f"   ✅ Title changed from 'Need Help?': {'✓' if contact_checks[3] else '✗'}")
        
        # Check 2: Priority Level Removal for Public
        priority_checks = [
            "isSpecialRequester" in request_form_content,
            "Only for Special Requesters" in request_form_content or "law department" in request_form_content,
            "user.role === 'admin'" in request_form_content
        ]
        
        print("\n🎯 2. PRIORITY LEVEL RESTRICTION:")
        print(f"   ✅ Special requester check implemented: {'✓' if priority_checks[0] else '✗'}")
        print(f"   ✅ Priority limited to special users: {'✓' if priority_checks[1] else '✗'}")
        print(f"   ✅ Admin/staff role check: {'✓' if priority_checks[2] else '✗'}")
        
        # Check 3: Payment Information
        payment_checks = [
            "Payment Information" in request_form_content,
            "Cash:" in request_form_content,
            "Check:" in request_form_content,
            "Credit/debit card payments are not currently accepted" in request_form_content or "not currently accepted" in request_form_content
        ]
        
        print("\n💳 3. PAYMENT OPTIONS:")
        print(f"   ✅ Payment section added: {'✓' if payment_checks[0] else '✗'}")
        print(f"   ✅ Cash payment option: {'✓' if payment_checks[1] else '✗'}")
        print(f"   ✅ Check payment option: {'✓' if payment_checks[2] else '✗'}")
        print(f"   ✅ No credit/debit card notice: {'✓' if payment_checks[3] else '✗'}")
        
        # Check 4: Case Number Field
        case_number_checks = [
            "case_number" in request_form_content,
            "Case Number" in request_form_content,
            "handleCaseNumberChange" in request_form_content,
            "##-######" in request_form_content,
            "24-123456" in request_form_content
        ]
        
        print("\n📋 4. CASE NUMBER FIELD:")
        print(f"   ✅ Case number field added: {'✓' if case_number_checks[0] else '✗'}")
        print(f"   ✅ Case number label: {'✓' if case_number_checks[1] else '✗'}")
        print(f"   ✅ Format handler implemented: {'✓' if case_number_checks[2] else '✗'}")
        print(f"   ✅ Format pattern ##-######: {'✓' if case_number_checks[3] else '✗'}")
        print(f"   ✅ Example format shown: {'✓' if case_number_checks[4] else '✗'}")
        
        # Check 5: Cost Acknowledgment (existing feature)
        cost_checks = [
            "COST ACKNOWLEDGMENT" in request_form_content,
            "$75" in request_form_content,
            "$750" in request_form_content,
            "ORC §149.43 and HB 315" in request_form_content
        ]
        
        print("\n💰 5. COST ACKNOWLEDGMENT (EXISTING):")
        print(f"   ✅ Cost acknowledgment header: {'✓' if cost_checks[0] else '✗'}")
        print(f"   ✅ $75 deposit mention: {'✓' if cost_checks[1] else '✗'}")
        print(f"   ✅ $750 max cost: {'✓' if cost_checks[2] else '✗'}")
        print(f"   ✅ Legal statutes: {'✓' if cost_checks[3] else '✗'}")
        
        # Overall Summary
        all_checks = contact_checks + priority_checks + payment_checks + case_number_checks + cost_checks
        passed_checks = sum(all_checks)
        total_checks = len(all_checks)
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Passed: {passed_checks}/{total_checks} ({(passed_checks/total_checks*100):.1f}%)")
        
        if passed_checks == total_checks:
            print("   🎉 ALL CHANGES SUCCESSFULLY IMPLEMENTED!")
        else:
            print("   ⚠️  Some changes may need attention")
            
    except Exception as e:
        print(f"❌ Error verifying changes: {str(e)}")
    
    # Check RequestDetail.js as well
    print(f"\n📄 CHECKING REQUESTDETAIL.JS:")
    try:
        with open('/app/frontend/src/components/RequestDetail.js', 'r') as f:
            detail_content = f.read()
        
        detail_checks = [
            "records@Shakerpd.com" in detail_content,
            "(216) 1220" in detail_content,
            "Contact Information" in detail_content
        ]
        
        print(f"   ✅ Email updated: {'✓' if detail_checks[0] else '✗'}")
        print(f"   ✅ Phone updated: {'✓' if detail_checks[1] else '✗'}")
        print(f"   ✅ Title updated: {'✓' if detail_checks[2] else '✗'}")
        
    except Exception as e:
        print(f"   ❌ Error checking RequestDetail: {str(e)}")

if __name__ == "__main__":
    verify_changes()
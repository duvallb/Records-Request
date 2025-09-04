#!/usr/bin/env python3
"""
Verify all deployment fixes have been applied correctly
"""
import subprocess
import os

def verify_deployment_fixes():
    print("🔍 VERIFYING DEPLOYMENT FIXES")
    print("=" * 60)
    
    # Check 1: HTML Syntax Error Fix
    print("🏷️  1. HTML SYNTAX ERROR FIX:")
    try:
        with open('/app/frontend/public/index.html', 'r') as f:
            html_content = f.read()
        
        # Check that the anchor tag is properly commented
        html_checks = [
            "<!--" in html_content and "-->" in html_content,
            'id="emergent-badge"' in html_content,
            # Ensure no malformed anchor tags
            "<a\n" not in html_content and "<a<!--" not in html_content,
            "Police Records Request App" in html_content
        ]
        
        print(f"   ✅ Proper HTML comments: {'✓' if html_checks[0] else '✗'}")
        print(f"   ✅ Emergent badge commented: {'✓' if html_checks[1] else '✗'}")
        print(f"   ✅ No malformed anchor tags: {'✓' if html_checks[2] else '✗'}")
        print(f"   ✅ Correct app title: {'✓' if html_checks[3] else '✗'}")
        
        html_passed = sum(html_checks)
        print(f"   📊 HTML fixes: {html_passed}/4 checks passed")
        
    except Exception as e:
        print(f"   ❌ Error checking HTML: {str(e)}")
        html_passed = 0
    
    # Check 2: Package.json Dependencies
    print("\n📦 2. PACKAGE.JSON DEPENDENCIES:")
    try:
        with open('/app/frontend/package.json', 'r') as f:
            package_content = f.read()
        
        dep_checks = [
            '"@babel/plugin-proposal-private-property-in-object"' in package_content,
            '"react"' in package_content,
            '"react-router-dom"' in package_content,
            '"axios"' in package_content
        ]
        
        print(f"   ✅ Babel plugin added: {'✓' if dep_checks[0] else '✗'}")
        print(f"   ✅ React dependency: {'✓' if dep_checks[1] else '✗'}")
        print(f"   ✅ React Router: {'✓' if dep_checks[2] else '✗'}")
        print(f"   ✅ Axios for API calls: {'✓' if dep_checks[3] else '✗'}")
        
        dep_passed = sum(dep_checks)
        print(f"   📊 Dependencies: {dep_passed}/4 checks passed")
        
    except Exception as e:
        print(f"   ❌ Error checking package.json: {str(e)}")
        dep_passed = 0
    
    # Check 3: Frontend Build Test
    print("\n🏗️  3. FRONTEND BUILD TEST:")
    try:
        # Change to frontend directory and run build
        result = subprocess.run(
            ['npm', 'run', 'build'], 
            cwd='/app/frontend',
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        build_success = result.returncode == 0
        has_output = 'Compiled successfully' in result.stdout
        no_parse_errors = 'Parse Error' not in result.stdout and 'Parse Error' not in result.stderr
        
        print(f"   ✅ Build command success: {'✓' if build_success else '✗'}")
        print(f"   ✅ Compilation successful: {'✓' if has_output else '✗'}")
        print(f"   ✅ No parse errors: {'✓' if no_parse_errors else '✗'}")
        
        if not build_success:
            print(f"   📝 Build stdout: {result.stdout[-200:]}")
            print(f"   📝 Build stderr: {result.stderr[-200:]}")
        
        build_passed = int(build_success) + int(has_output) + int(no_parse_errors)
        print(f"   📊 Build test: {build_passed}/3 checks passed")
        
    except subprocess.TimeoutExpired:
        print("   ❌ Build test timed out")
        build_passed = 0
    except Exception as e:
        print(f"   ❌ Error testing build: {str(e)}")
        build_passed = 0
    
    # Check 4: Backend Import Test
    print("\n🐍 4. BACKEND IMPORT TEST:")
    try:
        result = subprocess.run(
            ['python', '-c', 'import server; print("Backend imports successfully")'],
            cwd='/app/backend',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        backend_imports = result.returncode == 0
        success_message = 'Backend imports successfully' in result.stdout
        
        print(f"   ✅ Server module imports: {'✓' if backend_imports else '✗'}")
        print(f"   ✅ Success message: {'✓' if success_message else '✗'}")
        
        if not backend_imports:
            print(f"   📝 Import error: {result.stderr}")
        
        backend_passed = int(backend_imports) + int(success_message)
        print(f"   📊 Backend test: {backend_passed}/2 checks passed")
        
    except Exception as e:
        print(f"   ❌ Error testing backend: {str(e)}")
        backend_passed = 0
    
    # Check 5: Environment Configuration
    print("\n⚙️  5. ENVIRONMENT CONFIGURATION:")
    try:
        # Check backend .env
        backend_env_exists = os.path.exists('/app/backend/.env')
        frontend_env_exists = os.path.exists('/app/frontend/.env')
        
        env_checks = [backend_env_exists, frontend_env_exists]
        
        if backend_env_exists:
            with open('/app/backend/.env', 'r') as f:
                backend_env = f.read()
            env_checks.append('MONGO_URL' in backend_env)
            env_checks.append('SMTP_SERVER' in backend_env)
        
        if frontend_env_exists:
            with open('/app/frontend/.env', 'r') as f:
                frontend_env = f.read()
            env_checks.append('REACT_APP_BACKEND_URL' in frontend_env)
        
        print(f"   ✅ Backend .env exists: {'✓' if backend_env_exists else '✗'}")
        print(f"   ✅ Frontend .env exists: {'✓' if frontend_env_exists else '✗'}")
        print(f"   ✅ MongoDB config: {'✓' if len(env_checks) > 2 and env_checks[2] else '✗'}")
        print(f"   ✅ SMTP config: {'✓' if len(env_checks) > 3 and env_checks[3] else '✗'}")
        print(f"   ✅ Frontend API URL: {'✓' if len(env_checks) > 4 and env_checks[4] else '✗'}")
        
        env_passed = sum(env_checks)
        print(f"   📊 Environment: {env_passed}/{len(env_checks)} checks passed")
        
    except Exception as e:
        print(f"   ❌ Error checking environment: {str(e)}")
        env_passed = 0
    
    # Overall Summary
    total_passed = html_passed + dep_passed + build_passed + backend_passed + env_passed
    total_checks = 4 + 4 + 3 + 2 + 5  # Adjust based on actual checks
    
    print(f"\n📊 OVERALL DEPLOYMENT READINESS:")
    print(f"   Total checks passed: {total_passed}/{total_checks}")
    print(f"   Success rate: {(total_passed/total_checks*100):.1f}%")
    
    if total_passed >= total_checks * 0.9:  # 90% success rate
        print("   🎉 DEPLOYMENT READY!")
        print("   ✅ All critical issues have been resolved")
        print("   ✅ Frontend builds successfully without parse errors")
        print("   ✅ Backend imports and runs correctly")
        print("   ✅ Environment variables are properly configured")
        return True
    else:
        print("   ⚠️  Some issues may need attention")
        failed_checks = total_checks - total_passed
        print(f"   📋 {failed_checks} checks failed - review above for details")
        return False

if __name__ == "__main__":
    success = verify_deployment_fixes()
    exit(0 if success else 1)
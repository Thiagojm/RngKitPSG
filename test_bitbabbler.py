#!/usr/bin/env python3
"""
BitBabbler Device Test Script
This script helps diagnose BitBabbler connection issues
"""

import subprocess
import sys
import os

def test_bitbabbler_detection():
    """Test if BitBabbler device is detected"""
    print("🔍 Testing BitBabbler Device Detection...")
    print("=" * 50)
    
    # Check if seedd.exe exists
    seedd_path = "src/bin/seedd.exe"
    if not os.path.exists(seedd_path):
        print(f"❌ ERROR: {seedd_path} not found!")
        print("   Make sure you're running this from the RngKitPSG directory")
        return False
    
    print(f"✅ Found seedd.exe at: {seedd_path}")
    
    # Test device detection
    print("\n🔍 Testing device detection...")
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # Run seedd with device detection
        cmd = f"{seedd_path} --limit-max-xfer --no-qa -f0 -b 1"
        print(f"Running: {cmd}")
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              startupinfo=startupinfo, text=True)
        stdout, stderr = proc.communicate(timeout=10)
        
        print(f"Return code: {proc.returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")
        
        if proc.returncode == 0 and stdout:
            print("✅ BitBabbler device detected successfully!")
            print(f"   Data received: {len(stdout)} bytes")
            return True
        else:
            print("❌ BitBabbler device NOT detected")
            if stderr:
                print(f"   Error: {stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout: Device detection took too long")
        proc.kill()
        return False
    except Exception as e:
        print(f"❌ Error running seedd: {e}")
        return False

def test_seedd_help():
    """Test if seedd.exe runs and shows help"""
    print("\n🔍 Testing seedd.exe help...")
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        proc = subprocess.Popen("src/bin/seedd.exe --help", stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, startupinfo=startupinfo, text=True)
        stdout, stderr = proc.communicate(timeout=5)
        
        if proc.returncode == 0:
            print("✅ seedd.exe is working")
            print("Help output (first 10 lines):")
            for i, line in enumerate(stdout.split('\n')[:10]):
                print(f"   {line}")
            return True
        else:
            print(f"❌ seedd.exe error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running seedd --help: {e}")
        return False

def main():
    print("🎲 BitBabbler Device Test")
    print("=" * 50)
    
    # Test 1: Check if seedd.exe works
    if not test_seedd_help():
        print("\n❌ CRITICAL: seedd.exe is not working properly")
        print("   Please check your installation")
        return
    
    # Test 2: Check device detection
    if test_bitbabbler_detection():
        print("\n🎉 SUCCESS: BitBabbler is working correctly!")
        print("   You can now use it in the Streamlit app")
    else:
        print("\n❌ FAILURE: BitBabbler device not detected")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if BitBabbler is connected to USB")
        print("2. Install Visual C++ Redistributable (vcredist_x64.exe)")
        print("3. Install BitBabbler driver using Zadig (zadig-2.8.exe)")
        print("4. Try different USB ports")
        print("5. Check Windows Device Manager for the device")

if __name__ == "__main__":
    main()

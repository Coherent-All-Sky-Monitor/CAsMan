#!/usr/bin/env python3
"""
Quick test script to verify the web visualization font loading fix.
"""

import os
import sys
import importlib.util
from pathlib import Path

def test_web_viz_static_config():
    """Test that the web visualization Flask app is configured with proper static folder."""
    
    # Get the path to the web visualization script
    script_dir = Path(__file__).parent
    web_script_path = script_dir / "scripts" / "visualize_analog_chains_web.py"
    
    if not web_script_path.exists():
        print(f"❌ Error: Web visualization script not found at {web_script_path}")
        return False
    
    # Import the web module
    spec = importlib.util.spec_from_file_location("web_viz", web_script_path)
    web_module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(web_module)
        
        # Check if Flask app is properly configured
        app = web_module.app
        static_folder = app.static_folder
        
        print(f"✅ Flask app static folder: {static_folder}")
        
        # Check if the static folder exists and contains fonts
        if static_folder and os.path.exists(static_folder):
            fonts_dir = os.path.join(static_folder, "fonts")
            if os.path.exists(fonts_dir):
                font_files = os.listdir(fonts_dir)
                print(f"✅ Found {len(font_files)} font files in static folder")
                
                # Check for the specific font that was failing
                if "NationalPark-ExtraBold.woff" in font_files:
                    print("✅ NationalPark-ExtraBold.woff found!")
                    return True
                else:
                    print("❌ NationalPark-ExtraBold.woff not found in fonts directory")
                    return False
            else:
                print("❌ Fonts directory not found in static folder")
                return False
        else:
            print("❌ Static folder not configured or doesn't exist")
            return False
            
    except Exception as e:
        print(f"❌ Error importing web module: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing web visualization static file configuration...")
    success = test_web_viz_static_config()
    
    if success:
        print("\n🎉 Web visualization static file configuration looks good!")
        print("💡 The font loading error should now be fixed.")
    else:
        print("\n❌ There may still be issues with static file configuration.")
    
    sys.exit(0 if success else 1)

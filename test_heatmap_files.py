#!/usr/bin/env python3
"""
Test script to check if each Heatmap file is working
"""
import sys
import os
import ast
import importlib.util

# Change to Heatmap directory
os.chdir('/workspaces/Project-SafeSphere/Heatmap')
sys.path.insert(0, '/workspaces/Project-SafeSphere/Heatmap')

def check_syntax(filepath):
    """Check if a Python file has valid syntax"""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, "✅ Syntax OK"
    except SyntaxError as e:
        return False, f"❌ Syntax Error: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"

def check_imports(filepath):
    """Try to load the module and check imports"""
    try:
        spec = importlib.util.spec_from_file_location("temp_module", filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                return True, "✅ Imports OK"
            except ImportError as e:
                return False, f"❌ Import Error: {str(e)[:100]}"
            except Exception as e:
                return False, f"⚠️  Runtime Issue: {str(e)[:100]}"
        else:
            return False, "❌ Could not load module spec"
    except Exception as e:
        return False, f"❌ Error: {str(e)[:100]}"

def check_file(filepath):
    """Check a single file"""
    print(f"\n{'='*80}")
    print(f"FILE: {filepath}")
    print(f"{'='*80}")
    
    if not os.path.exists(filepath):
        print(f"❌ FILE NOT FOUND")
        return
    
    # Check file size
    size = os.path.getsize(filepath)
    print(f"📁 File size: {size} bytes")
    
    if size == 0:
        print(f"⚠️  EMPTY FILE")
        return
    
    # Check syntax
    syntax_ok, syntax_msg = check_syntax(filepath)
    print(f"SYNTAX: {syntax_msg}")
    
    if not syntax_ok:
        return
    
    # Check imports
    import_ok, import_msg = check_imports(filepath)
    print(f"IMPORTS: {import_msg}")

# List of files to check
files_to_check = [
    "backend_api.py",
    "shared/utils.py",
    "engines/threat_cv/main.py",
    "engines/threat_cv/inference/video_source.py",
    "engines/threat_cv/inference/motion_detector.py",
    "engines/threat_cv/inference/person_detector.py",
    "engines/threat_cv/inference/tracker.py",
    "engines/threat_cv/inference/behavior_analyzer.py",
    "engines/threat_cv/inference/context_boost.py",
    "engines/threat_cv/inference/threat_scorer.py",
    "engines/threat_cv/inference/weapon_detector.py",
    "engines/threat_cv/inference/threat_classifier.py",
    "engines/threat_cv/inference/enhanced_context.py",
    "engines/threat_cv/inference/incident_logger.py",
    "engines/llm_engine/main.py",
    "engines/safe_route/main.py",
    "engines/voice_ai/main.py",
    "engines/voice_ai/inference/audio_io.py",
    "engines/voice_ai/inference/keyword_detector.py",
    "engines/voice_ai/inference/speech_recognizer.py",
    "engines/voice_ai/inference/whisper_engine.py",
]

print("\n" + "🛡️ "*40)
print("SAFESPHERE HEATMAP FILES - DIAGNOSTIC TEST")
print("🛡️ "*40)

summary = []
for filepath in files_to_check:
    check_file(filepath)
    summary.append(filepath)

print(f"\n{'='*80}")
print(f"SUMMARY: Checked {len(summary)} files")
print(f"{'='*80}\n")

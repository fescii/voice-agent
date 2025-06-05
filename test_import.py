#!/usr/bin/env python3

import sys
print("Python path:", sys.path)

# Add current directory to path if not already there
if '.' not in sys.path:
    sys.path.append('.')
print("Updated Python path:", sys.path)

print("Trying to import services.ringover module...")
try:
    import services.ringover
    print("Imported services.ringover")
    print("Available in services.ringover:", dir(services.ringover))
except ImportError as e:
    print(f"Import error with services.ringover: {e}")

print("\nTrying to import RingoverStreamingService directly...")
try:
    from services.ringover import RingoverStreamingService
    print("Import successful!")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()

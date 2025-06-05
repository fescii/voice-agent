# Test importing step by step

def print_separator():
  print("\n" + "-" * 40 + "\n")


print("Step 1: Import the streaming module")
try:
  from services.ringover import streaming
  print("Successfully imported streaming module")
  print("Contents:", dir(streaming))
except Exception as e:
  print(f"Error importing streaming: {e}")

print_separator()

print("Step 2: Check if __init__.py contents are properly loaded")
try:
  import services.ringover.streaming
  print("Successfully checked streaming package")
  print("Available from streaming package:", dir(services.ringover.streaming))
except Exception as e:
  print(f"Error accessing streaming package: {e}")

print_separator()

print("Step 3: Import streaming.service")
try:
  from services.ringover.streaming import service
  print("Successfully imported streaming.service")
  print("Contents:", dir(service))
except Exception as e:
  print(f"Error importing streaming.service: {e}")

print_separator()

print("Step 4: Import RingoverStreamingService directly from streaming.service")
try:
  from services.ringover.streaming.service import RingoverStreamingService
  print("Successfully imported RingoverStreamingService from streaming.service")
except Exception as e:
  print(
      f"Error importing RingoverStreamingService from streaming.service: {e}")

print_separator()

print("Step 5: Import RingoverStreamingService from ringover directly")
try:
  from services.ringover import RingoverStreamingService
  print("Successfully imported RingoverStreamingService from ringover")
except Exception as e:
  print(f"Error importing RingoverStreamingService from ringover: {e}")

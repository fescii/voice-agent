"""
Script flow analysis and path finding utilities.
"""

from typing import Dict, List, Union
from pathlib import Path

from services.agent.conversation.script.advanced import load_script_from_json


async def analyze_script_flow(script_path: Union[str, Path]) -> None:
  """
  Analyze a script's flow structure.

  Args:
      script_path: Path to the script file
  """
  print(f"\n===== ANALYZING SCRIPT FLOW: {script_path} =====\n")

  script = await load_script_from_json(script_path)
  if not script:
    print("Failed to load script")
    return

  # Create a map of states by name
  states_by_name = {state.name: state for state in script.states}

  # Create a graph of state transitions
  graph = {}
  for state in script.states:
    graph[state.name] = []

  for edge in script.edges:
    if edge.from_state not in graph:
      graph[edge.from_state] = []
    graph[edge.from_state].append(edge.to_state)

  # Print flow stats
  print(f"Script: {script.name}")
  print(f"Total states: {len(script.states)}")
  print(f"Total edges: {len(script.edges)}")
  print(f"Starting state: {script.starting_state}")

  # Identify terminal states
  terminal_states = [
      s.name for s in script.states if s.type.value == "terminal"]
  print(
      f"Terminal states: {', '.join(terminal_states) if terminal_states else 'None'}")

  # Identify decision points
  decision_states = [
      s.name for s in script.states if s.type.value == "decision"]
  print(
      f"Decision points: {', '.join(decision_states) if decision_states else 'None'}")

  # Find longest path if we have a starting state
  starting_state = script.starting_state or (
      script.states[0].name if script.states else "")
  if starting_state:
    longest_path = find_longest_path(graph, starting_state)
    print(f"Longest possible path: {' -> '.join(longest_path)}")
    print(f"Max path length: {len(longest_path) - 1} transitions")
  else:
    print("No starting state defined, cannot analyze paths")

  print("\nFlow analysis complete!")


def find_longest_path(graph: Dict[str, List[str]], start: str) -> List[str]:
  """
  Find the longest possible path in a directed graph.

  Args:
      graph: Adjacency list representation of the graph
      start: Starting node

  Returns:
      List of nodes in the longest path
  """
  # Use dynamic programming to find longest path
  memo = {}

  def dfs(node):
    if node in memo:
      return memo[node]

    if not graph.get(node, []):
      return [node]

    max_path = [node]

    for neighbor in graph.get(node, []):
      path = dfs(neighbor)
      if len(path) + 1 > len(max_path):
        max_path = [node] + path

    memo[node] = max_path
    return max_path

  return dfs(start)

"""Task Executor for Local AI Development Environment.

This module implements the core orchestration component that executes development
tasks through an agent loop pattern. The TaskExecutor coordinates all system
components (Code Agent, Context Manager, LLM Interface) to plan, execute, observe,
reflect, and iterate on development tasks.

Key responsibilities:
- Orchestrate agent loop: plan → execute → observe → reflect → iterate
- Coordinate all system components to complete development tasks
- Manage task state and execution context
- Provide progress tracking and logging
- Handle error recovery and retry logic
- Manage context window for LLM (summarize old steps when needed)

Requirements implemented:
- 7.1: Plan steps needed to complete development tasks
- 7.2: Coordinate all system components to execute the plan
- 7.3: Write tests for new functionality
- 7.4: Run tests to verify correctness
- 7.5: Debug and fix issues when tests fail
- 7.6: Refactor code when necessary to maintain quality
- 7.7: Provide summary of changes made when task is complete
- 7.8: Report specific blockers if task cannot be completed
- 15.1: Provide progress updates while executing tasks
- 15.5: Provide task completion summaries
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

from src.core.models import (
    ExecutionPlan,
    ExecutionStep,
    TaskResult,
    Tool,
    ToolCall,
    LLMResponse
)
from src.core.llm_interface import (
    LocalLLMInterface,
    LLMError,
    ModelUnavailableError,
    LLMTimeoutError,
    InvalidResponseError
)
from src.agents.code_agent import CodeAgent
from src.context.context_manager import ContextManager
from src.agents.file_operations import OperationResult


class TaskExecutor:
    """Orchestrates development task execution through agent loop.
    
    The TaskExecutor implements the core agent loop pattern:
    1. Plan: Use LLM to break task into execution steps
    2. Execute: Execute steps using appropriate tools (Code Agent, etc.)
    3. Observe: Collect results from tool execution
    4. Reflect: LLM analyzes results and decides next action
    5. Iterate: Continue until task is complete or blocked
    
    State Management:
    - Maintains execution history (actions taken, results observed)
    - Tracks which files have been modified
    - Stores test results and verification status
    - Manages context window for LLM (summarizes old steps as needed)
    """
    
    # Maximum number of agent loop iterations before forcing completion
    MAX_ITERATIONS = 20
    
    # Maximum context length (in tokens) before summarization is triggered
    MAX_CONTEXT_TOKENS = 12000
    
    def __init__(
        self,
        llm_interface: LocalLLMInterface,
        code_agent: CodeAgent,
        context_manager: ContextManager,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize TaskExecutor.
        
        Args:
            llm_interface: Interface for communicating with local LLM
            code_agent: Agent for code operations (create, edit, search, etc.)
            context_manager: Manager for project context and analysis
            logger: Logger for tracking execution. If None, creates default logger.
        """
        self.llm = llm_interface
        self.code_agent = code_agent
        self.context_manager = context_manager
        self.logger = logger or self._create_default_logger()
        
        # Execution state
        self.execution_history: List[Dict[str, Any]] = []
        self.files_modified: List[str] = []
        self.test_results: Dict[str, bool] = {}
        self.current_iteration = 0
        
        self.logger.info("TaskExecutor initialized")
    
    def execute_task(self, task_description: str) -> TaskResult:
        """Execute a complete development task.
        
        This is the main entry point for task execution. It orchestrates the
        full agent loop from planning through completion.
        
        Args:
            task_description: Natural language description of the task to complete
            
        Returns:
            TaskResult with success status, actions taken, files modified,
            test results, and execution log
            
        Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 15.1, 15.5
        
        Example:
            result = executor.execute_task(
                "Create a new Python module for string utilities with tests"
            )
            if result.success:
                print(f"Task completed. Modified files: {result.files_modified}")
            else:
                print(f"Task failed: {result.error_message}")
        """
        start_time = datetime.now()
        self.logger.info(f"[{start_time}] Starting task execution: {task_description}")
        
        # Reset execution state
        self.execution_history = []
        self.files_modified = []
        self.test_results = {}
        self.current_iteration = 0
        
        try:
            # Step 1: Plan the task
            self.logger.info("Phase 1: Planning task")
            plan = self.plan_task(task_description)
            
            if not plan or not plan.steps:
                error_msg = "Failed to generate execution plan"
                self.logger.error(error_msg)
                return self._create_error_result(error_msg, "planning_failed")
            
            self.logger.info(f"Generated plan with {len(plan.steps)} steps")
            self.logger.info(f"Estimated complexity: {plan.estimated_complexity}")
            self.logger.info(f"Required tools: {', '.join(plan.required_tools)}")
            
            # Step 2: Execute agent loop
            self.logger.info("Phase 2: Executing agent loop")
            completed = False
            error_message = None
            
            while not completed and self.current_iteration < self.MAX_ITERATIONS:
                self.current_iteration += 1
                self.logger.info(f"\n--- Iteration {self.current_iteration} ---")
                
                # Execute next step(s) from plan
                if self.current_iteration == 1:
                    # First iteration: execute initial planned steps
                    for step in plan.steps:
                        self.logger.info(f"Executing step: {step.action}")
                        self.logger.debug(f"Rationale: {step.rationale}")
                        
                        step_result = self.execute_step(step)
                        
                        if not step_result.success:
                            self.logger.warning(f"Step failed: {step_result.message}")
                            # Continue with other steps - reflection will decide if we should retry
                else:
                    # Subsequent iterations: LLM decides next actions based on results
                    next_action = self._reflect_and_plan_next(task_description)
                    
                    if not next_action:
                        error_message = "Failed to determine next action"
                        self.logger.error(error_message)
                        break
                    
                    if next_action.action == "complete":
                        self.logger.info("Task marked as complete by LLM")
                        completed = True
                        break
                    elif next_action.action == "blocked":
                        error_message = next_action.parameters.get("reason", "Task blocked")
                        self.logger.error(f"Task blocked: {error_message}")
                        break
                    else:
                        # Execute the next action
                        self.logger.info(f"Executing next action: {next_action.action}")
                        step_result = self.execute_step(next_action)
                
                # Check if we should continue
                completed = self.should_continue(self.execution_history)
                
                if completed:
                    self.logger.info("Task execution determined to be complete")
                    break
            
            # Check if we hit max iterations
            if self.current_iteration >= self.MAX_ITERATIONS and not completed:
                self.logger.warning(f"Reached maximum iterations ({self.MAX_ITERATIONS})")
                error_message = f"Task did not complete within {self.MAX_ITERATIONS} iterations"
            
            # Step 3: Generate result
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            success = completed and error_message is None
            
            # Extract actions taken from execution history
            actions_taken = [
                ExecutionStep(
                    action=entry["action"],
                    parameters=entry["parameters"],
                    rationale=entry.get("rationale", "")
                )
                for entry in self.execution_history
            ]
            
            # Generate execution log
            execution_log = [
                f"[{entry['timestamp']}] {entry['action']}: {entry.get('result', {}).get('message', 'N/A')}"
                for entry in self.execution_history
            ]
            
            result = TaskResult(
                success=success,
                actions_taken=actions_taken,
                files_modified=self.files_modified,
                tests_passed=all(self.test_results.values()) if self.test_results else False,
                error_message=error_message,
                execution_log=execution_log
            )
            
            # Log completion summary
            self.logger.info(f"\n[{end_time}] Task execution {'completed' if success else 'failed'}")
            self.logger.info(f"Duration: {duration:.2f}s")
            self.logger.info(f"Iterations: {self.current_iteration}")
            self.logger.info(f"Actions taken: {len(actions_taken)}")
            self.logger.info(f"Files modified: {len(self.files_modified)}")
            
            if self.files_modified:
                self.logger.info("Modified files:")
                for file_path in self.files_modified:
                    self.logger.info(f"  - {file_path}")
            
            if self.test_results:
                passed = sum(1 for v in self.test_results.values() if v)
                total = len(self.test_results)
                self.logger.info(f"Tests: {passed}/{total} passed")
            
            if error_message:
                self.logger.error(f"Error: {error_message}")
            
            return result
            
        except LLMError as e:
            error_msg = f"LLM error during task execution: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_result(error_msg, "llm_error")
        except Exception as e:
            error_msg = f"Unexpected error during task execution: {str(e)}"
            self.logger.exception(error_msg)
            return self._create_error_result(error_msg, "unexpected")
    
    def plan_task(self, task_description: str) -> Optional[ExecutionPlan]:
        """Break task into execution steps using LLM.
        
        This method uses the LLM to analyze the task description and generate
        a structured execution plan with discrete steps.
        
        Args:
            task_description: Natural language description of the task
            
        Returns:
            ExecutionPlan with steps, complexity estimate, and required tools,
            or None if planning fails
            
        Validates: Requirement 7.1
        """
        self.logger.info("Planning task with LLM")
        
        # Build planning prompt
        prompt = self._build_planning_prompt(task_description)
        
        try:
            # Call LLM to generate plan
            response = self.llm.generate(prompt)
            
            if not response.content:
                self.logger.error("LLM returned empty response for planning")
                return None
            
            self.logger.debug(f"LLM planning response: {response.content[:500]}")
            
            # Parse plan from response
            plan = self._parse_execution_plan(response.content)
            
            return plan
            
        except LLMError as e:
            self.logger.error(f"LLM error during planning: {str(e)}")
            return None
    
    def execute_step(self, step: ExecutionStep) -> OperationResult:
        """Execute a single execution step.
        
        This routes the step to the appropriate component (Code Agent, Context
        Manager, etc.) based on the action type.
        
        Args:
            step: ExecutionStep to execute
            
        Returns:
            OperationResult with success status and message
            
        Validates: Requirement 7.2
        """
        timestamp = datetime.now()
        self.logger.debug(f"[{timestamp}] Executing step: {step.action}")
        
        result = OperationResult(success=False, message="Unknown action")
        
        try:
            # Route to appropriate handler
            if step.action == "create_file":
                result = self._execute_create_file(step)
            elif step.action == "edit_file":
                result = self._execute_edit_file(step)
            elif step.action == "read_file":
                result = self._execute_read_file(step)
            elif step.action == "search_code":
                result = self._execute_search_code(step)
            elif step.action == "run_command":
                result = self._execute_run_command(step)
            elif step.action == "analyze_code":
                result = self._execute_analyze_code(step)
            else:
                result = OperationResult(
                    success=False,
                    message=f"Unknown action: {step.action}",
                    error_type="unknown_action"
                )
            
            # Record in execution history
            self.execution_history.append({
                "timestamp": timestamp.isoformat(),
                "action": step.action,
                "parameters": step.parameters,
                "rationale": step.rationale,
                "result": {
                    "success": result.success,
                    "message": result.message
                }
            })
            
            # Track modified files
            if result.success and step.action in ["create_file", "edit_file"]:
                file_path = step.parameters.get("file_path")
                if file_path and file_path not in self.files_modified:
                    self.files_modified.append(file_path)
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing step {step.action}: {str(e)}"
            self.logger.error(error_msg)
            return OperationResult(
                success=False,
                message=error_msg,
                error_type="execution_error"
            )
    
    def should_continue(self, results: List[Dict[str, Any]]) -> bool:
        """Determine if task execution should continue or is complete.
        
        This analyzes the execution history to determine if the task is complete
        based on heuristics like:
        - All planned steps executed successfully
        - Tests are passing
        - No recent errors
        
        Args:
            results: List of execution history entries
            
        Returns:
            True if task appears complete, False if more work needed
            
        Validates: Requirement 7.7
        """
        if not results:
            return False
        
        # Check recent results (last 3 steps)
        recent = results[-3:]
        
        # If all recent steps succeeded and we have test results, check tests
        all_success = all(entry.get("result", {}).get("success", False) for entry in recent)
        
        if all_success and self.test_results:
            # If tests exist and all passed, task is likely complete
            if all(self.test_results.values()):
                self.logger.info("All tests passing - task appears complete")
                return True
        
        # If we've executed many steps without errors, might be complete
        if len(results) >= 5 and all_success:
            self.logger.info("Multiple successful steps - task may be complete")
            return True
        
        # Otherwise, continue
        return False
    
    # Private helper methods
    
    def _build_planning_prompt(self, task_description: str) -> str:
        """Build prompt for LLM to plan task execution.
        
        Args:
            task_description: Task to plan
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an AI development assistant. Break down the following development task into discrete execution steps.

Task: {task_description}

Available actions:
- create_file: Create a new file with content
- edit_file: Modify an existing file
- read_file: Read file contents
- search_code: Search for code patterns
- run_command: Execute shell command
- analyze_code: Analyze code structure

Respond with a JSON object containing:
- steps: Array of steps, each with:
  - action: One of the available actions
  - parameters: Dictionary of parameters for the action
  - rationale: Explanation of why this step is needed
- estimated_complexity: "simple", "moderate", or "complex"
- required_tools: Array of tool categories needed (e.g., ["file_ops", "code_search"])

Example response:
{{
  "steps": [
    {{
      "action": "create_file",
      "parameters": {{"file_path": "src/utils.py", "content": "def helper():\\n    pass\\n"}},
      "rationale": "Create initial file structure"
    }}
  ],
  "estimated_complexity": "simple",
  "required_tools": ["file_ops"]
}}

Respond with only the JSON object, no other text."""
        
        return prompt
    
    def _parse_execution_plan(self, llm_response: str) -> Optional[ExecutionPlan]:
        """Parse LLM response into ExecutionPlan.
        
        Args:
            llm_response: Raw LLM response text
            
        Returns:
            ExecutionPlan or None if parsing fails
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = llm_response.strip()
            
            if json_str.startswith("```"):
                # Remove markdown code fences
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Build ExecutionStep objects
            steps = []
            for step_data in data.get("steps", []):
                step = ExecutionStep(
                    action=step_data["action"],
                    parameters=step_data["parameters"],
                    rationale=step_data.get("rationale", "")
                )
                steps.append(step)
            
            # Build ExecutionPlan
            plan = ExecutionPlan(
                steps=steps,
                estimated_complexity=data.get("estimated_complexity", "moderate"),
                required_tools=data.get("required_tools", [])
            )
            
            return plan
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse execution plan: {str(e)}")
            self.logger.debug(f"LLM response: {llm_response}")
            return None
    
    def _reflect_and_plan_next(self, task_description: str) -> Optional[ExecutionStep]:
        """Use LLM to reflect on results and plan next action.
        
        Args:
            task_description: Original task description
            
        Returns:
            Next ExecutionStep to execute, or None if reflection fails
        """
        # Build reflection prompt with execution history
        prompt = self._build_reflection_prompt(task_description)
        
        try:
            response = self.llm.generate(prompt)
            
            if not response.content:
                return None
            
            # Parse next action from response
            return self._parse_next_action(response.content)
            
        except LLMError as e:
            self.logger.error(f"LLM error during reflection: {str(e)}")
            return None
    
    def _build_reflection_prompt(self, task_description: str) -> str:
        """Build prompt for LLM to reflect and plan next action.
        
        Args:
            task_description: Original task description
            
        Returns:
            Formatted prompt string
        """
        # Summarize execution history for context
        history_summary = self._summarize_execution_history()
        
        prompt = f"""You are an AI development assistant. Review the execution history and determine the next action.

Original Task: {task_description}

Execution History:
{history_summary}

Based on this history, what should the next action be?

Options:
1. Continue with another step (specify action and parameters)
2. Mark task as complete
3. Report task as blocked (explain why)

Respond with a JSON object:
{{
  "action": "create_file" | "edit_file" | "read_file" | "run_command" | "complete" | "blocked",
  "parameters": {{}},
  "rationale": "explanation"
}}

Respond with only the JSON object."""
        
        return prompt
    
    def _summarize_execution_history(self) -> str:
        """Summarize execution history for LLM context.
        
        Returns:
            Formatted summary string
        """
        if not self.execution_history:
            return "No steps executed yet."
        
        summary_lines = []
        for i, entry in enumerate(self.execution_history[-10:], 1):  # Last 10 steps
            action = entry["action"]
            success = entry.get("result", {}).get("success", False)
            message = entry.get("result", {}).get("message", "")
            
            status = "✓" if success else "✗"
            summary_lines.append(f"{i}. [{status}] {action}: {message}")
        
        return "\n".join(summary_lines)
    
    def _parse_next_action(self, llm_response: str) -> Optional[ExecutionStep]:
        """Parse LLM response into next ExecutionStep.
        
        Args:
            llm_response: Raw LLM response text
            
        Returns:
            ExecutionStep or None if parsing fails
        """
        try:
            # Extract JSON from response
            json_str = llm_response.strip()
            
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])
            
            data = json.loads(json_str)
            
            step = ExecutionStep(
                action=data["action"],
                parameters=data.get("parameters", {}),
                rationale=data.get("rationale", "")
            )
            
            return step
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse next action: {str(e)}")
            return None
    
    def _create_error_result(self, error_message: str, error_type: str) -> TaskResult:
        """Create a TaskResult for an error condition.
        
        Args:
            error_message: Error description
            error_type: Error category
            
        Returns:
            TaskResult with success=False
        """
        return TaskResult(
            success=False,
            actions_taken=[],
            files_modified=self.files_modified,
            tests_passed=False,
            error_message=error_message,
            execution_log=[f"Error ({error_type}): {error_message}"]
        )
    
    # Action execution methods
    
    def _execute_create_file(self, step: ExecutionStep) -> OperationResult:
        """Execute create_file action."""
        file_path = step.parameters.get("file_path")
        content = step.parameters.get("content", "")
        
        if not file_path:
            return OperationResult(
                success=False,
                message="Missing required parameter: file_path",
                error_type="invalid_parameters"
            )
        
        context = {
            "file_path": file_path,
            "content": content
        }
        
        return self.code_agent.create_code(step.rationale, context)
    
    def _execute_edit_file(self, step: ExecutionStep) -> OperationResult:
        """Execute edit_file action."""
        file_path = step.parameters.get("file_path")
        
        if not file_path:
            return OperationResult(
                success=False,
                message="Missing required parameter: file_path",
                error_type="invalid_parameters"
            )
        
        # Build context for edit
        context = {}
        if "new_content" in step.parameters:
            context["new_content"] = step.parameters["new_content"]
        elif "edits" in step.parameters:
            context["edits"] = step.parameters["edits"]
        else:
            return OperationResult(
                success=False,
                message="Missing required parameter: new_content or edits",
                error_type="invalid_parameters"
            )
        
        return self.code_agent.edit_code(file_path, step.rationale, context)
    
    def _execute_read_file(self, step: ExecutionStep) -> OperationResult:
        """Execute read_file action."""
        file_path = step.parameters.get("file_path")
        
        if not file_path:
            return OperationResult(
                success=False,
                message="Missing required parameter: file_path",
                error_type="invalid_parameters"
            )
        
        content, result = self.code_agent.file_ops.read_file(file_path)
        
        if result.success:
            # Store content in result for potential use
            result.data = {"content": content, "length": len(content)}
        
        return result
    
    def _execute_search_code(self, step: ExecutionStep) -> OperationResult:
        """Execute search_code action."""
        pattern = step.parameters.get("pattern")
        
        if not pattern:
            return OperationResult(
                success=False,
                message="Missing required parameter: pattern",
                error_type="invalid_parameters"
            )
        
        file_pattern = step.parameters.get("file_pattern", "*")
        
        try:
            results = self.code_agent.code_search.search_text(pattern, file_pattern)
            
            return OperationResult(
                success=True,
                message=f"Found {len(results)} matches",
                data={"results": results, "count": len(results)}
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Search failed: {str(e)}",
                error_type="search_error"
            )
    
    def _execute_run_command(self, step: ExecutionStep) -> OperationResult:
        """Execute run_command action."""
        command = step.parameters.get("command")
        
        if not command:
            return OperationResult(
                success=False,
                message="Missing required parameter: command",
                error_type="invalid_parameters"
            )
        
        cwd = step.parameters.get("cwd")
        timeout = step.parameters.get("timeout", 60)
        
        try:
            result = self.code_agent.command_executor.execute(command, cwd, timeout)
            
            # Track test results if this was a test command
            if "test" in command.lower() or "pytest" in command.lower():
                self.test_results[command] = result.return_code == 0
            
            return OperationResult(
                success=result.return_code == 0,
                message=f"Exit code: {result.return_code}",
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.return_code
                }
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Command execution failed: {str(e)}",
                error_type="command_error"
            )
    
    def _execute_analyze_code(self, step: ExecutionStep) -> OperationResult:
        """Execute analyze_code action."""
        file_path = step.parameters.get("file_path")
        
        if not file_path:
            return OperationResult(
                success=False,
                message="Missing required parameter: file_path",
                error_type="invalid_parameters"
            )
        
        try:
            analysis = self.context_manager.analyze_code(file_path)
            
            if analysis:
                return OperationResult(
                    success=True,
                    message=f"Analyzed {file_path}",
                    data={
                        "language": analysis.language,
                        "symbols_count": len(analysis.symbols),
                        "imports_count": len(analysis.imports),
                        "dependencies_count": len(analysis.dependencies)
                    }
                )
            else:
                return OperationResult(
                    success=False,
                    message=f"Failed to analyze {file_path}",
                    error_type="analysis_error"
                )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Analysis failed: {str(e)}",
                error_type="analysis_error"
            )
    
    def _create_default_logger(self) -> logging.Logger:
        """Create default logger for TaskExecutor.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('TaskExecutor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            
            logger.addHandler(handler)
        
        return logger

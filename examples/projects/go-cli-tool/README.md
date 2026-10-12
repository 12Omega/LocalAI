# Go CLI Tool Example Project

This example demonstrates using the Local AI Development Environment to build a command-line tool in Go, following Go best practices and idiomatic patterns.

## Project Structure

```
go-cli-tool/
├── cmd/
│   └── mycli/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── commands/
│   │   ├── root.go
│   │   ├── init.go
│   │   ├── list.go
│   │   └── remove.go
│   └── utils/
│       └── helpers.go
├── pkg/
│   └── api/
│       └── client.go
├── test/
│   ├── commands_test.go
│   └── utils_test.go
├── go.mod
├── go.sum
├── Makefile
└── README.md
```

## Setup

1. **Initialize module:**
   ```bash
   go mod download
   ```

2. **Build the CLI:**
   ```bash
   go build -o mycli cmd/mycli/main.go
   ```

3. **Run the CLI:**
   ```bash
   ./mycli --help
   ```

4. **Run tests:**
   ```bash
   go test ./...
   ```

5. **Run tests with coverage:**
   ```bash
   go test -cover ./...
   ```

## Example Tasks for the AI

### Task 1: Create a new CLI command

```
Create a CLI tool called "taskman" for managing tasks:
- Command: taskman add <task> - Add a new task
- Command: taskman list - List all tasks
- Command: taskman complete <id> - Mark task as complete
- Command: taskman remove <id> - Remove a task

Include:
- Use cobra library for CLI framework
- Store tasks in JSON file in user's home directory
- Add flags for filtering (--status, --priority)
- Include colored output using fatih/color
- Add proper error handling
- Include unit tests for all commands
```

### Task 2: Add configuration management

```
Implement configuration system:
- Support YAML configuration file (~/.taskman/config.yaml)
- Environment variable overrides
- Command-line flag overrides
- Config struct with viper library
- Default values for all settings
- Config validation
- Include tests for config loading
```

### Task 3: Implement API client

```
Create an HTTP client for external API:
- GET /api/tasks - Fetch tasks from server
- POST /api/tasks - Create task on server
- PUT /api/tasks/{id} - Update task
- DELETE /api/tasks/{id} - Delete task

Include:
- Retry logic with exponential backoff
- Request/response logging
- Authentication with API key
- Timeout configuration
- Error handling
- Mock HTTP server for tests
```

### Task 4: Add persistent storage

```
Implement database storage for tasks:
- Use SQLite for local storage
- Create tasks table schema
- CRUD operations with database/sql
- Connection pooling
- Transaction support
- Migration system
- Include integration tests with test database
```

### Task 5: Implement subcommands

```
Expand CLI with subcommand structure:
- taskman project create <name> - Create project
- taskman project list - List projects
- taskman task add <project> <task> - Add task to project
- taskman task list <project> - List project tasks

Use cobra for nested command structure.
Include help text for all commands and flags.
Add autocomplete support.
```

### Task 6: Add logging

```
Implement structured logging:
- Use zap or zerolog library
- Different log levels (debug, info, warn, error)
- Log to file and stdout
- Log rotation
- Configurable log level via flag
- Include request ID tracking
- Add tests for logging behavior
```

### Task 7: Debug performance issue

```
The 'taskman list' command is slow with large task lists.
Investigate and fix by:
- Profiling with pprof
- Optimizing database queries
- Adding pagination
- Implementing caching
- Benchmarking improvements
```

### Task 8: Add testing utilities

```
Create testing utilities package:
- Test fixture helpers
- Mock API client
- Test database setup/teardown
- Golden file testing for output
- Table-driven test examples
- Coverage report generation
```

## What the AI Will Do

1. **Analyze Context**: The AI will identify this as a Go project, understand the module structure, and recognize Go conventions.

2. **Generate Code**: The AI will create idiomatic Go code:
   - Package-based organization
   - Error handling with explicit returns
   - Interface-based abstractions
   - Proper use of goroutines and channels (when needed)

3. **Write Tests**: The AI will create comprehensive tests:
   - Table-driven tests
   - Benchmark tests
   - Example tests for documentation
   - Integration tests where appropriate

4. **Follow Conventions**: The AI will match Go coding style:
   - gofmt formatted code
   - Proper naming (exported vs unexported)
   - Idiomatic error handling
   - Comment conventions for godoc

5. **Verify Changes**: The AI will run `go test ./...` and `go build` to verify correctness.

## Expected Behavior

- **Code Style**: gofmt formatted, golint compliant
- **Error Handling**: Explicit error returns, descriptive error messages
- **Testing**: Table-driven tests, high coverage
- **Documentation**: godoc-compatible comments
- **Concurrency**: Proper use of goroutines and synchronization
- **Interfaces**: Small, focused interfaces
- **Packaging**: Clear public/internal separation

## Technology Stack

- **Language**: Go 1.20+
- **CLI Framework**: cobra + viper
- **HTTP Client**: net/http standard library
- **Database**: database/sql with SQLite driver
- **Logging**: zap or zerolog
- **Testing**: testing standard library
- **Formatting**: gofmt, goimports

## Common Patterns

The AI will recognize and follow these Go patterns:

**CLI Command**:
```go
package commands

import (
    "github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
    Use:   "list",
    Short: "List all tasks",
    Long:  `List all tasks with optional filtering by status or priority.`,
    RunE:  runList,
}

func init() {
    listCmd.Flags().StringP("status", "s", "", "Filter by status")
    listCmd.Flags().StringP("priority", "p", "", "Filter by priority")
}

func runList(cmd *cobra.Command, args []string) error {
    status, _ := cmd.Flags().GetString("status")
    // Implementation
    return nil
}
```

**Error Handling**:
```go
func GetTask(id int) (*Task, error) {
    task, err := db.FetchTask(id)
    if err != nil {
        return nil, fmt.Errorf("failed to fetch task %d: %w", id, err)
    }
    return task, nil
}
```

**Interface**:
```go
type TaskStore interface {
    Create(task *Task) error
    Get(id int) (*Task, error)
    List() ([]*Task, error)
    Update(task *Task) error
    Delete(id int) error
}
```

**Table-Driven Test**:
```go
func TestParseTask(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    *Task
        wantErr bool
    }{
        {
            name:  "valid task",
            input: "Buy groceries",
            want:  &Task{Description: "Buy groceries"},
        },
        {
            name:    "empty task",
            input:   "",
            wantErr: true,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseTask(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ParseTask() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("ParseTask() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

**HTTP Client**:
```go
type Client struct {
    baseURL    string
    httpClient *http.Client
}

func (c *Client) GetTask(ctx context.Context, id int) (*Task, error) {
    url := fmt.Sprintf("%s/api/tasks/%d", c.baseURL, id)
    
    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil {
        return nil, fmt.Errorf("creating request: %w", err)
    }
    
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("executing request: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("unexpected status: %d", resp.StatusCode)
    }
    
    var task Task
    if err := json.NewDecoder(resp.Body).Decode(&task); err != nil {
        return nil, fmt.Errorf("decoding response: %w", err)
    }
    
    return &task, nil
}
```

## Tips for Success

1. **Be Explicit**: Go values explicitness - specify error handling requirements
2. **Interfaces First**: Describe interfaces before concrete implementations
3. **Request Tests**: Always ask for table-driven tests
4. **Concurrency Needs**: Explicitly mention if goroutines/channels are needed
5. **Error Context**: Request descriptive error messages with context
6. **Documentation**: Ask for godoc-compatible comments

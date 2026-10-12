.PHONY: build test clean install lint fmt

# Build variables
BINARY_NAME=mycli
BUILD_DIR=bin
GO=go

# Build the binary
build:
	@echo "Building..."
	@$(GO) build -o $(BUILD_DIR)/$(BINARY_NAME) cmd/mycli/main.go

# Run tests
test:
	@echo "Running tests..."
	@$(GO) test -v ./...

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	@$(GO) test -cover -coverprofile=coverage.out ./...
	@$(GO) tool cover -html=coverage.out -o coverage.html

# Run benchmarks
bench:
	@echo "Running benchmarks..."
	@$(GO) test -bench=. -benchmem ./...

# Clean build artifacts
clean:
	@echo "Cleaning..."
	@rm -rf $(BUILD_DIR)
	@rm -f coverage.out coverage.html

# Install dependencies
install:
	@echo "Installing dependencies..."
	@$(GO) mod download

# Run linter
lint:
	@echo "Running linter..."
	@golangci-lint run ./...

# Format code
fmt:
	@echo "Formatting code..."
	@$(GO) fmt ./...
	@goimports -w .

# Run the application
run:
	@$(GO) run cmd/mycli/main.go

# Build for multiple platforms
build-all:
	@echo "Building for multiple platforms..."
	@GOOS=linux GOARCH=amd64 $(GO) build -o $(BUILD_DIR)/$(BINARY_NAME)-linux-amd64 cmd/mycli/main.go
	@GOOS=darwin GOARCH=amd64 $(GO) build -o $(BUILD_DIR)/$(BINARY_NAME)-darwin-amd64 cmd/mycli/main.go
	@GOOS=windows GOARCH=amd64 $(GO) build -o $(BUILD_DIR)/$(BINARY_NAME)-windows-amd64.exe cmd/mycli/main.go

help:
	@echo "Available targets:"
	@echo "  build         - Build the binary"
	@echo "  test          - Run tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  bench         - Run benchmarks"
	@echo "  clean         - Remove build artifacts"
	@echo "  install       - Install dependencies"
	@echo "  lint          - Run linter"
	@echo "  fmt           - Format code"
	@echo "  run           - Run the application"
	@echo "  build-all     - Build for multiple platforms"

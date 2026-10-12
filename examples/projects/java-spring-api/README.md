# Java Spring Boot API Example Project

This example demonstrates using the Local AI Development Environment to build a RESTful API with Spring Boot, following Java best practices and conventions.

## Project Structure

```
java-spring-api/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/api/
│   │   │       ├── ApiApplication.java
│   │   │       ├── controller/
│   │   │       │   └── UserController.java
│   │   │       ├── service/
│   │   │       │   └── UserService.java
│   │   │       ├── repository/
│   │   │       │   └── UserRepository.java
│   │   │       ├── model/
│   │   │       │   └── User.java
│   │   │       ├── dto/
│   │   │       │   └── UserDTO.java
│   │   │       ├── exception/
│   │   │       │   └── ResourceNotFoundException.java
│   │   │       └── config/
│   │   │           └── SecurityConfig.java
│   │   └── resources/
│   │       ├── application.properties
│   │       └── application-dev.properties
│   └── test/
│       └── java/
│           └── com/example/api/
│               ├── controller/
│               │   └── UserControllerTest.java
│               ├── service/
│               │   └── UserServiceTest.java
│               └── repository/
│                   └── UserRepositoryTest.java
├── pom.xml
└── README.md
```

## Setup

1. **Build the project:**
   ```bash
   mvn clean install
   ```

2. **Run the application:**
   ```bash
   mvn spring-boot:run
   ```

3. **Run tests:**
   ```bash
   mvn test
   ```

4. **Package as JAR:**
   ```bash
   mvn package
   ```

## Example Tasks for the AI

### Task 1: Create a new REST endpoint

```
Create a new REST endpoint for managing products:
- GET /api/products - List all products
- GET /api/products/{id} - Get product by ID
- POST /api/products - Create new product
- PUT /api/products/{id} - Update product
- DELETE /api/products/{id} - Delete product

Include:
- Product entity with JPA annotations
- ProductRepository extending JpaRepository
- ProductService with business logic
- ProductController with REST endpoints
- ProductDTO for data transfer
- Input validation using javax.validation
- Exception handling
- Unit tests and integration tests
```

### Task 2: Add authentication and authorization

```
Implement JWT-based authentication:
- Create AuthController with login and register endpoints
- Add Spring Security configuration
- Implement JWT token generation and validation
- Add UserDetailsService implementation
- Secure endpoints with @PreAuthorize annotations
- Add role-based access control (ADMIN, USER roles)
- Include tests for authentication flows
```

### Task 3: Implement database migrations

```
Add Flyway for database migrations:
- Configure Flyway in application.properties
- Create initial schema migration (V1__create_users_table.sql)
- Add migration for products table
- Include sample data migration
- Document migration naming conventions
```

### Task 4: Add API documentation

```
Integrate Swagger/OpenAPI:
- Add SpringDoc OpenAPI dependency
- Configure Swagger UI endpoint
- Add @Operation annotations to controllers
- Document request/response schemas
- Add security scheme documentation
- Include API usage examples
```

### Task 5: Implement caching

```
Add Redis caching to improve performance:
- Configure Redis connection
- Add @Cacheable to service methods
- Implement cache eviction strategies
- Add cache statistics monitoring
- Include tests for caching behavior
```

### Task 6: Add input validation

```
Enhance input validation across all DTOs:
- Add @Valid annotations to controller methods
- Use @NotNull, @NotBlank, @Size, @Email, etc.
- Create custom validators for complex rules
- Add global exception handler for validation errors
- Return structured error responses
- Include tests for validation scenarios
```

### Task 7: Debug performance issue

```
The /api/products endpoint is slow when returning large result sets.
Investigate and fix by:
- Adding pagination support (Pageable)
- Implementing lazy loading for associations
- Adding database indexes
- Optimizing queries with @Query annotations
- Measuring performance improvements
```

### Task 8: Add health checks

```
Implement Spring Boot Actuator health checks:
- Enable actuator endpoints
- Create custom health indicators
- Add database connection health check
- Add external API health check
- Configure health check security
- Document health check endpoints
```

## What the AI Will Do

1. **Analyze Context**: The AI will identify this as a Spring Boot project, understand the MVC architecture, and recognize Java conventions.

2. **Generate Code**: The AI will create Java classes following Spring Boot best practices:
   - Controller layer with REST annotations
   - Service layer with @Service annotation
   - Repository layer with JpaRepository
   - Entity classes with JPA annotations
   - DTO classes for data transfer

3. **Write Tests**: The AI will create comprehensive tests:
   - Unit tests with JUnit 5 and Mockito
   - Integration tests with @SpringBootTest
   - MockMvc for controller testing
   - Test database configuration

4. **Follow Conventions**: The AI will match the project's coding style:
   - Proper package structure
   - Naming conventions (Controller, Service, Repository suffixes)
   - Javadoc comments
   - Builder patterns where appropriate

5. **Verify Changes**: The AI will run `mvn test` to ensure all tests pass and `mvn compile` to verify the code compiles.

## Expected Behavior

- **Code Style**: Standard Java conventions, 4-space indentation
- **Architecture**: Clean architecture with separation of concerns
- **Dependency Injection**: Constructor injection preferred
- **Exception Handling**: Global exception handler with @ControllerAdvice
- **Validation**: Bean validation with proper error responses
- **Testing**: High test coverage with unit and integration tests
- **Logging**: SLF4J with Logback, structured logging
- **Documentation**: Javadoc for public APIs

## Technology Stack

- **Spring Boot**: 3.x
- **Java**: 17 or higher
- **Database**: H2 (dev), PostgreSQL (prod)
- **ORM**: Spring Data JPA
- **Testing**: JUnit 5, Mockito, MockMvc
- **Build**: Maven
- **API Docs**: SpringDoc OpenAPI
- **Security**: Spring Security with JWT
- **Migrations**: Flyway

## Common Patterns

The AI will recognize and follow these Spring Boot patterns:

**Controller**:
```java
@RestController
@RequestMapping("/api/users")
@Validated
public class UserController {
    
    private final UserService userService;
    
    public UserController(UserService userService) {
        this.userService = userService;
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUserById(@PathVariable Long id) {
        UserDTO user = userService.findById(id);
        return ResponseEntity.ok(user);
    }
    
    @PostMapping
    public ResponseEntity<UserDTO> createUser(@Valid @RequestBody UserDTO userDTO) {
        UserDTO created = userService.create(userDTO);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }
}
```

**Service**:
```java
@Service
@Transactional
public class UserService {
    
    private final UserRepository userRepository;
    
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
    
    public UserDTO findById(Long id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return UserMapper.toDTO(user);
    }
}
```

**Repository**:
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    
    @Query("SELECT u FROM User u WHERE u.active = true")
    List<User> findAllActive();
}
```

**Entity**:
```java
@Entity
@Table(name = "users")
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, unique = true)
    private String email;
    
    @Column(nullable = false)
    private String name;
    
    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    // Getters, setters, constructors
}
```

**Test**:
```java
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private UserService userService;
    
    @Test
    void getUserById_ReturnsUser_WhenUserExists() throws Exception {
        // Given
        UserDTO user = new UserDTO(1L, "test@example.com", "Test User");
        when(userService.findById(1L)).thenReturn(user);
        
        // When & Then
        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.email").value("test@example.com"))
            .andExpect(jsonPath("$.name").value("Test User"));
    }
}
```

## Tips for Success

1. **Be Specific**: Clearly specify business requirements and validation rules
2. **Mention Annotations**: Specify if you want specific Spring annotations
3. **Request Tests**: Always ask for both unit and integration tests
4. **Security Considerations**: Mention security requirements upfront
5. **Database Schema**: Describe entity relationships and constraints
6. **Error Handling**: Specify how errors should be returned to clients

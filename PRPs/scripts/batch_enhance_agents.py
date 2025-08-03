"""
Batch agent enhancement script for PRP-aware capabilities
Efficiently enhances multiple agents with consistent PRP execution capabilities
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


def get_framework_specific_enhancements() -> Dict[str, Dict[str, str]]:
    """Define framework-specific enhancements for each agent"""
    return {
        'react-specialist': {
            'test_framework': 'Jest with React Testing Library, user-event, and MSW for API mocking',
            'red_phase': 'Create failing component tests with accessibility checks and user interaction scenarios',
            'green_phase': 'Implement minimal React components with hooks, TypeScript, and proper accessibility',
            'level_1': 'ESLint with React hooks rules, TypeScript checking, Prettier formatting, accessibility linting',
            'level_2': 'Jest/RTL test execution with coverage, component rendering validation, user interaction testing',
            'level_3': 'Component integration testing, routing validation, state management testing, API integration',
            'level_4': 'Visual regression testing with Percy, Lighthouse accessibility audits, performance profiling, bundle analysis',
            'libraries': 'React, TypeScript, React Router, Redux/Zustand, styled-components, Jest, RTL',
            'coordination': 'nextjs-specialist for full-stack React, javascript-typescript-specialist for TypeScript optimization'
        },
        'nextjs-specialist': {
            'test_framework': 'Jest with React Testing Library plus Playwright for E2E testing',
            'red_phase': 'Create failing tests for SSR/SSG, API routes, and full-stack functionality',
            'green_phase': 'Implement minimal Next.js features with App Router, Server Components, and API routes', 
            'level_1': 'ESLint with Next.js rules, TypeScript checking, next lint, Prettier formatting',
            'level_2': 'Jest unit tests, API route testing, component testing with Next.js specific utilities',
            'level_3': 'E2E testing with Playwright, SSR/SSG validation, API integration testing, database integration',
            'level_4': 'Lighthouse performance audits, Core Web Vitals testing, SEO validation, deployment testing',
            'libraries': 'Next.js, React, TypeScript, Prisma, NextAuth, Tailwind CSS, Vercel',
            'coordination': 'react-specialist for component architecture, postgresql-specialist for database integration'
        },
        'vuejs-specialist': {
            'test_framework': 'Vitest with Vue Test Utils and Cypress for component and E2E testing',
            'red_phase': 'Create failing Vue component tests with Composition API and reactive testing',
            'green_phase': 'Implement minimal Vue components with Composition API, TypeScript, and Pinia',
            'level_1': 'ESLint with Vue rules, TypeScript checking, Vue SFC linting, Prettier formatting',
            'level_2': 'Vitest execution with coverage, component testing, reactive state validation',
            'level_3': 'Component integration testing, Vue Router testing, Pinia state management validation',
            'level_4': 'E2E testing with Cypress, performance testing, bundle analysis, accessibility validation',
            'libraries': 'Vue 3, TypeScript, Pinia, Vue Router, Vite, Vitest, Nuxt.js',
            'coordination': 'javascript-typescript-specialist for TypeScript optimization, cypress-testing-specialist for E2E testing'
        },
        'flutter-specialist': {
            'test_framework': 'Flutter test framework with widget testing, integration testing, and golden tests',
            'red_phase': 'Create failing widget tests with pump and settle, gesture testing, and golden file validation',
            'green_phase': 'Implement minimal Flutter widgets with proper state management and platform integration',
            'level_1': 'dart analyze, dart format, flutter analyze, custom linting rules',
            'level_2': 'flutter test with coverage, widget testing, unit testing, mock validation',
            'level_3': 'Integration testing, platform channel testing, navigation testing, state management validation',
            'level_4': 'Performance profiling, memory leak detection, platform-specific testing, app store validation',
            'libraries': 'Flutter, Dart, Provider/Riverpod, GoRouter, Dio, Hive/Drift',
            'coordination': 'performance-optimizer for mobile performance, security-analyst for mobile security'
        },
        'docker-kubernetes-specialist': {
            'test_framework': 'Container testing with Testcontainers, Kubernetes testing with kind/minikube',
            'red_phase': 'Create failing container and infrastructure tests with security and performance validation',
            'green_phase': 'Implement minimal containerization with multi-stage builds and K8s deployments',
            'level_1': 'Dockerfile linting with hadolint, Kubernetes YAML validation, security scanning',
            'level_2': 'Container testing, image vulnerability scanning, resource validation',
            'level_3': 'Kubernetes integration testing, service mesh validation, ingress testing',
            'level_4': 'Load testing on K8s, security compliance testing, disaster recovery validation',
            'libraries': 'Docker, Kubernetes, Helm, Istio, Prometheus, Grafana',
            'coordination': 'aws-specialist for cloud deployment, security-analyst for container security'
        },
        'aws-specialist': {
            'test_framework': 'AWS CDK testing, LocalStack for local testing, pytest for infrastructure testing',
            'red_phase': 'Create failing infrastructure tests for AWS resources and deployment pipelines',
            'green_phase': 'Implement minimal AWS infrastructure with IaC and proper security configurations',
            'level_1': 'CloudFormation/CDK linting, security policy validation, cost optimization checks',
            'level_2': 'Infrastructure testing, deployment validation, resource configuration testing',
            'level_3': 'End-to-end deployment testing, service integration validation, monitoring setup',
            'level_4': 'Performance testing at scale, security compliance validation, disaster recovery testing',
            'libraries': 'AWS CDK, CloudFormation, Terraform, Serverless Framework, AWS CLI',
            'coordination': 'docker-kubernetes-specialist for container orchestration, security-analyst for cloud security'
        }
    }

def get_language_specific_enhancements() -> Dict[str, Dict[str, str]]:
    """Define language-specific enhancements for each agent"""
    return {
        'javascript-typescript-specialist': {
            'test_framework': 'Jest with React Testing Library and TypeScript support',
            'red_phase': 'Create failing Jest tests with TypeScript type safety and comprehensive assertions',
            'green_phase': 'Implement minimal TypeScript/JavaScript code following modern ES6+ standards',
            'level_1': 'ESLint with TypeScript rules, Prettier formatting, TypeScript compiler checking',
            'level_2': 'Jest test execution with coverage, type checking validation, module integration testing',
            'level_3': 'Component integration testing, API endpoint validation, build system integration, browser compatibility',
            'level_4': 'Bundle analysis, performance profiling, security scanning with npm audit, dependency vulnerability checks',
            'libraries': 'React, Node.js, Express, TypeScript, Jest, ESLint, Prettier, webpack',
            'coordination': 'react-specialist for component architecture, nextj-specialist for full-stack applications'
        },
        'go-specialist': {
            'test_framework': 'Go built-in testing package with testify assertions and benchmark support',
            'red_phase': 'Create failing Go tests with table-driven tests and comprehensive error scenarios',
            'green_phase': 'Implement minimal Go code following Go idioms and effective Go practices',
            'level_1': 'go fmt, go vet, golangci-lint comprehensive linting, go mod tidy',
            'level_2': 'go test execution with coverage reporting, race condition detection, benchmark validation',
            'level_3': 'Integration testing with databases, HTTP APIs, concurrent operation validation, performance testing',
            'level_4': 'Go profiling with pprof, memory leak detection, goroutine analysis, security scanning with gosec',
            'libraries': 'gorilla/mux, gin, gorm, testify, cobra, viper, logrus',
            'coordination': 'docker-kubernetes-specialist for containerization, performance-optimizer for concurrency optimization'
        },
        'rust-specialist': {
            'test_framework': 'Rust built-in test framework with cargo test and criterion for benchmarking',
            'red_phase': 'Create failing Rust tests with property-based testing and comprehensive error handling',
            'green_phase': 'Implement minimal Rust code following ownership principles and safety guarantees',
            'level_1': 'rustfmt formatting, clippy linting, cargo check compilation validation',
            'level_2': 'cargo test execution with coverage, borrow checker validation, unsafe code analysis',
            'level_3': 'Integration testing with async operations, FFI validation, system integration, cross-compilation testing',
            'level_4': 'Performance profiling with cargo flamegraph, memory safety analysis, security auditing with cargo-audit',
            'libraries': 'tokio, serde, clap, reqwest, sqlx, anyhow, thiserror',
            'coordination': 'performance-optimizer for systems programming optimization, security-analyst for memory safety validation'
        },
        'java-specialist': {
            'test_framework': 'JUnit 5 with Mockito, AssertJ, and comprehensive test lifecycle management',
            'red_phase': 'Create failing JUnit tests with parameterized tests and comprehensive assertion coverage',
            'green_phase': 'Implement minimal Java code following Java best practices and modern Java features',
            'level_1': 'Checkstyle, SpotBugs, PMD static analysis, Maven/Gradle build validation',
            'level_2': 'JUnit test execution with JaCoCo coverage, integration test validation, dependency injection testing',
            'level_3': 'Spring Boot integration testing, database integration, REST API validation, security testing',
            'level_4': 'JVM profiling with JProfiler, heap analysis, security scanning with OWASP dependency check',
            'libraries': 'Spring Boot, Hibernate, Jackson, Apache Commons, Guava, SLF4J',
            'coordination': 'postgresql-specialist for JPA optimization, aws-specialist for cloud deployment'
        }
    }


def generate_prp_enhancement(agent_name: str, enhancement_data: Dict[str, str]) -> str:
    """Generate PRP enhancement content for a specific agent"""
    return f"""
## PRP Execution Capabilities

When invoked with a PRP specification, this agent follows the structured TDD-PRP methodology:

### PRP Structure Understanding
- Parses Goal, Why, What, Context, Implementation Blueprint, and Validation Loop sections
- Extracts {agent_name.replace('-specialist', '').replace('-', '/')}-specific requirements and framework constraints from All Needed Context
- Identifies success criteria and measurable {agent_name.replace('-specialist', '').replace('-', '/')} development outcomes
- Maps PRP requirements to appropriate {agent_name.replace('-specialist', '').replace('-', '/')} patterns, libraries, and architectural approaches

### TDD Methodology Integration
- **Red Phase**: {enhancement_data['red_phase']}
- **Green Phase**: {enhancement_data['green_phase']}
- **Refactor Phase**: Enhances code quality using {agent_name.replace('-specialist', '').replace('-', '/')} best practices, performance optimizations, and security improvements

### 4-Level Validation Loop
- **Level 0**: Test Creation - Write failing tests with proper test organization and comprehensive scenarios
- **Level 1**: Syntax & Style - {enhancement_data['level_1']}
- **Level 2**: Unit Tests - {enhancement_data['level_2']}
- **Level 3**: Integration Testing - {enhancement_data['level_3']}
- **Level 4**: Creative Validation - {enhancement_data['level_4']}

### Autonomous Execution Pattern
When executing a PRP autonomously:
1. Parse PRP requirements and extract {agent_name.replace('-specialist', '').replace('-', '/')}-specific implementation requirements and constraints
2. Analyze existing codebase patterns for consistency with project architecture and {agent_name.replace('-specialist', '').replace('-', '/')} conventions
3. Create comprehensive test suite following {agent_name.replace('-specialist', '').replace('-', '/')} testing best practices (Red Phase)
4. Implement solution using appropriate {agent_name.replace('-specialist', '').replace('-', '/')} libraries and frameworks (Green Phase)
5. Refactor and optimize using {agent_name.replace('-specialist', '').replace('-', '/')} performance patterns and security best practices (Refactor Phase)
6. Execute complete validation loop with {agent_name.replace('-specialist', '').replace('-', '/')} ecosystem tooling
7. Report completion status with {agent_name.replace('-specialist', '').replace('-', '/')}-specific metrics for project management integration

### Context-Aware Implementation
- Analyzes existing {agent_name.replace('-specialist', '').replace('-', '/')} patterns and follows established project conventions and architecture
- Leverages {agent_name.replace('-specialist', '').replace('-', '/')}-specific libraries ({enhancement_data['libraries']}) appropriately
- Applies {agent_name.replace('-specialist', '').replace('-', '/')} security and performance best practices
- Integrates with existing {agent_name.replace('-specialist', '').replace('-', '/')} development toolchain and build systems
- Uses {agent_name.replace('-specialist', '').replace('-', '/')} ecosystem tools and package management

## TDD Integration for {agent_name.replace('-specialist', '').title().replace('-', '/')} Development

### {agent_name.replace('-specialist', '').title().replace('-', '/')}-First Development Methodology
- **Test Framework**: {enhancement_data['test_framework']}
- **Red Phase**: {enhancement_data['red_phase']}
- **Green Phase**: {enhancement_data['green_phase']}
- **Refactor Phase**: Advanced optimization, performance tuning, and security hardening

### Validation Loop ({agent_name.replace('-specialist', '').title().replace('-', '/')}-Specific)
- **Level 0**: Tests that fail initially with clear, descriptive test names and comprehensive assertions
- **Level 1**: {enhancement_data['level_1']}
- **Level 2**: {enhancement_data['level_2']}
- **Level 3**: {enhancement_data['level_3']}
- **Level 4**: {enhancement_data['level_4']}

## Autonomous Workflow Integration

### Status Reporting
- Integrates with ACTIVE_TODOS.md for {agent_name.replace('-specialist', '').replace('-', '/')} development completion tracking
- Reports implementation progress with code quality metrics and test coverage results
- Updates PRP references with development completion status and performance achievements
- Provides detailed analysis reports with recommendations for development team visibility

### Multi-Agent Coordination
- Identifies when PRP requires coordination with {enhancement_data['coordination']}
- Communicates with security-analyst to ensure security best practices and vulnerability prevention
- Ensures implementations integrate with performance-optimizer for scalability and efficiency improvements
- Coordinates with test-writer for comprehensive test coverage and quality assurance

### Error Handling and Recovery
- Graceful handling of test failures and dependency resolution issues
- Automatic retry mechanisms for transient build and toolchain issues
- Clear error reporting with actionable debugging recommendations
- Environment isolation and cleanup procedures to prevent conflicts

### Performance and Efficiency
- Optimizes development process for fast feedback while maintaining comprehensive testing and quality
- Caches analysis results for similar project patterns and library combinations
- Reuses proven patterns and configuration templates when appropriate
- Balances code comprehensiveness with development velocity and maintainability requirements
"""


def enhance_agent_file(agent_path: Path, enhancement_content: str) -> bool:
    """Add PRP enhancement to an agent file"""
    try:
        # Read existing content
        existing_content = agent_path.read_text(encoding='utf-8')
        
        # Check if already enhanced
        if "PRP Execution Capabilities" in existing_content:
            print(f"  ✅ {agent_path.name} already enhanced")
            return True
        
        # Add enhancement content
        enhanced_content = existing_content + enhancement_content
        
        # Write back to file
        agent_path.write_text(enhanced_content, encoding='utf-8')
        print(f"  ✅ Enhanced {agent_path.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to enhance {agent_path.name}: {e}")
        return False


def main():
    """Batch enhance language specialist agents"""
    parser = argparse.ArgumentParser(description='Batch enhance agents with PRP capabilities')
    parser.add_argument('--agents-dir', default='.claude/agents',
                       help='Directory containing agent files')
    parser.add_argument('--phase', choices=['language', 'framework', 'database'], 
                       default='language', help='Enhancement phase')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be enhanced without making changes')
    
    args = parser.parse_args()
    
    # Determine project root and agents directory
    project_root = Path(__file__).parent.parent.parent
    agents_dir = project_root / args.agents_dir
    
    if not agents_dir.exists():
        print(f"ERROR: Agents directory not found: {agents_dir}")
        return 1
    
    # Get enhancement data based on phase
    if args.phase == 'language':
        enhancements = get_language_specific_enhancements()
    elif args.phase == 'framework':
        enhancements = get_framework_specific_enhancements()
    else:
        print(f"ERROR: Unsupported phase: {args.phase}")
        return 1
    
    # Process agents
    enhanced_count = 0
    total_count = 0
    
    print(f"🚀 Starting {args.phase} specialists enhancement...")
    
    for agent_name, enhancement_data in enhancements.items():
        agent_file = agents_dir / f"{agent_name}.md"
        total_count += 1
        
        if not agent_file.exists():
            print(f"  ⚠️  Agent file not found: {agent_file}")
            continue
        
        if args.dry_run:
            print(f"  📋 Would enhance: {agent_name}")
            continue
        
        # Generate enhancement content
        enhancement_content = generate_prp_enhancement(agent_name, enhancement_data)
        
        # Enhance the agent
        if enhance_agent_file(agent_file, enhancement_content):
            enhanced_count += 1
    
    if not args.dry_run:
        print(f"\n✅ Enhancement complete: {enhanced_count}/{total_count} agents enhanced")
    else:
        print(f"\n📋 Dry run complete: {total_count} agents would be enhanced")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
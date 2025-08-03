"""
Main orchestration workflow coordinating all components
Pipeline processing with error handling and status updates for autonomous todo-to-PRP conversion
"""
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import argparse
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PRPs.scripts.todo_parser import (
    parse_active_todos, get_next_priority_todo, filter_todos_by_priority,
    filter_todos_by_status, get_ready_todos, TodoItem
)
from PRPs.scripts.context_injector import inject_context_for_todo, ContextPackage
from PRPs.scripts.template_selector import select_optimal_template
from PRPs.scripts.prp_generator import generate_prp_from_todo

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TodoToPRPOrchestrator:
    """Main orchestrator for autonomous todo-to-PRP conversion"""
    
    def __init__(self, project_root: Path, todos_file: Path):
        """
        Initialize orchestrator
        
        Args:
            project_root: Root directory of the project
            todos_file: Path to ACTIVE_TODOS.md file
        """
        self.project_root = Path(project_root)
        self.todos_file = Path(todos_file)
        self.templates_dir = self.project_root / "PRPs" / "templates"
        self.output_dir = self.project_root / "PRPs" / "active"
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            'todos_processed': 0,
            'prps_generated': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def orchestrate_todo_to_prp(self, todo_id: Optional[str] = None, 
                               priority: Optional[str] = None,
                               select_next: bool = False,
                               generate_prp: bool = True,
                               limit: int = 1) -> List[Dict[str, Any]]:
        """
        Main orchestration workflow
        
        Args:
            todo_id: Specific todo ID to process
            priority: Filter by priority level
            select_next: Select next priority todo automatically
            generate_prp: Whether to generate PRP files
            limit: Maximum number of todos to process
            
        Returns:
            List of processing results
        """
        logger.info("Starting todo-to-PRP orchestration")
        
        try:
            # Load todos
            todos = self._load_todos()
            if not todos:
                logger.warning("No todos found")
                return []
            
            # Select todos to process
            selected_todos = self._select_todos(todos, todo_id, priority, select_next, limit)
            if not selected_todos:
                logger.warning("No todos selected for processing")
                return []
            
            # Process each selected todo
            results = []
            for todo in selected_todos:
                try:
                    result = self._process_single_todo(todo, generate_prp)
                    results.append(result)
                    self.stats['todos_processed'] += 1
                    
                    if result['prp_generated']:
                        self.stats['prps_generated'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing todo {todo.id}: {e}")
                    self.stats['errors'] += 1
                    results.append({
                        'todo_id': todo.id,
                        'success': False,
                        'error': str(e),
                        'prp_generated': False
                    })
            
            # Update todos file with PRP references
            if generate_prp:
                self._update_todos_file(results)
            
            # Log final statistics
            self._log_final_stats()
            
            return results
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            self.stats['errors'] += 1
            raise
    
    def _load_todos(self) -> List[TodoItem]:
        """Load and validate todos from file"""
        if not self.todos_file.exists():
            raise FileNotFoundError(f"Todos file not found: {self.todos_file}")
        
        logger.info(f"Loading todos from: {self.todos_file}")
        todos = parse_active_todos(self.todos_file)
        logger.info(f"Loaded {len(todos)} todos")
        
        return todos
    
    def _select_todos(self, todos: List[TodoItem], todo_id: Optional[str],
                     priority: Optional[str], select_next: bool, limit: int) -> List[TodoItem]:
        """Select todos based on criteria"""
        
        # Specific todo ID
        if todo_id:
            todo = next((t for t in todos if t.id == todo_id), None)
            if not todo:
                logger.error(f"Todo {todo_id} not found")
                return []
            logger.info(f"Selected specific todo: {todo_id}")
            return [todo]
        
        # Next priority todo
        if select_next:
            next_todo = get_next_priority_todo(todos)
            if not next_todo:
                logger.warning("No ready todos found")
                return []
            logger.info(f"Selected next priority todo: {next_todo.id}")
            return [next_todo]
        
        # Filter by priority
        available_todos = todos
        if priority:
            available_todos = filter_todos_by_priority(todos, priority)
            logger.info(f"Filtered to {len(available_todos)} {priority} priority todos")
        
        # Get ready todos (dependencies satisfied)
        ready_todos = get_ready_todos(available_todos)
        logger.info(f"Found {len(ready_todos)} ready todos")
        
        # Apply limit
        selected = ready_todos[:limit]
        if selected:
            selected_ids = [t.id for t in selected]
            logger.info(f"Selected todos: {selected_ids}")
        
        return selected
    
    def _process_single_todo(self, todo: TodoItem, generate_prp: bool) -> Dict[str, Any]:
        """Process a single todo through the complete pipeline"""
        logger.info(f"Processing todo: {todo.id} - {todo.title}")
        
        result = {
            'todo_id': todo.id,
            'todo_title': todo.title,
            'success': False,
            'prp_generated': False,
            'template_selected': None,
            'prp_path': None,
            'agent_recommendations': [],
            'processing_time': None
        }
        
        start_time = datetime.now()
        
        try:
            # Step 1: Context injection
            logger.info(f"Injecting context for {todo.id}")
            context = inject_context_for_todo(todo, self.project_root)
            
            # Step 2: Template selection  
            logger.info(f"Selecting template for {todo.id}")
            template_name = select_optimal_template(todo, context)
            result['template_selected'] = template_name
            logger.info(f"Selected template: {template_name}")
            
            # Step 3: Agent recommendations
            result['agent_recommendations'] = self._get_agent_recommendations(todo)
            
            # Step 4: PRP generation
            if generate_prp:
                logger.info(f"Generating PRP for {todo.id}")
                prp_path = generate_prp_from_todo(
                    todo, template_name, context,
                    templates_dir=self.templates_dir,
                    output_dir=self.output_dir
                )
                result['prp_path'] = str(prp_path)
                result['prp_generated'] = True
                logger.info(f"Generated PRP: {prp_path}")
            
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Error processing {todo.id}: {e}")
            result['error'] = str(e)
            raise
        
        finally:
            result['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def _get_agent_recommendations(self, todo: TodoItem) -> List[str]:
        """Get recommended specialist agents for todo"""
        agent_mapping = {
            'python': 'python-specialist',
            'javascript': 'javascript-typescript-specialist',
            'react': 'react-specialist', 
            'vue': 'vuejs-specialist',
            'api': 'api-design-specialist',
            'database': 'postgresql-specialist',
            'security': 'security-analyst',
            'testing': 'test-writer',
            'frontend': 'react-specialist',
            'performance': 'performance-optimizer',
            'infrastructure': 'docker-kubernetes-specialist',
            'refactoring': 'refactoring-expert'
        }
        
        recommended = []
        for domain in todo.domain_areas:
            if domain in agent_mapping:
                agent = agent_mapping[domain]
                if agent not in recommended:
                    recommended.append(agent)
        
        if not recommended:
            recommended = ['general-purpose']
        
        return recommended[:3]  # Limit to 3 agents
    
    def _update_todos_file(self, results: List[Dict[str, Any]]):
        """Update ACTIVE_TODOS.md with PRP references"""
        if not self.todos_file.exists():
            return
        
        logger.info("Updating todos file with PRP references")
        
        try:
            content = self.todos_file.read_text(encoding='utf-8')
            
            for result in results:
                if result['prp_generated'] and result['prp_path']:
                    todo_id = result['todo_id']
                    prp_path = Path(result['prp_path']).name
                    
                    # Add PRP reference if not already present
                    todo_pattern = f"**{todo_id}**"
                    if todo_pattern in content:
                        # Check if PRP reference already exists
                        prp_ref_pattern = f"PRP: `PRPs/active/{prp_path}`"
                        if prp_ref_pattern not in content:
                            # Add PRP reference
                            content = content.replace(
                                f"- Status: Not Started",
                                f"- Status: Ready for Implementation\n  - PRP: `PRPs/active/{prp_path}`"
                            )
                            logger.info(f"Added PRP reference for {todo_id}")
            
            # Write updated content
            self.todos_file.write_text(content, encoding='utf-8')
            
        except Exception as e:
            logger.error(f"Error updating todos file: {e}")
    
    def _log_final_stats(self):
        """Log final processing statistics"""
        elapsed_time = (datetime.now() - self.stats['start_time']).total_seconds()
        
        logger.info("=== Orchestration Complete ===")
        logger.info(f"Todos processed: {self.stats['todos_processed']}")
        logger.info(f"PRPs generated: {self.stats['prps_generated']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Total time: {elapsed_time:.2f} seconds")
        
        if self.stats['todos_processed'] > 0:
            avg_time = elapsed_time / self.stats['todos_processed']
            logger.info(f"Average time per todo: {avg_time:.2f} seconds")
    
    def analyze_todos(self) -> Dict[str, Any]:
        """Analyze todos and provide recommendations"""
        todos = self._load_todos()
        
        analysis = {
            'total_todos': len(todos),
            'by_priority': {},
            'by_status': {},
            'ready_for_processing': 0,
            'domain_distribution': {},
            'next_recommended': None
        }
        
        # Count by priority
        for priority in ['High', 'Medium', 'Low']:
            priority_todos = filter_todos_by_priority(todos, priority)
            analysis['by_priority'][priority] = len(priority_todos)
        
        # Count by status
        for status in ['Not Started', 'In Progress', 'Completed']:
            status_todos = filter_todos_by_status(todos, status)
            analysis['by_status'][status] = len(status_todos)
        
        # Ready todos
        ready_todos = get_ready_todos(todos)
        analysis['ready_for_processing'] = len(ready_todos)
        
        # Domain distribution
        domain_counts = {}
        for todo in todos:
            for domain in todo.domain_areas:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        analysis['domain_distribution'] = domain_counts
        
        # Next recommended
        next_todo = get_next_priority_todo(todos)
        if next_todo:
            analysis['next_recommended'] = {
                'id': next_todo.id,
                'title': next_todo.title,
                'priority': next_todo.priority,
                'domains': next_todo.domain_areas
            }
        
        return analysis


def main():
    """CLI interface for the orchestrator"""
    parser = argparse.ArgumentParser(description='Todo-to-PRP Orchestrator')
    parser.add_argument('todos_file', help='Path to ACTIVE_TODOS.md file')
    parser.add_argument('--todo-id', help='Process specific todo ID')
    parser.add_argument('--priority', choices=['High', 'Medium', 'Low'], 
                       help='Filter by priority level')
    parser.add_argument('--select-next', action='store_true',
                       help='Select next priority todo automatically')
    parser.add_argument('--no-generate', action='store_true',
                       help='Skip PRP generation (analysis only)')
    parser.add_argument('--limit', type=int, default=1,
                       help='Maximum number of todos to process')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze todos and show recommendations')
    parser.add_argument('--project-root', default='.',
                       help='Project root directory')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = TodoToPRPOrchestrator(
        project_root=Path(args.project_root),
        todos_file=Path(args.todos_file)
    )
    
    try:
        if args.analyze:
            # Analysis mode
            analysis = orchestrator.analyze_todos()
            print("\n=== Todo Analysis ===")
            print(f"Total todos: {analysis['total_todos']}")
            print(f"Ready for processing: {analysis['ready_for_processing']}")
            
            print("\nBy Priority:")
            for priority, count in analysis['by_priority'].items():
                print(f"  {priority}: {count}")
            
            print("\nBy Status:")
            for status, count in analysis['by_status'].items():
                print(f"  {status}: {count}")
            
            if analysis['next_recommended']:
                next_rec = analysis['next_recommended']
                print(f"\nNext Recommended: {next_rec['id']} - {next_rec['title']}")
                print(f"  Priority: {next_rec['priority']}")
                print(f"  Domains: {', '.join(next_rec['domains'])}")
            
            print("\nTop Domains:")
            sorted_domains = sorted(analysis['domain_distribution'].items(), 
                                  key=lambda x: x[1], reverse=True)
            for domain, count in sorted_domains[:5]:
                print(f"  {domain}: {count}")
        
        else:
            # Processing mode
            results = orchestrator.orchestrate_todo_to_prp(
                todo_id=args.todo_id,
                priority=args.priority,
                select_next=args.select_next,
                generate_prp=not args.no_generate,
                limit=args.limit
            )
            
            # Print results
            print("\n=== Processing Results ===")
            for result in results:
                status = "✅ Success" if result['success'] else "❌ Failed"
                print(f"{result['todo_id']}: {status}")
                
                if result['success']:
                    print(f"  Template: {result['template_selected']}")
                    if result['prp_generated']:
                        print(f"  PRP: {result['prp_path']}")
                    if result['agent_recommendations']:
                        print(f"  Agents: {', '.join(result['agent_recommendations'])}")
                    print(f"  Time: {result['processing_time']:.2f}s")
                else:
                    print(f"  Error: {result.get('error', 'Unknown error')}")
    
    except KeyboardInterrupt:
        logger.info("Orchestration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
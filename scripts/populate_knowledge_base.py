import asyncio
import logging
from pathlib import Path
import json
from typing import List

from src.rag_system import RAGSystem
from src.models import KnowledgeDocument, DocumentType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBasePopulator:
    """Populate the knowledge base with sample learning content."""
    
    def __init__(self):
        self.rag_system = RAGSystem()
    
    async def populate_sample_data(self):
        """Populate the knowledge base with sample educational content."""
        logger.info("Starting knowledge base population...")
        
        await self.rag_system.initialize()
        
        # Sample documents for software development learning
        sample_documents = [
            {
                "id": "js-basics-1",
                "title": "JavaScript Fundamentals - Variables and Data Types",
                "content": """
                JavaScript is a dynamically typed language where variables can store different types of data.
                
                Variable Declaration:
                - let: Block-scoped, can be reassigned
                - const: Block-scoped, cannot be reassigned
                - var: Function-scoped (avoid in modern code)
                
                Data Types:
                - Primitive: string, number, boolean, undefined, null, symbol, bigint
                - Objects: arrays, functions, objects
                
                Example:
                let name = "John";
                const age = 25;
                let isStudent = true;
                
                Best Practices:
                - Use const by default, let when reassignment needed
                - Avoid var in modern JavaScript
                - Use descriptive variable names
                """,
                "source": "MDN Web Docs",
                "document_type": "documentation",
                "metadata": {
                    "difficulty": "beginner",
                    "topics": ["javascript", "variables", "data-types"],
                    "estimated_time": "30 minutes",
                    "prerequisites": ["basic programming concepts"]
                }
            },
            {
                "id": "react-components-1",
                "title": "React Components - Functional vs Class Components",
                "content": """
                React components are the building blocks of React applications. There are two main types:
                
                Functional Components (Recommended):
                - Simpler syntax
                - Use React Hooks for state and lifecycle
                - Better performance
                - Easier to test and debug
                
                Example:
                function Welcome(props) {
                  return <h1>Hello, {props.name}!</h1>;
                }
                
                Class Components (Legacy):
                - More verbose syntax
                - Use this.state and lifecycle methods
                - Still supported but not recommended for new code
                
                Example:
                class Welcome extends React.Component {
                  render() {
                    return <h1>Hello, {this.props.name}!</h1>;
                  }
                }
                
                Best Practices:
                - Use functional components with hooks
                - Keep components small and focused
                - Use prop-types or TypeScript for type checking
                """,
                "source": "React Official Documentation",
                "document_type": "documentation",
                "metadata": {
                    "difficulty": "intermediate",
                    "topics": ["react", "components", "jsx"],
                    "estimated_time": "45 minutes",
                    "prerequisites": ["javascript", "html", "css"]
                }
            },
            {
                "id": "nodejs-intro-1",
                "title": "Node.js Introduction - Server-side JavaScript",
                "content": """
                Node.js is a JavaScript runtime built on Chrome's V8 engine that allows you to run JavaScript on the server.
                
                Key Features:
                - Asynchronous and event-driven
                - Single-threaded with event loop
                - Fast execution with V8 engine
                - Large ecosystem (npm)
                
                Common Use Cases:
                - Web servers and APIs
                - Real-time applications
                - Command-line tools
                - Microservices
                
                Basic HTTP Server:
                const http = require('http');
                
                const server = http.createServer((req, res) => {
                  res.writeHead(200, {'Content-Type': 'text/plain'});
                  res.end('Hello World!');
                });
                
                server.listen(3000, () => {
                  console.log('Server running on port 3000');
                });
                
                Package Management:
                - npm (Node Package Manager)
                - package.json for dependency management
                - npm install for package installation
                """,
                "source": "Node.js Official Docs",
                "document_type": "documentation",
                "metadata": {
                    "difficulty": "intermediate",
                    "topics": ["nodejs", "backend", "server"],
                    "estimated_time": "60 minutes",
                    "prerequisites": ["javascript", "basic networking"]
                }
            },
            {
                "id": "git-basics-1",
                "title": "Git Version Control - Essential Commands",
                "content": """
                Git is a distributed version control system essential for modern software development.
                
                Basic Workflow:
                1. Initialize repository: git init
                2. Add files: git add .
                3. Commit changes: git commit -m "message"
                4. Push to remote: git push origin main
                
                Essential Commands:
                - git status: Check working directory status
                - git log: View commit history
                - git branch: Manage branches
                - git merge: Combine branches
                - git pull: Fetch and merge remote changes
                
                Branching Strategy:
                - main/master: Production-ready code
                - develop: Integration branch
                - feature/: Individual features
                - hotfix/: Emergency fixes
                
                Best Practices:
                - Write clear commit messages
                - Commit frequently, push regularly
                - Use branches for features
                - Review code before merging
                """,
                "source": "Git Documentation",
                "document_type": "documentation",
                "metadata": {
                    "difficulty": "beginner",
                    "topics": ["git", "version-control", "collaboration"],
                    "estimated_time": "90 minutes",
                    "prerequisites": ["command line basics"]
                }
            },
            {
                "id": "python-web-django-1",
                "title": "Django Web Framework - Building Web Applications",
                "content": """
                Django is a high-level Python web framework that encourages rapid development and clean design.
                
                Key Features:
                - Model-View-Template (MVT) architecture
                - Object-Relational Mapping (ORM)
                - Admin interface
                - Security features built-in
                - Scalable and maintainable
                
                Project Structure:
                - Models: Define data structure
                - Views: Handle business logic
                - Templates: Present data to users
                - URLs: Route requests
                
                Basic Model Example:
                from django.db import models
                
                class Post(models.Model):
                    title = models.CharField(max_length=200)
                    content = models.TextField()
                    created_at = models.DateTimeField(auto_now_add=True)
                
                Basic View Example:
                from django.shortcuts import render
                from .models import Post
                
                def post_list(request):
                    posts = Post.objects.all()
                    return render(request, 'blog/post_list.html', {'posts': posts})
                
                Getting Started:
                1. Install Django: pip install django
                2. Create project: django-admin startproject myproject
                3. Create app: python manage.py startapp myapp
                4. Run server: python manage.py runserver
                """,
                "source": "Django Documentation",
                "document_type": "documentation",
                "metadata": {
                    "difficulty": "intermediate",
                    "topics": ["python", "django", "web-development", "backend"],
                    "estimated_time": "120 minutes",
                    "prerequisites": ["python", "html", "css", "sql"]
                }
            },
            {
                "id": "css-flexbox-1",
                "title": "CSS Flexbox - Modern Layout System",
                "content": """
                Flexbox is a one-dimensional layout method for arranging items in rows or columns.
                
                Container Properties (display: flex):
                - flex-direction: row | column | row-reverse | column-reverse
                - justify-content: flex-start | center | flex-end | space-between | space-around
                - align-items: stretch | flex-start | center | flex-end
                - flex-wrap: nowrap | wrap | wrap-reverse
                
                Item Properties:
                - flex-grow: How much item should grow
                - flex-shrink: How much item should shrink
                - flex-basis: Initial size before growing/shrinking
                - align-self: Override align-items for individual item
                
                Common Patterns:
                
                Centering:
                .container {
                  display: flex;
                  justify-content: center;
                  align-items: center;
                }
                
                Equal Height Columns:
                .container {
                  display: flex;
                }
                .item {
                  flex: 1;
                }
                
                Responsive Navigation:
                .nav {
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                }
                
                Best Practices:
                - Use flexbox for component-level layouts
                - Combine with CSS Grid for page layouts
                - Test on different screen sizes
                """,
                "source": "CSS-Tricks",
                "document_type": "tutorial",
                "metadata": {
                    "difficulty": "intermediate",
                    "topics": ["css", "flexbox", "layout", "responsive"],
                    "estimated_time": "75 minutes",
                    "prerequisites": ["html", "css basics"]
                }
            }
        ]
        
        # Convert to KnowledgeDocument objects
        documents = []
        for doc_data in sample_documents:
            doc = KnowledgeDocument(
                id=doc_data["id"],
                title=doc_data["title"],
                content=doc_data["content"],
                source=doc_data["source"],
                document_type=DocumentType(doc_data["document_type"]),
                metadata=doc_data["metadata"]
            )
            documents.append(doc)
        
        # Add documents to knowledge base
        success_count = await self.rag_system.add_documents_batch(documents)
        logger.info(f"Successfully added {success_count}/{len(documents)} documents to knowledge base")
        
        # Get final stats
        stats = await self.rag_system.get_collection_stats()
        logger.info(f"Knowledge base stats: {stats}")
        
        return success_count

async def main():
    """Main function to populate knowledge base."""
    populator = KnowledgeBasePopulator()
    await populator.populate_sample_data()

if __name__ == "__main__":
    asyncio.run(main())
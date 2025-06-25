# DevMarket - Software Marketplace Platform

## Overview

DevMarket is a comprehensive collaborative coding platform built with Flask, designed to facilitate team-based software development, project management, and developer collaboration. The platform features user authentication via Replit Auth, team management, project collaboration, real-time code editing, payment processing with Stripe, messaging systems, and administrative controls. Originally built as a marketplace, it has evolved into a full collaborative development environment supporting teams, projects, repositories, and real-time coding sessions.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with PostgreSQL backend
- **Authentication**: Replit Auth integration with OAuth2 flow
- **Payment Processing**: Stripe integration for secure transactions
- **File Handling**: Pillow for image processing and optimization
- **Form Validation**: WTForms with Flask-WTF for CSRF protection

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask
- **CSS Framework**: Bootstrap 5 with dark theme
- **JavaScript**: Vanilla JS with Bootstrap components
- **Icons**: Font Awesome
- **Image Handling**: Lazy loading and responsive design

### Database Design
- **Users**: Core user management with buyer/seller roles
- **Products**: Complete product catalog with categories, pricing, and metadata
- **Reviews**: Rating and review system for products and sellers
- **Messages**: Internal messaging system between users
- **Purchases**: Transaction tracking and order management
- **OAuth**: Required table for Replit Auth integration

## Key Components

### Authentication System
- Replit Auth integration for seamless user onboarding
- Role-based access control (buyer, seller, admin, team roles)
- Session management with Flask-Login
- User profile management with editable fields

### Team Collaboration System
- Team creation and management with role-based permissions
- Public and private team visibility options
- Team member management with different access levels
- Team-based project organization

### Project Management
- Collaborative project creation and management
- Project requirements and goal definition
- Milestone tracking with payment integration
- Priority-based project organization
- Public project discovery and contribution

### Real-time Collaborative Coding
- Multi-user code editing environment with Monaco Editor
- File and repository management within projects
- Version control integration with commit tracking
- Live chat during coding sessions
- Session-based collaboration with participant management
- Real-time code synchronization between participants

### Community Forum System
- Category-based discussion forums
- Topic creation with code snippet support
- Reply system with nested comments
- Voting system for topics and replies
- Search and filtering capabilities
- Solution marking for problem-solving

### Code Module Library
- Shareable code modules and snippets
- Language-specific categorization
- Download and import functionality
- Public module discovery
- Tagging and search system
- Usage analytics and popularity tracking

### Repository Management
- Project-based repository organization
- File management with syntax highlighting
- Language-specific file handling
- Public, private, and team-only repository visibility

### Payment System
- Stripe integration for secure payment processing
- Milestone-based payment distribution
- Contributor compensation tracking
- Multiple payment models (hourly, fixed, equity)
- Transaction tracking and management

### Messaging System
- Private messaging between users
- Team communication channels
- Project-specific discussions
- Real-time chat in collaboration sessions
- Notification system for project updates

### Search and Discovery
- Team and project discovery
- Advanced filtering by status, priority, language
- Public project browsing
- Team member search and recruitment

## Data Flow

### User Registration/Login
1. User authenticates via Replit Auth
2. OAuth token stored in database
3. User profile created/updated
4. Session established with Flask-Login

### Product Purchase Flow
1. User browses products
2. Adds product to cart (checkout)
3. Stripe checkout session created
4. Payment processed securely
5. Purchase record created
6. Success/failure handling

### Product Creation Flow
1. Seller creates product listing
2. Form validation and file upload processing
3. Images optimized and stored
4. Product saved to database
5. Admin approval workflow (if enabled)

## External Dependencies

### Core Framework Dependencies
- Flask: Web application framework
- SQLAlchemy: Database ORM
- Gunicorn: WSGI HTTP server for production

### Authentication & Security
- Flask-Login: User session management
- Flask-Dance: OAuth integration
- PyJWT: JSON Web Token handling
- Werkzeug: WSGI utilities and security

### Payment Processing
- Stripe: Payment processing API

### File Processing
- Pillow: Image processing and optimization

### Form Handling
- WTForms: Form validation and rendering
- Flask-WTF: CSRF protection and file uploads

### Database
- psycopg2-binary: PostgreSQL adapter

## Deployment Strategy

### Production Configuration
- **Server**: Gunicorn WSGI server
- **Binding**: 0.0.0.0:5000 for container compatibility
- **Auto-scaling**: Configured for Replit autoscale deployment
- **Environment Variables**: Session secrets and database URLs
- **File Uploads**: Local storage with optimization

### Development Setup
- **Debug Mode**: Enabled for development
- **Hot Reload**: Gunicorn with --reload flag
- **Port Configuration**: Automatic port detection

### Static Assets
- **CSS/JS**: Served via Flask static files
- **Images**: Upload directory with .gitkeep
- **CDN Integration**: Bootstrap and Font Awesome via CDN

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- June 25, 2025: Initial marketplace setup with basic product management
- June 25, 2025: Major evolution into collaborative coding platform
  - Added comprehensive team management system
  - Implemented project-based collaboration features
  - Created real-time collaborative code editor
  - Added repository and file management
  - Integrated milestone tracking and payment distribution
  - Built notification system for project updates
  - Enhanced dashboard for collaborative workflow
- June 25, 2025: Fixed critical 500 server errors
  - Resolved duplicate route definitions and circular imports
  - Fixed database relationship backref collisions
  - Added missing Jinja2 filters and template files
  - Implemented proper User.full_name() method
  - Added missing route handlers (edit_team, edit_product, etc.)
  - Created comprehensive error handling for templates
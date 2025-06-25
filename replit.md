# DevMarket - Software Marketplace Platform

## Overview

DevMarket is a comprehensive software marketplace platform built with Flask, designed to facilitate the buying and selling of software products, applications, and code libraries between developers. The platform features user authentication via Replit Auth, product management, payment processing with Stripe, messaging systems, and administrative controls.

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
- Role-based access control (buyer, seller, admin)
- Session management with Flask-Login
- User profile management with editable fields

### Product Management
- Complete product lifecycle (create, read, update, delete)
- Category-based organization
- Image upload with automatic optimization
- Programming language and framework tagging
- Demo URLs and documentation links
- Version control and licensing information

### Payment System
- Stripe integration for secure payment processing
- Checkout flow with order summaries
- Transaction tracking and receipt generation
- Success/cancel page handling

### Messaging System
- Private messaging between users
- Conversation threading
- Product-specific inquiries
- Unread message tracking

### Search and Discovery
- Advanced product filtering
- Category-based browsing
- Programming language filtering
- Price range selection
- Search functionality

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
- June 25, 2025. Initial setup
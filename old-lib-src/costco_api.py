#!/usr/bin/env python3
"""
Costco Database REST API

Flask API providing read-only access to the Costco scraping database with Swagger documentation.
Serves data from the SQL database through RESTful endpoints.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import Flask, jsonify, request, abort
from flask_restx import Api, Resource, fields, Namespace
from werkzeug.exceptions import NotFound, BadRequest

from costco_database import CostcoDatabase
from costco_service import CostcoService


# Initialize Flask app
app = Flask(__name__)
app.config['RESTX_MASK_SWAGGER'] = False  # Disable field masking for cleaner docs

# Initialize Flask-RESTX API with Swagger documentation
api = Api(
    app,
    version='1.0',
    title='Costco Database API',
    description='Read-only REST API for accessing Costco scraping data',
    doc='/docs/',  # Swagger UI available at /docs/
    contact='costco-scraper@example.com',
    license='MIT',
    license_url='https://opensource.org/licenses/MIT'
)

# Initialize database connection
db = CostcoDatabase()
service = CostcoService()

# API Namespaces
sessions_ns = Namespace('sessions', description='Scraping sessions operations')
categories_ns = Namespace('categories', description='Categories operations')
products_ns = Namespace('products', description='Products operations')
stats_ns = Namespace('stats', description='Statistics and analytics')
system_ns = Namespace('system', description='System operations')

api.add_namespace(sessions_ns, path='/api/v1/sessions')
api.add_namespace(categories_ns, path='/api/v1/categories')
api.add_namespace(products_ns, path='/api/v1/products')
api.add_namespace(stats_ns, path='/api/v1/stats')
api.add_namespace(system_ns, path='/api/v1/system')

# Swagger Models
session_model = api.model('Session', {
    'session_id': fields.String(required=True, description='Unique session identifier'),
    'start_time': fields.String(description='Session start timestamp'),
    'end_time': fields.String(description='Session end timestamp'),
    'status': fields.String(description='Session status', enum=['running', 'completed', 'failed']),
    'ai_enabled': fields.Boolean(description='Whether AI extraction was enabled'),
    'categories_found': fields.Integer(description='Number of categories found'),
    'products_found': fields.Integer(description='Number of products found'),
    'leaf_categories': fields.Integer(description='Number of leaf categories'),
    'navigation_categories': fields.Integer(description='Number of navigation categories'),
    'avg_product_price': fields.Float(description='Average product price'),
    'min_product_price': fields.Float(description='Minimum product price'),
    'max_product_price': fields.Float(description='Maximum product price')
})

category_model = api.model('Category', {
    'id': fields.Integer(required=True, description='Category ID'),
    'session_id': fields.String(required=True, description='Session ID'),
    'name': fields.String(required=True, description='Category name'),
    'url': fields.String(description='Category URL'),
    'category_type': fields.String(description='Category type', enum=[
        'leaf_product', 'leaf_service', 'leaf_location', 
        'non_leaf_navigation', 'non_leaf_hub', 'unknown'
    ]),
    'description': fields.String(description='Category description'),
    'parent_category_id': fields.Integer(description='Parent category ID'),
    'is_leaf': fields.Boolean(description='Whether this is a leaf category'),
    'level': fields.Integer(description='Hierarchy level'),
    'path': fields.String(description='Full category path'),
    'scraped_at': fields.String(description='When category was scraped')
})

product_model = api.model('Product', {
    'id': fields.Integer(required=True, description='Product ID'),
    'session_id': fields.String(required=True, description='Session ID'),
    'name': fields.String(required=True, description='Product name'),
    'item_number': fields.String(description='Costco item number'),
    'price': fields.Float(description='Current price'),
    'original_price': fields.Float(description='Original price (if on sale)'),
    'currency': fields.String(description='Price currency', default='CAD'),
    'description': fields.String(description='Product description'),
    'brand': fields.String(description='Product brand'),
    'model': fields.String(description='Product model'),
    'availability': fields.String(description='Product availability'),
    'rating': fields.Float(description='Product rating (1.0-5.0)'),
    'review_count': fields.Integer(description='Number of reviews'),
    'image_url': fields.String(description='Product image URL'),
    'product_url': fields.String(description='Product page URL'),
    'warehouse_only': fields.Boolean(description='Available in warehouse only'),
    'online_only': fields.Boolean(description='Available online only'),
    'member_exclusive': fields.Boolean(description='Member exclusive product'),
    'scraped_at': fields.String(description='When product was scraped')
})

category_hierarchy_model = api.model('CategoryHierarchy', {
    'id': fields.Integer(required=True, description='Category ID'),
    'name': fields.String(required=True, description='Category name'),
    'level': fields.Integer(description='Hierarchy level'),
    'path': fields.String(description='Full category path'),
    'category_type': fields.String(description='Category type'),
    'is_leaf': fields.Boolean(description='Whether this is a leaf category'),
    'children': fields.List(fields.Nested(lambda: category_hierarchy_model), description='Child categories')
})

database_stats_model = api.model('DatabaseStats', {
    'total_sessions': fields.Integer(description='Total number of sessions'),
    'total_categories': fields.Integer(description='Total number of categories'),
    'total_products': fields.Integer(description='Total number of products'),
    'database_size_bytes': fields.Integer(description='Database size in bytes'),
    'recent_sessions': fields.List(fields.Nested(session_model), description='Recent sessions')
})

search_result_model = api.model('SearchResult', {
    'total_results': fields.Integer(description='Total number of results'),
    'results': fields.List(fields.Nested(product_model), description='Search results')
})

# Error handling
@api.errorhandler(NotFound)
def handle_not_found(error):
    return {'message': 'Resource not found'}, 404

@api.errorhandler(BadRequest)
def handle_bad_request(error):
    return {'message': 'Bad request'}, 400

@api.errorhandler(Exception)
def handle_generic_error(error):
    return {'message': 'Internal server error'}, 500

# Sessions Endpoints
@sessions_ns.route('')
class SessionsList(Resource):
    @sessions_ns.doc('list_sessions')
    @sessions_ns.marshal_list_with(session_model)
    @sessions_ns.param('limit', 'Maximum number of sessions to return', type=int, default=10)
    @sessions_ns.param('status', 'Filter by session status', type=str, enum=['running', 'completed', 'failed'])
    def get(self):
        """Get list of scraping sessions"""
        limit = request.args.get('limit', 10, type=int)
        status = request.args.get('status')
        
        sessions = db.get_recent_sessions(limit)
        
        if status:
            sessions = [s for s in sessions if s.get('status') == status]
        
        return sessions

@sessions_ns.route('/<string:session_id>')
class Session(Resource):
    @sessions_ns.doc('get_session')
    @sessions_ns.marshal_with(session_model)
    def get(self, session_id):
        """Get specific session details"""
        stats = db.get_session_stats(session_id)
        if not stats:
            abort(404, description=f"Session {session_id} not found")
        return stats

@sessions_ns.route('/<string:session_id>/export')
class SessionExport(Resource):
    @sessions_ns.doc('export_session')
    def get(self, session_id):
        """Export complete session data"""
        try:
            data = service.get_session_data(session_id)
            if not data:
                abort(404, description=f"Session {session_id} not found")
            return data
        except Exception as e:
            abort(400, description=str(e))

# Categories Endpoints
@categories_ns.route('')
class CategoriesList(Resource):
    @categories_ns.doc('list_categories')
    @categories_ns.marshal_list_with(category_model)
    @categories_ns.param('session_id', 'Filter by session ID', type=str)
    @categories_ns.param('category_type', 'Filter by category type', type=str)
    @categories_ns.param('is_leaf', 'Filter by leaf status', type=bool)
    @categories_ns.param('parent_id', 'Filter by parent category ID', type=int)
    def get(self):
        """Get list of categories"""
        session_id = request.args.get('session_id')
        category_type = request.args.get('category_type')
        is_leaf = request.args.get('is_leaf', type=bool)
        parent_id = request.args.get('parent_id', type=int)
        
        if not session_id:
            # Get latest session if none specified
            recent_sessions = db.get_recent_sessions(1)
            if not recent_sessions:
                return []
            session_id = recent_sessions[0]['session_id']
        
        categories = db.get_categories(session_id, parent_id)
        
        # Apply filters
        if category_type:
            categories = [c for c in categories if c.get('category_type') == category_type]
        
        if is_leaf is not None:
            categories = [c for c in categories if c.get('is_leaf') == is_leaf]
        
        return categories

@categories_ns.route('/<int:category_id>')
class Category(Resource):
    @categories_ns.doc('get_category')
    @categories_ns.marshal_with(category_model)
    def get(self, category_id):
        """Get specific category details"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            category = cursor.fetchone()
            
            if not category:
                abort(404, description=f"Category {category_id} not found")
            
            return dict(category)

@categories_ns.route('/<int:category_id>/products')
class CategoryProducts(Resource):
    @categories_ns.doc('get_category_products')
    @categories_ns.marshal_list_with(product_model)
    def get(self, category_id):
        """Get products in a specific category"""
        products = db.get_products_by_category(category_id)
        return products

@categories_ns.route('/hierarchy')
class CategoriesHierarchy(Resource):
    @categories_ns.doc('get_category_hierarchy')
    @categories_ns.param('session_id', 'Session ID (uses latest if not specified)', type=str)
    def get(self):
        """Get category hierarchy tree"""
        session_id = request.args.get('session_id')
        
        if not session_id:
            recent_sessions = db.get_recent_sessions(1)
            if not recent_sessions:
                return []
            session_id = recent_sessions[0]['session_id']
        
        hierarchy = db.get_category_hierarchy(session_id)
        
        # Build tree structure
        def build_tree(categories, parent_id=None, level=0):
            tree = []
            for cat in categories:
                if cat['level'] == level and (
                    (parent_id is None and cat.get('parent_category_id') is None) or
                    cat.get('parent_category_id') == parent_id
                ):
                    cat_dict = dict(cat)
                    cat_dict['children'] = build_tree(categories, cat['id'], level + 1)
                    tree.append(cat_dict)
            return tree
        
        return build_tree(hierarchy)

# Products Endpoints
@products_ns.route('')
class ProductsList(Resource):
    @products_ns.doc('list_products')
    @products_ns.marshal_list_with(product_model)
    @products_ns.param('session_id', 'Filter by session ID', type=str)
    @products_ns.param('brand', 'Filter by brand', type=str)
    @products_ns.param('min_price', 'Minimum price filter', type=float)
    @products_ns.param('max_price', 'Maximum price filter', type=float)
    @products_ns.param('availability', 'Filter by availability', type=str)
    @products_ns.param('limit', 'Maximum number of products to return', type=int, default=50)
    def get(self):
        """Get list of products with optional filters"""
        session_id = request.args.get('session_id')
        brand = request.args.get('brand')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        availability = request.args.get('availability')
        limit = request.args.get('limit', 50, type=int)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with filters
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            if brand:
                query += " AND brand LIKE ?"
                params.append(f"%{brand}%")
            
            if min_price is not None:
                query += " AND price >= ?"
                params.append(min_price)
            
            if max_price is not None:
                query += " AND price <= ?"
                params.append(max_price)
            
            if availability:
                query += " AND availability = ?"
                params.append(availability)
            
            query += " ORDER BY name LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            products = [dict(row) for row in cursor.fetchall()]
            
            return products

@products_ns.route('/<int:product_id>')
class Product(Resource):
    @products_ns.doc('get_product')
    @products_ns.marshal_with(product_model)
    def get(self, product_id):
        """Get specific product details"""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            
            if not product:
                abort(404, description=f"Product {product_id} not found")
            
            return dict(product)

@products_ns.route('/search')
class ProductsSearch(Resource):
    @products_ns.doc('search_products')
    @products_ns.marshal_with(search_result_model)
    @products_ns.param('q', 'Search query', type=str, required=True)
    @products_ns.param('session_id', 'Session ID to search within', type=str)
    @products_ns.param('limit', 'Maximum number of results', type=int, default=50)
    def get(self):
        """Search products by name, brand, or description"""
        query = request.args.get('q')
        session_id = request.args.get('session_id')
        limit = request.args.get('limit', 50, type=int)
        
        if not query:
            abort(400, description="Search query parameter 'q' is required")
        
        if not session_id:
            # Use latest session if none specified
            recent_sessions = db.get_recent_sessions(1)
            if recent_sessions:
                session_id = recent_sessions[0]['session_id']
            else:
                return {'total_results': 0, 'results': []}
        
        results = db.search_products(session_id, query, limit)
        
        return {
            'total_results': len(results),
            'results': results
        }

# Statistics Endpoints
@stats_ns.route('/database')
class DatabaseStats(Resource):
    @stats_ns.doc('get_database_stats')
    @stats_ns.marshal_with(database_stats_model)
    def get(self):
        """Get overall database statistics"""
        stats = service.get_database_stats()
        return stats

@stats_ns.route('/sessions/<string:session_id>')
class SessionStats(Resource):
    @stats_ns.doc('get_session_stats')
    @stats_ns.marshal_with(session_model)
    def get(self, session_id):
        """Get detailed statistics for a specific session"""
        stats = db.get_session_stats(session_id)
        if not stats:
            abort(404, description=f"Session {session_id} not found")
        return stats

@stats_ns.route('/categories')
class CategoryStats(Resource):
    @stats_ns.doc('get_category_stats')
    @stats_ns.param('session_id', 'Session ID (uses latest if not specified)', type=str)
    def get(self):
        """Get category statistics and counts"""
        session_id = request.args.get('session_id')
        
        if not session_id:
            recent_sessions = db.get_recent_sessions(1)
            if not recent_sessions:
                return {}
            session_id = recent_sessions[0]['session_id']
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Category type distribution
            cursor.execute("""
                SELECT category_type, COUNT(*) as count
                FROM categories 
                WHERE session_id = ?
                GROUP BY category_type
            """, (session_id,))
            
            type_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Leaf vs non-leaf
            cursor.execute("""
                SELECT is_leaf, COUNT(*) as count
                FROM categories 
                WHERE session_id = ?
                GROUP BY is_leaf
            """, (session_id,))
            
            leaf_distribution = {
                'leaf_categories': 0,
                'navigation_categories': 0
            }
            
            for is_leaf, count in cursor.fetchall():
                if is_leaf:
                    leaf_distribution['leaf_categories'] = count
                else:
                    leaf_distribution['navigation_categories'] = count
            
            # Category levels
            cursor.execute("""
                SELECT level, COUNT(*) as count
                FROM categories 
                WHERE session_id = ?
                GROUP BY level
                ORDER BY level
            """, (session_id,))
            
            level_distribution = {f"level_{row[0]}": row[1] for row in cursor.fetchall()}
            
            return {
                'session_id': session_id,
                'type_distribution': type_distribution,
                'leaf_distribution': leaf_distribution,
                'level_distribution': level_distribution
            }

@stats_ns.route('/products')
class ProductStats(Resource):
    @stats_ns.doc('get_product_stats')
    @stats_ns.param('session_id', 'Session ID (uses latest if not specified)', type=str)
    def get(self):
        """Get product statistics and pricing information"""
        session_id = request.args.get('session_id')
        
        if not session_id:
            recent_sessions = db.get_recent_sessions(1)
            if not recent_sessions:
                return {}
            session_id = recent_sessions[0]['session_id']
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Price statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_products,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as products_with_price
                FROM products 
                WHERE session_id = ?
            """, (session_id,))
            
            price_stats = dict(cursor.fetchone())
            
            # Brand distribution (top 10)
            cursor.execute("""
                SELECT brand, COUNT(*) as count
                FROM products 
                WHERE session_id = ? AND brand IS NOT NULL
                GROUP BY brand
                ORDER BY count DESC
                LIMIT 10
            """, (session_id,))
            
            brand_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Availability distribution
            cursor.execute("""
                SELECT availability, COUNT(*) as count
                FROM products 
                WHERE session_id = ? AND availability IS NOT NULL
                GROUP BY availability
            """, (session_id,))
            
            availability_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                'session_id': session_id,
                'price_statistics': price_stats,
                'top_brands': brand_distribution,
                'availability_distribution': availability_distribution
            }

# Health check endpoint
@system_ns.route('/health')
class Health(Resource):
    @system_ns.doc('health_check')
    def get(self):
        """API health check"""
        try:
            # Test database connection
            stats = service.get_database_stats()
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'total_sessions': stats.get('total_sessions', 0)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }, 500

# Root endpoint
@system_ns.route('/info')
class Root(Resource):
    @system_ns.doc('api_info')
    def get(self):
        """API information and available endpoints"""
        return {
            'name': 'Costco Database API',
            'version': '1.0',
            'description': 'Read-only REST API for accessing Costco scraping data',
            'endpoints': {
                'documentation': '/docs/',
                'health': '/api/v1/system/health',
                'sessions': '/api/v1/sessions',
                'categories': '/api/v1/categories',
                'products': '/api/v1/products',
                'statistics': '/api/v1/stats'
            }
        }

# Add simple health route for easy testing
@app.route('/health')
def simple_health():
    """Simple health check route"""
    try:
        stats = service.get_database_stats()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'total_sessions': stats.get('total_sessions', 0)
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/')
def api_root():
    """Root API information"""
    return jsonify({
        'name': 'Costco Database API',
        'version': '1.0',
        'description': 'Read-only REST API for accessing Costco scraping data',
        'documentation': '/docs/',
        'health': '/health',
        'endpoints': {
            'sessions': '/api/v1/sessions',
            'categories': '/api/v1/categories',
            'products': '/api/v1/products',
            'statistics': '/api/v1/stats',
            'system': '/api/v1/system'
        }
    })

if __name__ == '__main__':
    # Development server
    port = 5001
    print("🚀 Starting Costco Database API...")
    print(f"📚 Swagger documentation available at: http://localhost:{port}/docs/")
    print(f"🏥 Health check available at: http://localhost:{port}/health")
    
    app.run(debug=True, host='0.0.0.0', port=port)

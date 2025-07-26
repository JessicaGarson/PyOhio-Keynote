import os
import json
from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import numpy as np

app = Flask(__name__)

# Initialize Elasticsearch client
def get_elasticsearch_client():
    """Initialize and return Elasticsearch client using environment variables"""
    es_host = os.getenv('ELASTICSEARCH_HOST')
    es_api_key = os.getenv('ELASTICSEARCH_API_KEY')
    
    if not es_host or not es_api_key:
        raise ValueError("ELASTICSEARCH_HOST and ELASTICSEARCH_API_KEY environment variables must be set")
    
    return Elasticsearch(
        [es_host],
        api_key=es_api_key,
        verify_certs=True
    )

# Initialize sentence transformer model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Sample PyOhio-related data
SAMPLE_DATA = [
    {
        "id": "1",
        "title": "Introduction to Python Web Development",
        "content": "Learn how to build modern web applications using Flask and Django frameworks. This session covers routing, templates, and database integration.",
        "speaker": "Sarah Johnson",
        "track": "Web Development"
    },
    {
        "id": "2", 
        "title": "Machine Learning with scikit-learn",
        "content": "Explore machine learning fundamentals using scikit-learn. Topics include classification, regression, and model evaluation techniques.",
        "speaker": "Mike Chen",
        "track": "Data Science"
    },
    {
        "id": "3",
        "title": "Python Performance Optimization",
        "content": "Discover techniques to optimize Python code performance. Learn about profiling, caching, and using Cython for speed improvements.",
        "speaker": "Alex Rodriguez",
        "track": "Performance"
    },
    {
        "id": "4",
        "title": "Building APIs with FastAPI",
        "content": "Create high-performance APIs using FastAPI. This talk covers automatic documentation, type hints, and async programming.",
        "speaker": "Emily Davis",
        "track": "Web Development"
    },
    {
        "id": "5",
        "title": "Data Visualization with Matplotlib and Seaborn",
        "content": "Master data visualization techniques using Python's most popular plotting libraries. Learn to create compelling charts and graphs.",
        "speaker": "David Kim",
        "track": "Data Science"
    }
]

def create_index_mapping():
    """Create Elasticsearch index with proper mapping for vector search"""
    return {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "speaker": {"type": "keyword"},
                "track": {"type": "keyword"},
                "content_vector": {
                    "type": "dense_vector",
                    "dims": 384,  # all-MiniLM-L6-v2 produces 384-dimensional vectors
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }

def setup_elasticsearch():
    """Set up Elasticsearch index and populate with sample data"""
    try:
        es = get_elasticsearch_client()
        index_name = "pyohio_talks"
        
        # Delete index if it exists
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
        
        # Create index with mapping
        es.indices.create(index=index_name, body=create_index_mapping())
        
        # Index sample data with embeddings
        for talk in SAMPLE_DATA:
            # Create embedding for the content
            content_text = f"{talk['title']} {talk['content']}"
            embedding = model.encode(content_text).tolist()
            
            # Add embedding to document
            doc = talk.copy()
            doc['content_vector'] = embedding
            
            es.index(index=index_name, id=talk['id'], body=doc)
        
        # Refresh index to make documents searchable
        es.indices.refresh(index=index_name)
        
        return True, "Elasticsearch setup completed successfully"
    except Exception as e:
        return False, f"Elasticsearch setup failed: {str(e)}"

@app.route('/')
def hello_pyohio():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def vector_search():
    """Perform vector search on PyOhio talks"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        es = get_elasticsearch_client()
        
        # Create embedding for the search query
        query_embedding = model.encode(query).tolist()
        
        # Perform vector search
        search_body = {
            "knn": {
                "field": "content_vector",
                "query_vector": query_embedding,
                "k": 5,
                "num_candidates": 10
            },
            "_source": ["title", "content", "speaker", "track"]
        }
        
        response = es.search(index="pyohio_talks", body=search_body)
        
        # Format results
        results = []
        for hit in response['hits']['hits']:
            result = hit['_source']
            result['score'] = hit['_score']
            results.append(result)
        
        return jsonify({
            "query": query,
            "results": results,
            "total": len(results)
        })
        
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

@app.route('/setup', methods=['POST'])
def setup_index():
    """Endpoint to set up Elasticsearch index"""
    success, message = setup_elasticsearch()
    return jsonify({"success": success, "message": message})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        es = get_elasticsearch_client()
        es.ping()
        return jsonify({"status": "healthy", "elasticsearch": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

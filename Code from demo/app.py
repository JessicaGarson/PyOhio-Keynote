from flask import Flask, render_template, request, jsonify
import os
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import json

app = Flask(__name__)

# Initialize Elasticsearch client
def get_elasticsearch_client():
    host = os.getenv('ELASTICSEARCH_HOST')
    api_key = os.getenv('ELASTICSEARCH_API_KEY')
    
    if not host or not api_key:
        raise ValueError("ELASTICSEARCH_HOST and ELASTICSEARCH_API_KEY environment variables must be set")
    
    return Elasticsearch(
        hosts=[host],
        api_key=api_key,
        verify_certs=True
    )

# Initialize sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Sample PyOhio conference data
SAMPLE_TALKS = [
    {
        "id": "talk_1",
        "title": "Building Modern Web Applications with Flask and React",
        "speaker": "Sarah Johnson",
        "track": "Web Development",
        "content": "Learn how to create scalable web applications using Flask as a backend API and React for the frontend. We'll cover authentication, database integration, and deployment strategies."
    },
    {
        "id": "talk_2",
        "title": "Machine Learning with Python: From Data to Insights",
        "speaker": "Dr. Michael Chen",
        "track": "Data Science",
        "content": "Explore the complete machine learning pipeline using Python libraries like pandas, scikit-learn, and TensorFlow. Learn data preprocessing, model training, and evaluation techniques."
    },
    {
        "id": "talk_3",
        "title": "Python Performance Optimization: Making Your Code Faster",
        "speaker": "Alex Rodriguez",
        "track": "Performance",
        "content": "Discover techniques to optimize Python code performance including profiling, caching, async programming, and using Cython for critical sections."
    },
    {
        "id": "talk_4",
        "title": "Building RESTful APIs with FastAPI",
        "speaker": "Emily Davis",
        "track": "Web Development",
        "content": "FastAPI is a modern, fast web framework for building APIs with Python. Learn about automatic documentation, type hints, and async support."
    },
    {
        "id": "talk_5",
        "title": "Data Visualization with Python: Beyond Basic Charts",
        "speaker": "James Wilson",
        "track": "Data Science",
        "content": "Create compelling data visualizations using matplotlib, seaborn, and plotly. Learn about interactive dashboards and advanced plotting techniques."
    }
]

@app.route('/')
def hello_pyohio():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Check Elasticsearch connection health"""
    try:
        es = get_elasticsearch_client()
        health = es.cluster.health()
        return jsonify({
            'status': 'healthy',
            'elasticsearch': health['status']
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/setup', methods=['POST'])
def setup_index():
    """Initialize Elasticsearch index with sample data"""
    try:
        es = get_elasticsearch_client()
        index_name = 'pyohio_talks'
        
        # Create index with mapping
        mapping = {
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "speaker": {"type": "text"},
                    "track": {"type": "keyword"},
                    "content": {"type": "text"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "similarity": "cosine"
                    }
                }
            }
        }
        
        # Delete index if it exists
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
        
        # Create new index
        es.indices.create(index=index_name, body=mapping)
        
        # Index sample talks with embeddings
        for talk in SAMPLE_TALKS:
            # Create embedding from title + content
            text_to_embed = f"{talk['title']} {talk['content']}"
            embedding = model.encode(text_to_embed).tolist()
            
            doc = {
                **talk,
                "embedding": embedding
            }
            
            es.index(index=index_name, id=talk['id'], body=doc)
        
        # Refresh index
        es.indices.refresh(index=index_name)
        
        return jsonify({
            'status': 'success',
            'message': f'Indexed {len(SAMPLE_TALKS)} talks successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/search', methods=['POST'])
def search_talks():
    """Perform vector search on PyOhio talks"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        es = get_elasticsearch_client()
        index_name = 'pyohio_talks'
        
        # Generate embedding for the query
        query_embedding = model.encode(query).tolist()
        
        # Perform kNN search
        search_body = {
            "knn": {
                "field": "embedding",
                "query_vector": query_embedding,
                "k": 5,
                "num_candidates": 10
            },
            "_source": ["title", "speaker", "track", "content"]
        }
        
        response = es.search(index=index_name, body=search_body)
        
        results = []
        for hit in response['hits']['hits']:
            results.append({
                'id': hit['_id'],
                'score': hit['_score'],
                'title': hit['_source']['title'],
                'speaker': hit['_source']['speaker'],
                'track': hit['_source']['track'],
                'content': hit['_source']['content']
            })
        
        return jsonify({
            'status': 'success',
            'query': query,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

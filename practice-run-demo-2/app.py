from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
import json
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Elasticsearch
es_host = os.environ.get('ELASTICSEARCH_HOST')
es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')

# Initialize Elasticsearch client
es = Elasticsearch(
    es_host.strip(),
    api_key=es_api_key
)

# Sample data for Elasticsearch (will be used if index doesn't exist)
sample_data = [
    {"title": "Python in Ohio", "content": "Python is widely used in Ohio for web development, data science, and automation.", "tags": ["python", "ohio", "programming"]},
    {"title": "Flask Web Framework", "content": "Flask is a lightweight WSGI web application framework in Python.", "tags": ["python", "flask", "web"]},
    {"title": "Elasticsearch Basics", "content": "Elasticsearch is a distributed, RESTful search and analytics engine.", "tags": ["elasticsearch", "search", "database"]},
    {"title": "PyOhio Conference", "content": "PyOhio is a free annual Python conference in Ohio.", "tags": ["python", "conference", "ohio"]},
    {"title": "Data Visualization", "content": "Python offers great libraries like Matplotlib and Seaborn for data visualization.", "tags": ["python", "data", "visualization"]},
    {"title": "Web Development", "content": "Python is excellent for web development with frameworks like Flask and Django.", "tags": ["python", "web", "development"]},
    {"title": "Machine Learning", "content": "Python is the leading language for machine learning and AI development.", "tags": ["python", "machine learning", "AI"]},
    {"title": "Ohio Tech Scene", "content": "Ohio has a growing tech scene with many Python opportunities.", "tags": ["ohio", "tech", "jobs"]}
]

# Index name
INDEX_NAME = "pyohio_demo"

def setup_elasticsearch():
    """Set up Elasticsearch index if it doesn't exist"""
    try:
        # Check if index exists
        if not es.indices.exists(index=INDEX_NAME):
            # Create index
            es.indices.create(
                index=INDEX_NAME,
                mappings={
                    "properties": {
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "tags": {"type": "keyword"}
                    }
                }
            )
            
            # Add sample data
            for i, doc in enumerate(sample_data):
                es.index(index=INDEX_NAME, id=i+1, document=doc)
            
            print(f"Created index {INDEX_NAME} with sample data")
        return True
    except Exception as e:
        print(f"Error setting up Elasticsearch: {e}")
        return False

# Set up Elasticsearch on startup
es_available = setup_elasticsearch()

@app.route('/')
def hello():
    current_date = datetime.now().strftime("%B %d, %Y")
    return render_template('index.html', 
                          current_date=current_date,
                          es_available=es_available)

@app.route('/search', methods=['POST'])
def search():
    if not es_available:
        return jsonify({"error": "Elasticsearch is not available"}), 503
    
    query = request.form.get('query', '')
    
    try:
        # Search in both title and content
        response = es.search(
            index=INDEX_NAME,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content", "tags^1.5"]  # Boost title and tags
                }
            },
            highlight={
                "fields": {
                    "title": {},
                    "content": {}
                }
            }
        )
        
        # Process results
        hits = response['hits']['hits']
        results = []
        
        for hit in hits:
            result = {
                "id": hit["_id"],
                "score": hit["_score"],
                "title": hit["_source"]["title"],
                "content": hit["_source"]["content"],
                "tags": hit["_source"]["tags"]
            }
            
            # Add highlights if available
            if "highlight" in hit:
                result["highlights"] = hit["highlight"]
            
            results.append(result)
        
        # Get tag statistics
        tag_stats = {}
        for hit in hits:
            for tag in hit["_source"]["tags"]:
                if tag in tag_stats:
                    tag_stats[tag] += 1
                else:
                    tag_stats[tag] = 1
        
        return jsonify({
            "results": results,
            "tag_stats": tag_stats,
            "total": len(results)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

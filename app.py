from flask import Flask, render_template, request, jsonify
import sqlite3
import numpy as np
import arxiv
import argparse
from datetime import datetime, timedelta
import pytz
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
import google.generativeai as genai
import os


app = Flask(__name__)

# Initialize the Gemini API client
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

logreg = LinearSVC(class_weight='balanced', C=0.01)
scaler = StandardScaler()

# Add this near the top of the file, after imports
parser = argparse.ArgumentParser(description='Run the Flask app with paper date filtering.')
parser.add_argument('--days', type=int, default=None, help='Number of days to filter papers')
args = parser.parse_args()

def get_db_connection():
    conn = sqlite3.connect('papers.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_recent_papers(max_results=100):
    client = arxiv.Client()
    categories = ['cs.LG', 'stat.ML', 'cs.AI', 'cs.CL', 'cs.IR']
    
    query = f"cat:{' OR cat:'.join(categories)}"
    
    search = arxiv.Search(
        query=query,
        sort_by=arxiv.SortCriterion.LastUpdatedDate,
        sort_order=arxiv.SortOrder.Descending,
        max_results=max_results
    )

    all_results = []
    try:
        for result in client.results(search):
            # Add date filtering here
            if args.days is not None:
                cutoff_date = datetime.now(pytz.UTC) - timedelta(days=args.days)
                if result.updated < cutoff_date:
                    continue
            all_results.append(result)
    except arxiv.UnexpectedEmptyPageError:
        pass

    # Get saved paper IDs from the database
    conn = get_db_connection()
    saved_paper_ids = set(row['id'] for row in conn.execute('SELECT id FROM saved_papers').fetchall())
    conn.close()
    
    print("Finished retrieving papers")
    # Filter out papers that are already in the database
    filtered_results = [paper for paper in all_results if paper.entry_id not in saved_paper_ids]
    
    print(f"Retrieved {len(all_results)} papers, {len(filtered_results)} are new")
    
    return filtered_results


def get_saved_papers():
    conn = get_db_connection()
    papers = conn.execute('SELECT * FROM saved_papers').fetchall()
    conn.close()
    return papers

def encode_papers(papers, is_arxiv=True):
    print("Start encoding")
    encoded_papers = []
    batch_size = 500  # Adjust this based on your needs and API limits

    for i in range(0, len(papers), batch_size):
        batch = papers[i:i+batch_size]
        texts = []
        for paper in batch:
            if is_arxiv:
                text = paper.title + ' ' + paper.summary
            else:
                text = paper['title'] + ' ' + paper['abstract']
            texts.append(text)
        
        # Use Gemini API for batch embeddings
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=texts,
            task_type="CLASSIFICATION",
        )
        # The result contains a single 'embedding' key with a list of embeddings
        embeddings = result['embedding']
        
        for paper, embedding in zip(batch, embeddings):
            encoded_papers.append((paper, embedding))
    
    print("Finished encoding")
    return encoded_papers

def train_model(encoded_recent_papers):
    print("Start training")
    saved_papers = get_saved_papers()
    if not saved_papers:
        return False

    # Prepare data for training
    X = []
    y = []

    encoded_saved_papers = encode_papers(saved_papers, is_arxiv=False)

    for _, embedding in encoded_saved_papers:
        X.append(embedding)
        y.append(1)

    for _, embedding in encoded_recent_papers:
        X.append(embedding)
        y.append(0)

    X = np.array(X)
    y = np.array(y)

    # Scale features
    X_scaled = scaler.fit_transform(X)

    # Train the model
    logreg.fit(X_scaled, y)
    print("Finished training")
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/papers')
def get_papers():
    all_results = get_recent_papers(max_results=500)
    encoded_papers = encode_papers(all_results)
    
    train_model(encoded_papers)
    
    def serialize_paper(paper, embedding):
        scaled_embedding = scaler.transform([embedding])
        score = logreg.decision_function(scaled_embedding)[0]
        
        return {
            'id': paper.entry_id,
            'title': paper.title,
            'abstract': paper.summary,
            'published': paper.updated.isoformat(),
            'score': float(score)
        }
    
    #print("wololo")
    serialized_papers = [serialize_paper(paper, embedding) for paper, embedding in encoded_papers]
    sorted_papers = sorted(serialized_papers, key=lambda x: x['score'], reverse=True)
    
    return jsonify(sorted_papers[:100])



@app.route('/save_paper', methods=['POST'])
def save_paper():
    data = request.json
    paper_id = data['paper_id']
    
    # Fetch the paper from arXiv API
    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(client.results(search))
    except StopIteration:
        return jsonify({'success': False, 'message': 'Paper not found'}), 404

    # Serialize the paper data
    serialized_paper = {
        'id': paper.entry_id,
        'title': paper.title,
        'abstract': paper.summary,
        'updated': paper.updated.isoformat(),
        'url': paper.pdf_url,
    }

    # Insert the paper into the database
    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO saved_papers 
        (id, title, abstract, updated, url) 
        VALUES (?, ?, ?, ?, ?)
    ''', (
        serialized_paper['id'],
        serialized_paper['title'],
        serialized_paper['abstract'],
        serialized_paper['updated'],
        serialized_paper['url'],
    ))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'paper': serialized_paper})


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_papers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            abstract TEXT,
            updated TEXT,
            url TEXT
        )
    """)
    
    # Check if the database is empty
    cursor = conn.execute("SELECT COUNT(*) FROM saved_papers")
    count = cursor.fetchone()[0]

    if count == 0:
        # Add seed paper if database is empty
        try:
            client = arxiv.Client()
            search = arxiv.Search(id_list=['1603.02754'])  # Add seed paper ID
            seed_paper = next(client.results(search))

            conn.execute('''
                INSERT INTO saved_papers (id, title, abstract, updated, url)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                seed_paper.entry_id,
                seed_paper.title,
                seed_paper.summary,
                seed_paper.updated.isoformat(),
                seed_paper.pdf_url
            ))

            print("Added seed paper 1603.02754 to the database.")

        except Exception as e:
            print(f"Error adding seed paper: {e}")


    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    #train_model()  # Train the model on startup
    app.run(debug=True)



import pandas as pd
import ollama
import os
import re
from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS




app = Flask(__name__, template_folder='template', static_folder='static')
CORS(app)

@app.route("/")
def home():
    return render_template("temp.html")  # Corrected path

# Load CSV files
folder_path = 'OllamaModel'
all_tables = []

for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)
        df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')

        if 'category' not in df.columns:
            inferred_category = os.path.splitext(filename)[0].lower().rstrip('s')
            df['category'] = inferred_category

        df['category'] = df['category'].str.strip().str.lower()
        df['name'] = df['name'].astype(str).str.strip().str.lower()
        df['description'] = df['description'].astype(str).str.strip().str.lower()
        all_tables.append(df)

df = pd.concat(all_tables, ignore_index=True)

def build_markdown_table(filtered_df):
    rows = ["| Name | Description | Price | Category |", "|------|-------------|--------|----------|"]
    for _, row in filtered_df.iterrows():
        name = row.get('name', 'Unnamed').title()
        desc = row.get('description', 'No description').capitalize()
        price = row.get('price', 'N/A')
        category = row.get('category', 'N/A').title()
        rows.append(f"| {name} | {desc} | ${price} | {category} |")
    return "\n".join(rows)

def filter_df_by_keywords(df, question):
    question = question.lower()
    keywords = re.findall(r'\b\w+\b', question)
    filtered = df[df.apply(lambda row: any(
        kw in row['name'] or kw in row['description'] or kw in row['category']
        for kw in keywords
    ), axis=1)]
    return filtered

system_prompt = """
You are a helpful assistant at a fast food restaurant called MacDonalds.

Your job is to help customers find menu items based strictly on the data provided.

The menu is structured with the following columns:
- Name
- Description
- Price
- Category

Customers may ask for:
- A specific item by name
- Items under a certain price
- Items from a specific category (like 'Drinks', 'Main Dish', etc.)

When responding:
- Only use items from the dataset
- Always format your response as a Markdown table with columns: Name, Description, Price, and Category
- If no matches are found, respond politely and ask if they'd like help finding something else

NEVER make up items, prices, or descriptions.
"""


@app.route("/ask", methods=['POST'])
def ask():
    try:
        data = request.get_json(force=True)
        question = data.get("question", "")
        if not question:
            return jsonify({"response": "No question provided."}), 400

        filtered_items = filter_df_by_keywords(df, question)
        context_table = build_markdown_table(filtered_items) if not filtered_items.empty else "No matching items found."

        full_prompt = f"""{system_prompt}

{context_table}

Now answer this question:
{question}
"""

        response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': full_prompt}])

        if not response or 'message' not in response or 'content' not in response['message']:
            return jsonify({"response": "Model returned an unexpected response."}), 500

        return jsonify({"response": response['message']['content']})

    except Exception as e:
        return jsonify({"response": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':

    port = os.getenv('PORT', 5000)
    
    app.run(host='0.0.0.0', port=port, debug=True)

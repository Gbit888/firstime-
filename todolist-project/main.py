from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from openai import OpenAI

app = Flask(__name__)

# File to store todos
TODOS_FILE = 'todos.json'

# Inizializza OpenAI client
client = OpenAI(api_key=os.getenv('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'))


def load_todos():
    if os.path.exists(TODOS_FILE):
        with open(TODOS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_todos(todos):
    with open(TODOS_FILE, 'w') as f:
        json.dump(todos, f, indent=2)


@app.route('/')
def index():
    todos = load_todos()
    return render_template('index.html', todos=todos)


@app.route('/add', methods=['POST'])
def add_todo():
    todo_text = request.form.get('todo')
    if todo_text:
        todos = load_todos()
        new_todo = {
            'id': len(todos) + 1,
            'text': todo_text,
            'note': '',
            'completed': False
        }
        todos.append(new_todo)
        save_todos(todos)
    return redirect(url_for('index'))


@app.route('/update_note/<int:todo_id>', methods=['POST'])
def update_note(todo_id):
    note_text = request.form.get('note', '')
    todos = load_todos()
    for todo in todos:
        if todo['id'] == todo_id:
            todo['note'] = note_text
            break
    save_todos(todos)
    return redirect(url_for('index'))


@app.route('/toggle/<int:todo_id>')
def toggle_todo(todo_id):
    todos = load_todos()
    for todo in todos:
        if todo['id'] == todo_id:
            todo['completed'] = not todo['completed']
            break
    save_todos(todos)
    return redirect(url_for('index'))


@app.route('/delete/<int:todo_id>')
def delete_todo(todo_id):
    todos = load_todos()
    todos = [todo for todo in todos if todo['id'] != todo_id]
    save_todos(todos)
    return redirect(url_for('index'))


@app.route('/chat', methods=['POST'])
def chat():
    try:
        if request.json:
            user_message = request.json.get('message', '')
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid Content-Type. Expected application/json'
            }), 400
        todos = load_todos()
        
        # Prepara il contesto per l'AI
        total_todos = len(todos)
        completed_todos = len([t for t in todos if t['completed']])
        pending_todos = total_todos - completed_todos
        
        todo_list = "\n".join([f"- {todo['text']} ({'✓ completata' if todo['completed'] else '⏳ da fare'})" 
                              for todo in todos])
        
        system_prompt = f"""Sei un assistente AI personale per una TodoList. 
        
Stato attuale dell'utente:
- Attività totali: {total_todos}
- Completate: {completed_todos}
- Da fare: {pending_todos}

Lista attività:
{todo_list if todo_list else "Nessuna attività presente"}

Rispondi in italiano in modo amichevole e utile. Puoi:
- Ricordare attività pendenti
- Dare consigli di produttività
- Motivare l'utente
- Suggerire come organizzare il lavoro
- Rispondere a domande sulle attività

Sii conciso ma utile. Usa emoji quando appropriato."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return jsonify({
            'success': True,
            'response': response.choices[0].message.content
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)

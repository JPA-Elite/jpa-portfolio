from flask import Flask, render_template, request, redirect # type: ignore
import json

app = Flask(__name__)

# Load existing projects from the JSON file
def load_projects():
    try:
        with open('data.json', 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {"projects": []}
    return data

# Save projects to the JSON file
def save_projects(data):
    with open('data.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

# Route to display the project list and form
@app.route('/')
def index():
    data = load_projects()  # Load project data from JSON file
    return render_template('index.html', projects=data['projects'])  # Render HTML with project data

# Route to handle form submission and add a new project
@app.route('/add_project', methods=['POST'])
def add_project():
    # Get the data submitted from the form
    name = request.form['name']
    status = request.form['status']
    description = request.form['description']
    
    # Load current projects and append the new project
    data = load_projects()
    new_project = {
        "name": name,
        "status": status,
        "description": description
    }
    data['projects'].append(new_project)  # Add the new project to the list
    
    # Save updated data back to the JSON file
    save_projects(data)
    
    # Redirect back to the main page to display updated project list
    return redirect('/')

# Route to display the project list and form
@app.route('/profile')
def profile():
    data = load_projects()  # Load project data from JSON file
    return render_template('profile.html')  # Render HTML with project data

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

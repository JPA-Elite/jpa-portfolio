from flask import Flask, render_template, url_for, redirect # type: ignore
import json
from config import PROFILE_IMAGE, RESUME_PDF, GALLERY_JSON_PATH, IMAGE_PATH

app = Flask(__name__)

@app.route('/')
def index():
    # Redirect to the '/profile' route
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    # Use the profile_image and resume_pdf in this route
    return render_template('profile.html', profile_image=PROFILE_IMAGE, resume_pdf=RESUME_PDF)

@app.route('/gallery')
def gallery():
    # Load the gallery data from JSON using the config constant
    with open(GALLERY_JSON_PATH) as f:
        gallery_data = json.load(f)
    return render_template('gallery.html', gallery_data=gallery_data, image_path=IMAGE_PATH)

# Custom error handler for 404 Not Found
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

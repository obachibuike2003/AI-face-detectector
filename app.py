from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
import cv2
import os
import uuid
import datetime
import sqlite3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning
load_dotenv()

# --- MTCNN Initialization ---
# Initialize detector to None initially
detector = None
mtcnn_available = False

try:
    from mtcnn import MTCNN
    detector = MTCNN()
    mtcnn_available = True
    print("MTCNN successfully initialized.")
except ImportError:
    print("ERROR: MTCNN not found. Please install it using: pip install mtcnn opencv-python tensorflow")
    print("Face detection will be disabled.")
except Exception as e:
    print(f"ERROR: Failed to initialize MTCNN: {e}")
    print("Face detection will be disabled.")

# If MTCNN is not available, create a dummy detector to prevent NameError
if not mtcnn_available:
    class DummyMTCNN:
        def detect_faces(self, img):
            print("Warning: MTCNN is not available. Returning 0 faces.")
            return []
    detector = DummyMTCNN()
# --- End MTCNN Initialization ---

# Define the absolute path to the directory where app.py resides
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the absolute path for the 'static' folder
STATIC_FOLDER_ABSOLUTE_PATH = os.path.join(BASE_DIR, 'static')

# Initialize Flask app, explicitly telling it where the static folder is
# This ensures Flask knows to look for static files in the 'static' directory
app = Flask(__name__, static_folder=STATIC_FOLDER_ABSOLUTE_PATH)
CORS(app) # Enable CORS for all origins, useful for development

# Retrieve SECRET_KEY from environment variables, essential for Flask session security
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key_for_dev_only')

# Define the absolute path for the 'uploads' subfolder within 'static'
UPLOADS_FOLDER_ABSOLUTE_PATH = os.path.join(STATIC_FOLDER_ABSOLUTE_PATH, 'uploads')

# Ensure the 'uploads' directory exists. If not, create it.
os.makedirs(UPLOADS_FOLDER_ABSOLUTE_PATH, exist_ok=True)

# Store the absolute path in app.config for use when saving files
app.config['UPLOAD_FOLDER'] = UPLOADS_FOLDER_ABSOLUTE_PATH

# Initialize SQLite DB
DB_NAME = os.getenv('DATABASE_NAME', 'attendance.db')

def get_db_connection():
    """
    Establishes and returns a new SQLite database connection.
    Configures row_factory to allow accessing columns by name.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name (e.g., row['column_name'])
    return conn

# Create the attendance table if it doesn't exist
with get_db_connection() as conn:
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 timestamp TEXT,
                 faces INTEGER,
                 image_path TEXT)''') # image_path will store path relative to static folder
    conn.commit()

@app.route('/')
def index():
    """
    Renders the main HTML page for the application.
    """
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """
    Handles image uploads, performs face detection, saves results,
    and logs attendance. Returns JSON response.
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not file:
        return jsonify({"error": "File is empty"}), 400

    original_filepath_abs = None # Initialize for cleanup

    try:
        # Generate secure filenames for both original and processed images
        original_filename_secure = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        result_filename_secure = f"detected_{uuid.uuid4().hex}_{original_filename_secure}"

        # Construct absolute paths for saving files
        original_filepath_abs = os.path.join(app.config['UPLOAD_FOLDER'], original_filename_secure)
        result_filepath_abs = os.path.join(app.config['UPLOAD_FOLDER'], result_filename_secure)

        # Save the original uploaded file
        file.save(original_filepath_abs)
        app.logger.info(f"Original image saved to: {original_filepath_abs}") # Log save path

        # Read the image using OpenCV
        img = cv2.imread(original_filepath_abs)
        if img is None:
            os.remove(original_filepath_abs)
            return jsonify({"error": "Could not read image file. Invalid format or corrupt."}), 400

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        faces = []
        if mtcnn_available:
            faces = detector.detect_faces(img_rgb)
        else:
            app.logger.warning("MTCNN not available. Skipping face detection for this image.")

        num_faces = len(faces)

        for face in faces:
            x, y, w, h = face['box']
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Save the image with detected faces
        cv2.imwrite(result_filepath_abs, img)
        app.logger.info(f"Processed image saved to: {result_filepath_abs}") # Log save path

        # Construct URLs for the frontend using url_for('static', filename=...)
        # The filename argument must be relative to the 'static' folder.
        # Since images are in 'static/uploads', the relative path is 'uploads/filename'.
        original_image_url_for_frontend = url_for('static', filename=f'uploads/{original_filename_secure}')
        result_image_url_for_frontend = url_for('static', filename=f'uploads/{result_filename_secure}')

        # Log attendance data
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            c = conn.cursor()
            # Store the path relative to the static folder in the DB
            c.execute("INSERT INTO attendance (timestamp, faces, image_path) VALUES (?, ?, ?)",
                      (timestamp, num_faces, f"uploads/{result_filename_secure}"))
            conn.commit()

        return jsonify({
            "success": True,
            "result_image_url": result_image_url_for_frontend,
            "original_image_url": original_image_url_for_frontend,
            "faces_detected": num_faces,
            "timestamp": timestamp
        }), 200

    except Exception as e:
        app.logger.error(f"Error during image upload and processing: {e}", exc_info=True)
        # Clean up the original uploaded file if an error occurred after saving it
        if original_filepath_abs and os.path.exists(original_filepath_abs):
            os.remove(original_filepath_abs)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

@app.route('/attendance', methods=['GET'])
def get_attendance():
    """
    Retrieves all attendance logs from the database and returns them as JSON.
    """
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT timestamp, faces, image_path FROM attendance ORDER BY timestamp DESC")
            logs = c.fetchall()
            logs_list = []
            for row in logs:
                log_dict = dict(row)
                if log_dict['image_path']:
                    # Generate the full URL for the image using url_for('static', ...)
                    log_dict['image_url'] = url_for('static', filename=log_dict['image_path'])
                else:
                    log_dict['image_url'] = None # Or a placeholder URL
                logs_list.append(log_dict)
        return jsonify(logs_list), 200
    except Exception as e:
        app.logger.error(f"Error fetching attendance logs: {e}", exc_info=True)
        return jsonify({"error": f"Failed to retrieve attendance logs: {str(e)}"}), 500

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))

    app.run(debug=debug_mode, host=host, port=port)

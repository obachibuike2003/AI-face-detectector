

# 🧠 Face Detection Attendance Logger

A Flask web application that allows users to upload images, detects faces using the MTCNN deep learning model, and logs attendance with time, face count, and image references.

---

## 🚀 Features

✅ Upload images and detect faces
✅ Draw bounding boxes around detected faces using OpenCV
✅ Save both original and processed images
✅ Store attendance logs (timestamp, face count, image) in SQLite
✅ Serve images from `/static/uploads/...`
✅ REST API for frontend to fetch logs and upload images
✅ MTCNN detection with fallback (dummy) when unavailable
✅ CORS enabled for frontend integration

---

## 📁 Folder Structure

```
project/
├── static/
│   └── uploads/               # Processed and original uploaded images
├── templates/
│   └── index.html             # Frontend interface (upload form)
├── app.py                     # Main Flask backend
├── .env                       # Configuration file
├── attendance.db              # SQLite database
└── README.md
```

---

## ⚙️ Requirements

* Python 3.7+
* pip (Python package manager)

### 🧪 Dependencies

Install with:

```bash
pip install -r requirements.txt
```

**`requirements.txt`**:

```
flask
flask-cors
opencv-python
mtcnn
tensorflow
python-dotenv
```

---

## 🛠 Setup Instructions

1. **Clone the repository**:

```bash
git clone https://github.com/yourusername/face-attendance-logger.git
cd face-attendance-logger
```

2. **Create `.env` file**:

```env
FLASK_ENV=development
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
SECRET_KEY=your_super_secret_key
DATABASE_NAME=attendance.db
```

3. **Run the app**:

```bash
python app.py
```

4. **Visit in browser**:

```
http://localhost:5000
```

---

## 📷 How It Works

* Go to the homepage.
* Upload an image with one or more faces.
* The app detects faces, saves the result, and logs the data to SQLite.
* You get:

  * Number of faces
  * Original and processed image
  * Timestamp

---

## 📡 API Endpoints

### `POST /upload`

Uploads an image and returns face detection results.

**Form Data**:

* `image`: JPEG/PNG image

**Response**:

```json
{
  "success": true,
  "faces_detected": 3,
  "timestamp": "2025-07-16 21:23:45",
  "original_image_url": "/static/uploads/xxx.jpg",
  "result_image_url": "/static/uploads/detected_xxx.jpg"
}
```

---

### `GET /attendance`

Returns JSON list of past detection logs.

**Response**:

```json
[
  {
    "timestamp": "2025-07-16 21:23:45",
    "faces": 3,
    "image_path": "uploads/detected_xxx.jpg",
    "image_url": "/static/uploads/detected_xxx.jpg"
  },
  ...
]
```

---

## ⚠️ Known Issues

* `favicon.ico` 404 can be ignored or patched.
* MTCNN may be slow on CPU-only machines.
* Ensure uploaded images are valid JPEG/PNG formats.

---

## 📌 To-Do

* [ ] Add login/authentication
* [ ] Build React frontend
* [ ] Export attendance to Excel/CSV
* [ ] Add face recognition (not just detection)
* [ ] Deploy on Render/VPS

---

## 👤 Author

**Chibuike** – [GitHub](https://github.com/obachibuike2003)

---

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).


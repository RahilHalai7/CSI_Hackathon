# CSI Hackathon Platform

A comprehensive web application for managing business idea submissions, mentor feedback, and administrative oversight for the CSI Hackathon.

## Features

### For Entrepreneurs
- **File Upload**: Upload PDF documents or audio files for business idea processing
- **AI Processing**: Automatic text extraction and Business Model Canvas generation
- **Submission Management**: View past submissions and their processing status
- **Feedback Viewing**: Receive and view mentor feedback on submissions

### For Mentors
- **Entrepreneur Management**: View assigned entrepreneurs
- **Submission Review**: Review and provide feedback on entrepreneur submissions
- **Feedback System**: Rate and provide detailed feedback with suggestions

### For Admins
- **User Management**: Approve mentor applications and manage user accounts
- **Mentor Assignments**: Assign mentors to entrepreneurs
- **Progress Tracking**: Monitor overall platform activity and statistics
- **System Oversight**: View all submissions and feedback across the platform

## Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLite**: Database for user management and data storage
- **Google Cloud APIs**: Speech-to-Text and Vision for file processing
- **Gemini AI**: Business Model Canvas generation
- **PyMuPDF**: PDF text extraction
- **Pydub**: Audio processing

### Frontend
- **React**: Modern JavaScript framework
- **Tailwind CSS**: Utility-first CSS framework
- **React Router**: Client-side routing
- **Axios**: HTTP client for API communication
- **React Dropzone**: File upload handling
- **Lucide React**: Icon library

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud credentials for Speech-to-Text and Vision APIs
- Gemini API key

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CSI_Hackathon
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. **Initialize database**
   The database will be automatically created when you run the application.

6. **Run the backend**
   ```bash
   python app.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## Usage

### Getting Started

1. **Create an Admin Account**
   - Register with role "admin"
   - All users are automatically approved upon registration

2. **Mentor Registration**
   - Mentors can register and start using the platform immediately
   - They can be assigned to entrepreneurs by the admin

3. **Entrepreneur Registration**
   - Entrepreneurs can register and start submitting files immediately
   - They will be assigned a mentor by the admin

### File Processing

The system supports two types of file uploads:

1. **PDF Documents**: Text extraction using PyMuPDF and OCR via Google Vision API
2. **Audio Files**: Speech-to-text conversion using Google Cloud Speech-to-Text

Both types are processed to generate Business Model Canvas data using Gemini AI.

## API Endpoints

### Authentication
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `GET /api/me` - Get current user info

### Admin Endpoints
- `GET /api/admin/pending-mentors` - Get pending mentor approvals
- `POST /api/admin/approve-mentor/<id>` - Approve a mentor
- `POST /api/admin/assign-mentor` - Assign mentor to entrepreneur
- `GET /api/admin/users` - Get all users
- `GET /api/admin/submissions` - Get all submissions

### Mentor Endpoints
- `GET /api/mentor/entrepreneurs` - Get assigned entrepreneurs
- `GET /api/mentor/submissions` - Get submissions from assigned entrepreneurs
- `POST /api/mentor/feedback` - Submit feedback

### Entrepreneur Endpoints
- `GET /api/entrepreneur/mentor` - Get assigned mentor
- `GET /api/entrepreneur/submissions` - Get own submissions
- `POST /api/entrepreneur/submit` - Submit file for processing

## Database Schema

The application uses SQLite with the following main tables:
- `users` - User accounts and roles
- `mentor_assignments` - Mentor-entrepreneur relationships
- `submissions` - File submissions and processing results
- `feedback` - Mentor feedback on submissions
- `processing_logs` - File processing history

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team or create an issue in the repository.
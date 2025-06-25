import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import hashlib

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_folder='static/uploads'):
    """Save uploaded file and return the relative path"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Optimize image if it's an image file
        try:
            optimize_image(file_path)
        except Exception as e:
            print(f"Failed to optimize image: {e}")
        
        return file_path
    return None

def optimize_image(file_path, max_size=(800, 600), quality=85):
    """Optimize image for web use"""
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized version
            img.save(file_path, optimize=True, quality=quality)
    except Exception as e:
        print(f"Error optimizing image {file_path}: {e}")

def generate_conversation_id(user1_id, user2_id):
    """Generate a consistent conversation ID for two users"""
    sorted_ids = sorted([str(user1_id), str(user2_id)])
    conversation_string = f"{sorted_ids[0]}_{sorted_ids[1]}"
    return hashlib.md5(conversation_string.encode()).hexdigest()

def format_price(amount, currency='USD'):
    """Format price for display"""
    if currency == 'USD':
        return f"${amount:.2f}"
    return f"{amount:.2f} {currency}"

def get_language_choices():
    """Get programming language choices for forms"""
    languages = [
        'Python', 'JavaScript', 'TypeScript', 'Java', 'C#', 'C++', 'C', 
        'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'Scala', 'R', 
        'MATLAB', 'SQL', 'HTML/CSS', 'Shell/Bash', 'PowerShell'
    ]
    return [('', 'All Languages')] + [(lang, lang) for lang in sorted(languages)]

def paginate_query(query, page, per_page=12):
    """Helper function for pagination"""
    return query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )

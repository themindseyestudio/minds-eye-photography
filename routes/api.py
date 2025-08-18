from flask import Blueprint, jsonify, request
from src.models.user import db, PortfolioImage, Category, FeaturedImage, BackgroundImage, ContactSubmission
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/portfolio')
def get_portfolio():
    """Get all portfolio images"""
    try:
        category_filter = request.args.get('category')
        
        query = PortfolioImage.query.filter_by(is_active=True)
        
        if category_filter and category_filter != 'all':
            category = Category.query.filter(Category.name.ilike(category_filter)).first()
            if category:
                query = query.filter(PortfolioImage.categories.contains(category))
        
        images = query.order_by(PortfolioImage.sort_order, PortfolioImage.created_at.desc()).all()
        
        return jsonify({
            'images': [image.to_dict() for image in images]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/categories')
def get_categories():
    """Get categories that have images assigned to them"""
    try:
        # Only get categories that have at least one image
        categories = db.session.query(Category).join(
            Category.images
        ).group_by(Category.id).order_by(Category.sort_order).all()
        
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/featured')
def get_featured():
    """Get current featured image"""
    try:
        featured = FeaturedImage.query.filter_by(is_active=True).first()
        
        if not featured:
            return jsonify({'featured': None})
        
        return jsonify({
            'featured': featured.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/background')
def get_background():
    """Get current background image"""
    try:
        background = BackgroundImage.query.filter_by(is_active=True).first()
        
        if not background:
            return jsonify({'background': None})
        
        return jsonify({
            'background': background.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_email(contact_data):
    """Send confirmation email to customer for their contact form submission"""
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "rick@themindseyestudio.com"
        sender_password = "njth maag lfjh bzok"  # App password
        recipient_email = contact_data['email']  # Send TO the customer
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Thank you for your photography inquiry - Mind's Eye Photography"
        
        # Create customer confirmation email body
        body = f"""
Dear {contact_data['name']},

Thank you for reaching out to Mind's Eye Photography! I've received your inquiry and I'm excited to learn more about your photography needs.

Here's a summary of what you submitted:

Project Details:
- Event Date: {contact_data.get('event_date', 'Not specified')}
- Photography Type: {contact_data.get('photography_type', 'Not specified')}
- Budget Range: {contact_data.get('budget_range', 'Not specified')}
- How you heard about us: {contact_data.get('how_heard', 'Not specified')}

Your Project Description:
{contact_data.get('project_description', 'No description provided')}

I will review your inquiry and get back to you within 24 hours to discuss your project in detail. In the meantime, feel free to browse my portfolio at themindseyestudio.com to see examples of my work.

If you have any urgent questions, you can reach me directly at:
📧 rick@themindseyestudio.com
📱 608-219-6066

Looking forward to potentially working together to capture your special moments!

Best regards,
Rick Corey
Mind's Eye Photography
"Where Moments Meet Imagination"

---
This is an automated confirmation email. Please do not reply to this message.
For direct communication, use rick@themindseyestudio.com
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False

@api_bp.route('/contact', methods=['POST'])
def submit_contact():
    """Submit contact form"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['name', 'email', 'project_description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Parse event_date if provided
        event_date = None
        if data.get('event_date'):
            try:
                event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
            except ValueError:
                pass
        
        contact = ContactSubmission(
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            event_date=event_date,
            photography_type=data.get('photography_type', ''),
            budget_range=data.get('budget_range', ''),
            project_description=data['project_description'],
            how_heard=data.get('how_heard', '')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        # Send email notification
        email_sent = send_email(data)
        
        if email_sent:
            return jsonify({
                'message': 'Contact form submitted successfully and email sent'
            })
        else:
            return jsonify({
                'message': 'Contact form submitted successfully but email notification failed'
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


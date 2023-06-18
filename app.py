from flask import Flask, render_template, redirect, request, session, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import cloudinary
import cloudinary.uploader


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tutaStore.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Add a secret key for session management
UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# password fnvekwjelbofdnee

cloudinary.config( 
  cloud_name = "dhdeg8ccz", 
  api_key = "993795536597183", 
  api_secret = "SDn7wJ82jMxD8tInc--NEMZaBdw" 
)

# Create the directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

product_category = db.Table('product_category',
                            db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
                            db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
                            )
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(100), nullable=True)  # Image file path
    description = db.Column(db.Text, nullable=True)  # Description field
    featured = db.Column(db.Boolean, default=False)  # New attribute for indicating if a product is featured
    categories = db.relationship('Category', secondary=product_category, backref=db.backref('products', lazy='dynamic'))
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)

    def __repr__(self):
        return self.name


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    image = db.Column(db.String(100), nullable=True) 

    def __repr__(self):
        return self.name

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    item = db.relationship('Product', backref='carts')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    telephone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')

    def __repr__(self):
        return self.username


class CartProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    # Additional columns and properties for the cart product
    
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='orders')
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')
    delivered = db.Column(db.Boolean, default=False)  # New attribute for marking order as delivered
    paid = db.Column(db.Boolean, default=False)  # New attribute for marking order as paid
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return self.name


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f"OrderItem(order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})"

class Brand(db.Model):
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(255))

    # Establish relationship with the Product model
    products = db.relationship('Product', backref='brand', lazy=True)
    
class Banner(db.Model):
    __tablename__ = 'banners'

    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False)
    subtitle = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(255), nullable=False)

    def __init__(self, image, subtitle, title, text):
        self.image = image
        self.subtitle = subtitle
        self.title = title
        self.text = text

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    products = Product.query.all()
    categories = Category.query.all()
    banners = Banner.query.all()
    featured_products = Product.query.filter_by(featured=True).all()
    return render_template('index.html', products=products, banners=banners, categories=categories, featured_products=featured_products)

@app.route('/products')
def products():
    all_products = Product.query.all()
    return render_template('products.html', products=all_products)
@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        featured = bool(request.form.get('featured'))

        # Handle image upload
        if 'image' in request.files:
            image = request.files['image']
            # Upload image to Cloudinary
            result = cloudinary.uploader.upload(image)
            image_url = result['secure_url']
        else:
            image_url = None

        # Retrieve selected categories
        selected_categories = request.form.getlist('categories')

        brand_id = request.form.get('brand')  # Retrieve the selected brand ID

        brand = Brand.query.get(brand_id)  # Get the brand object using the ID

        if brand:
            product = Product(name=name, price=price, image=image_url, description=description, featured=featured, brand_id=brand.id)

            # Add the product to the database
            db.session.add(product)
            db.session.commit()

            # Add the selected categories to the product
            for category_id in selected_categories:
                category = Category.query.get(category_id)
                if category:
                    product.categories.append(category)

            db.session.commit()
            flash('Product added successfully!', 'success')
        else:
            flash('Invalid brand selected!', 'error')

        return redirect('/')

    # Retrieve categories and brands from the database
    categories = Category.query.all()
    brands = Brand.query.all()

    return render_template('add_product.html', categories=categories, brands=brands)
@app.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']
        product.description = request.form['description']
        product.brand_id = request.form['brand_id']
        product.featured = 'featured' in request.form  # Check if "featured" checkbox is selected

        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                # Save the uploaded image to the designated directory
                filename = 'static/images/' + image.filename
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
                product.image = filename

        # Update the categories
        selected_categories = request.form.getlist('categories')
        product.categories = Category.query.filter(Category.id.in_(selected_categories)).all()

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect('/')

    brands = Brand.query.all()
    categories = Category.query.all()
    return render_template('edit_product.html', product=product, brands=brands, categories=categories)


@app.route('/delete-product/<int:product_id>', methods=['GET'])
def delete_product(product_id):
    # Retrieve the product from the database
    product = Product.query.get(product_id)
    
    if product:
        # Delete the product from the database
        db.session.delete(product)
        db.session.commit()
        
        flash('Product deleted successfully', 'success')
    else:
        flash('Product not found', 'error')
    
    return redirect(url_for('products'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        # User is already logged in, redirect to home page or any other page
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']
        city = request.form['city']
        telephone = request.form['telephone']
        role = 'user'  # Set the role as 'user' by default

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=generate_password_hash(password), address=address, city=city, telephone=telephone, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # User is already logged in, redirect to home page or any other page
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            if check_password_hash(user.password, password):
                session['user_id'] = user.id  # Save user ID in the session
                flash('Login successful', 'success')
                return redirect(url_for('home'))
            else:
                flash('Incorrect password', 'error')
        else:
            flash('User does not exist', 'error')

    return render_template('login.html')

@app.route('/add-to-cart/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Please login to add items to the cart', 'error')
        return redirect(url_for('login'))

    # Get the current user
    user_id = session['user_id']
    user = User.query.get(user_id)

    if user:
        # Check if the item is already in the cart
        cart_item = Cart.query.filter_by(user_id=user.id, item_id=product_id).first()

        if cart_item:
            # Item already exists in the cart, increment the quantity
            cart_item.quantity += 1
        else:
            # Item does not exist in the cart, create a new entry
            cart_item = Cart(user_id=user.id, item_id=product_id)

        db.session.add(cart_item)
        db.session.commit()

        flash('Item added to cart', 'success')
    else:
        flash('User not found', 'error')

    return redirect(url_for('home'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please login to view the cart', 'error')
        return redirect(url_for('login'))

    # Get the current user
    user = User.query.get(session['user_id'])

    if user is not None:
        # Get all products in the user's cart
        cart_items = Cart.query.filter_by(user_id=user.id).join(Cart.item).all()

        # Calculate total price
        total_price = sum(cart_item.item.price * cart_item.quantity for cart_item in cart_items)

        return render_template('cart.html', cart_items=cart_items, total_price=total_price)
    else:
        flash('User not found', 'error')
        return redirect(url_for('login'))


@app.route('/remove-from-cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    if 'user_id' not in session:
        flash('Please login to remove items from the cart', 'error')
        return redirect(url_for('login'))

    # Get the current user
    user = User.query.get(session['user_id'])

    # Get the cart item to be removed
    cart_item = Cart.query.filter_by(user_id=user.id, id=cart_item_id).first()

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart', 'success')
    else:
        flash('Item not found in the cart', 'error')

    return redirect(url_for('cart'))

@app.route('/update_quantity/<int:cart_item_id>', methods=['GET'])
def update_quantity(cart_item_id):
    if 'user_id' not in session:
        flash('Please login to update cart quantity', 'error')
        return redirect(url_for('login'))
    # Get the current user
    user = User.query.get(session['user_id'])

    # Get the cart item to be updated
    cart_item = Cart.query.filter_by(user_id=user.id, id=cart_item_id).first()

    if cart_item:
        new_quantity = int(request.args.get('quantity', cart_item.quantity))

        # Check if the new quantity is within valid range
        if new_quantity > 0:
            # Update the quantity of the cart item
            cart_item.quantity = new_quantity
            db.session.commit()
            flash('Quantity updated', 'success')
        else:
            flash('Quantity must be greater than 0', 'error')
    else:
        flash('Item not found in the cart', 'error')

    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login to proceed to checkout', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        city = request.form.get('city')
        address = request.form.get('address')
        telephone = request.form.get('telephone')

        if not name or not email or not city or not address or not telephone:
            flash('Please fill in all the required fields', 'error')
            return redirect(url_for('checkout'))

        user = User.query.get(session['user_id'])

        order = Order(name=name, email=email, city=city, address=address, telephone=telephone, user=user)
        db.session.add(order)
        db.session.commit()

        user_id = session['user_id']
        cart_items = Cart.query.filter_by(user_id=user_id).all()

        for cart_item in cart_items:
            order_item = OrderItem(order_id=order.id, product_id=cart_item.item_id, quantity=cart_item.quantity)
            db.session.add(order_item)

        db.session.commit()

        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        flash('Order placed successfully!', 'success')

        return redirect(url_for('home'))

    user_id = session['user_id']
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    total_price = sum(cart_item.item.price * cart_item.quantity for cart_item in cart_items)

    return render_template('checkout.html', cart_items=cart_items, total_price=total_price)


@app.route('/orders')
def orders():
    # Query all orders from the table
    all_orders = Order.query.all()

    # Calculate total price for each order
    for order in all_orders:
        total_price = sum(item.product.price * item.quantity for item in order.items)
        order.total_price = total_price
        order.timestamp_formatted = order.timestamp.strftime('%Y-%m-%d %H:%M:%S')


    return render_template('orders.html', orders=all_orders)


@app.route('/mark_paid/<int:order_id>', methods=['POST'])
def mark_paid(order_id):
    order = Order.query.get(order_id)
    if order:
        order.paid = True
        db.session.commit()
        flash('Order marked as paid.', 'success')
    else:
        flash('Order not found.', 'error')
    return redirect(url_for('orders'))

@app.route('/mark_delivered/<int:order_id>', methods=['POST'])
def mark_delivered(order_id):
    order = Order.query.get(order_id)
    if order:
        order.delivered = True
        db.session.commit()
        flash('Order marked as delivered.', 'success')
    else:
        flash('Order not found.', 'error')
    return redirect(url_for('orders'))


@app.route('/add-category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        # Handle image upload (if necessary)
        if 'image' in request.files:
            image = request.files['image']
            # Upload image to Cloudinary
            result = cloudinary.uploader.upload(image)
            image_url = result['secure_url']
        else:
            image_url = None
        category = Category(name=name, image=image_url)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('categories'))

    return render_template('add_category.html')
@app.route('/category/<int:category_id>')
def category_products(category_id):
    category = Category.query.get_or_404(category_id)
    products = category.products
    return render_template('category_products.html', category=category, products=products)

@app.route('/categories')
def categories():
    all_categories = Category.query.all()
    return render_template('categories.html', categories=all_categories)

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    if request.method == 'POST':
        # Handle the POST request logic here
        # ...
        pass

    product = Product.query.get_or_404(product_id)
    
    # Retrieve other products with the same categories
    other_products_categories = Product.query.filter(Product.categories.any(Category.id.in_([category.id for category in product.categories]))).filter(Product.id != product.id).limit(4).all()
    
    # Retrieve other products with the same brand
    other_products_brand = Product.query.filter_by(brand_id=product.brand_id).filter(Product.id != product.id).limit(4).all()
    
    image = product.image if product.image else None
    return render_template('product_details.html', product=product, image=image, other_products_categories=other_products_categories, other_products_brand=other_products_brand)


@app.route('/add_brand', methods=['GET', 'POST'])
def add_brand():
    if request.method == 'POST':
        brand_name = request.form['name']
        brand_image = request.files['image']

        # Upload image to Cloudinary
        result = cloudinary.uploader.upload(brand_image)
        brand_image_url = result['secure_url']

        new_brand = Brand(name=brand_name, image=brand_image_url)
        db.session.add(new_brand)
        db.session.commit()

        flash('Brand added successfully!', 'success')
        return redirect(url_for('brands'))
    else:
        return render_template('add_brand.html')


@app.route('/edit_brand/<int:brand_id>', methods=['GET', 'POST'])
def edit_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)

    if request.method == 'POST':
        brand_name = request.form['name']
        brand_image = request.files['image']

        # Save the uploaded image file to Cloudinary
        if brand_image:
            # Upload the image to Cloudinary
            upload_result = cloudinary.uploader.upload(brand_image)
            brand.image = upload_result['secure_url']

        brand.name = brand_name

        db.session.commit()
        flash('Brand updated successfully!', 'success')
        return redirect(url_for('brands'))

    return render_template('edit_brand.html', brand=brand)


@app.route('/brands')
def brands():
    # Retrieve all brands from the database
    brands = Brand.query.all()
    
    return render_template('brands.html', brands=brands)

@app.route('/delete_brand/<int:brand_id>', methods=['GET'])
def delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)

    # Delete the brand's image from Cloudinary (optional)
    if brand.image:
        cloudinary.uploader.destroy(brand.image, invalidate=True)

    db.session.delete(brand)
    db.session.commit()

    flash('Brand deleted successfully!', 'success')
    return redirect(url_for('brands'))


@app.route('/shop')
def shop():
    # Retrieve products from the database
    products = Product.query.all()

    # Sort products based on the selected sorting option
    sort = request.args.get('sort')
    if sort == 'bestselling':
        products = sorted(products, key=lambda x: get_sold_count(x), reverse=True)
    elif sort == 'pricelowtohigh':
        products = sorted(products, key=lambda x: x.price)
    elif sort == 'pricehightolow':
        products = sorted(products, key=lambda x: x.price, reverse=True)

    # Get featured products
    featured_products = Product.query.filter_by(featured=True).all()

    return render_template('shop.html', products=products, featured_products=featured_products)

def get_sold_count(product):
    # Calculate and return the total quantity sold for a product
    sold_count = 0
    for order_item in product.order_items:
        sold_count += order_item.quantity
    return sold_count


@app.route('/add_banner', methods=['GET', 'POST'])
def add_banner():
    if request.method == 'POST':
        banner_image = request.files['image']
        banner_subtitle = request.form['subtitle']
        banner_title = request.form['title']
        banner_text = request.form['text']

        # Upload image to Cloudinary
        result = cloudinary.uploader.upload(banner_image)
        banner_image_url = result['secure_url']

        new_banner = Banner(image=banner_image_url, subtitle=banner_subtitle, title=banner_title, text=banner_text)
        db.session.add(new_banner)
        db.session.commit()

        flash('Banner added successfully!', 'success')
        return redirect(url_for('banners'))
    else:
        return render_template('add_banner.html')

@app.route('/banners')
def banners():
    banners = Banner.query.all()
    return render_template('banners.html', banners=banners)

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the homepage or any other desired page
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

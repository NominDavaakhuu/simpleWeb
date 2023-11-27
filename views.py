from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from .models import Category, Product, Order
from datetime import datetime
from .forms import CheckoutForm
from . import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    categories = Category.query.order_by(Category.name).all()
    return render_template('index.html', categories=categories)


@main_bp.route('/products/<int:categoryid>')
def categoryproducts(categoryid):
    products = Product.query.filter(Product.category_id == categoryid)
    return render_template('categoryproducts.html', products=products)

# Referred to as "BASKET" to the user


# SEARCH

@main_bp.route('/products/')
def search():
    search = request.args.get('search')
    search = '%{}%' .format(search)
    products = Product.query.filter(Product.description.like(search)).all()
    return render_template('categoryproducts.html', products=products)


@main_bp.route('/order', methods=['POST', 'GET'])
def order():
    product_id = request.values.get('product_id')

    # retrieve order if there is one
    if 'order_id' in session.keys():
        order = Order.query.get(session['order_id'])
        # order will be None if order_id stale
    else:
        # there is no order
        order = None

    # create new order if needed
    if order is None:
        order = Order(status=False, firstname='', surname='',
                      email='', phone='', totalcost=0, date=datetime.now())
        try:
            db.session.add(order)
            db.session.commit()
            session['order_id'] = order.id
        except:
            print('failed at creating a new order')
            order = None

    #! calcultate TOTALPRICE
    total_price = 0
    if order is not None:
        for product in order.products:
            total_price = total_price + product.price

    #! are we adding an item?
    if product_id is not None and order is not None:
        product = Product.query.get(product_id)
        if product not in order.products:
            try:
                order.products.append(product)
                db.session.commit()
            except:
                return 'There was an issue adding the item to your basket'
            return redirect(url_for('main.order'))
        else:
            flash('item already in basket!')
            return redirect(url_for('main.order'))
    return render_template('order.html', order=order, total_price=total_price)

# Delete specific BASKET items


@main_bp.route('/deleteorderitem', methods=['POST'])
def deleteorderitem():
    id = request.form['id']
    if 'order_id' in session:
        order = Order.query.get_or_404(session['order_id'])
        product_to_delete = Product.query.get(id)
        try:
            order.products.remove(product_to_delete)
            db.session.commit()
            return redirect(url_for('main.order'))
        except:
            return 'Problem deleting item from order'
    return redirect(url_for('main.order'))

# SCRAP BASKET


@main_bp.route('/deleteorder')
def deleteorder():
    if 'order_id' in session:
        del session['order_id']
        flash('All items deleted')
    return redirect(url_for('main.index'))

# CHECKOUT


@main_bp.route('/checkout', methods=['POST', 'GET'])
def checkout():
    form = CheckoutForm()
    if 'order_id' in session:
        order = Order.query.get_or_404(session['order_id'])

        if form.validate_on_submit():
            order.status = True
            order.firstname = form.firstname.data
            order.surname = form.surname.data
            order.email = form.email.data
            order.phone = form.phone.data
            totalcost = 0
            for product in order.products:
                totalcost = totalcost + product.price
            order.totalcost = totalcost
            order.date = datetime.now()
            try:
                db.session.commit()
                del session['order_id']
                flash(
                    'Thank you! One of our awesome team members will contact you soon...')
                return redirect(url_for('main.index'))
            except:
                return 'There was an issue completing your order'
    return render_template('checkout.html', form=form)

# PROD DETAIL PAGE


@main_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    print(product_id)
    product = Product.query.get_or_404(product_id)
    return render_template('ProductDetail.html', product=product)

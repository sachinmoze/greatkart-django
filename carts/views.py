from itertools import product
import re
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Cart, cartItem
from store.models import Product, Variation
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
# Create your views here.
def __cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart    

def add_cart(request, product_id):
    current_user =  request.user
    product = Product.objects.get(id=product_id)  #get the product
    if current_user.is_authenticated:
        product_variation =[]
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
                print(key, value)
        is_cart_item_exists = cartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
        #try:
            cart_item = cartItem.objects.filter(product=product, user=current_user)
            #existing variations
            # current variations
            #item id
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            print(ex_var_list)     

            if product_variation in ex_var_list:
                index =  ex_var_list.index(product_variation)
                item_id = id[index]
                item = cartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
                
            else:   
                item = cartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
            # cart_item.quantity += 1
                item.save()
        #except cartItem.DoesNotExist:
        else:
            cart_item = cartItem.objects.create(
                product = product,
                quantity= 1,
                user=current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                #for item in product_variation:
                cart_item.variations.add(*product_variation)
            cart_item.save()

        # return HttpResponse(cart_item.product)
        # exit()
        return redirect('cart')
    else:   
        product_variation =[]
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
                print(key, value)

        
        try:
            cart = Cart.objects.get(cart_id=__cart_id(request))  #get the cart using cart_id present in the session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = __cart_id(request)
            )    

        cart.save()

        is_cart_item_exists = cartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
        #try:
            cart_item = cartItem.objects.filter(product=product, cart=cart)
            #existing variations
            # current variations
            #item id
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            print(ex_var_list)     

            if product_variation in ex_var_list:
                index =  ex_var_list.index(product_variation)
                item_id = id[index]
                item = cartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
                
            else:   
                item = cartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
            # cart_item.quantity += 1
                item.save()
        #except cartItem.DoesNotExist:
        else:
            cart_item = cartItem.objects.create(
                product = product,
                quantity= 1,
                cart = cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                #for item in product_variation:
                cart_item.variations.add(*product_variation)
            cart_item.save()

        # return HttpResponse(cart_item.product)
        # exit()
        return redirect('cart')

def remove_cart(request, product_id, cart_item_id):
    
    product   = get_object_or_404(Product, id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = cartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart      = Cart.objects.get(cart_id=__cart_id(request))
            cart_item = cartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity >1 :
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass        
    return redirect('cart')    

def remove_cart_item(request, product_id, cart_item_id):
    
    product   = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = cartItem.objects.get(product=product, user=request.user, id=cart_item_id) 
    else:
        cart      = Cart.objects.get(cart_id=__cart_id(request))
        cart_item = cartItem.objects.get(product=product, cart=cart, id=cart_item_id)    
    cart_item.delete()
    return redirect('cart')    




def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = cartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=__cart_id(request))
            cart_items = cartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity +=cart_item.quantity
        tax = (2*total)/100
        grand_total = tax + total

    except ObjectDoesNotExist:
        pass
    


    context ={
        'total': total,
        'quantity':quantity,
        'cart_items': cart_items,
        'tax' : tax,
        'grand_total' : grand_total, 
    }    

    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = cartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=__cart_id(request))
            cart_items = cartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity +=cart_item.quantity
        tax = (2*total)/100
        grand_total = tax + total
    except ObjectDoesNotExist:
        pass 

    context ={
        'total': total,
        'quantity':quantity,
        'cart_items': cart_items,
        'tax' : tax,
        'grand_total' : grand_total, 
    }    
    return render(request, 'store/checkout.html', context)
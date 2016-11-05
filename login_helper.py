from functools import wraps
from flask import g, request, redirect, url_for, flash
from flask import session as login_session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# def is_content_owner(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not g.user.id == login_session['user_id']:
#             flash('You are not the creator of this resource','danger')
#             return redirect(request.referrer)
#         return f(*args,**kwargs)
#     return decorated_function

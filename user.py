import random

from mailer                 import Mailer, Message

from flask                  import Blueprint, render_template, request, redirect

from flask_login            import ( LoginManager,
                                     login_required,
                                     login_user,
                                     logout_user,
                                     current_user
                                   )

from models.user            import Users

from forms import SignInForm, SignUpForm, ForgotForm
from log import log
from settings import EMAIL


user = Blueprint( 'user', __name__  )

login_manager = LoginManager()
login_manager.login_view = "user.signin"


def init_user( app ):
    """ Used by flask to initialize a user
    @param app: Application id set up by flask
    """
    login_manager.init_app(app)
    app.register_blueprint(user)


@login_manager.user_loader
def load_user(userid):
    """ Used by login to get a user "
    @param userid: User referenced in the database pass in by flask
    """
    try:
        user = Users.get(userid)
    except:
        return None
    return user


@user.route('/signup', methods=['GET', 'POST'])
def signup():
    """ Signup a new user 
    """
    if request.method == 'GET':
        form = SignUpForm(obj=current_user)

    else:
        form = SignUpForm(request.form)
        if request.method == 'POST' and form.validate():
            email      = form.email.data
            password   = form.password.data

            # Check if they they exist already
            user = Users.get_one(email = email)
            if not user:
                email = form.email.data
                first_name = form.first_name.data
                last_name = form.last_name.data
                user = User(**{'email':email, 'first_name':first_name, 'last_name':last_name})
                user.set_password(password)
                user.provider_type = form.provider_type.data
                user.practice_name = form.practice_name.data
                user.practice_type = form.practice_type.data
                try:
                    user.save()
                except Exception as e:
                    log.exception(f"Exception trying to save user {email}")
                else:
                    return redirect('/')
            else:
                form.errors = "User already exists"
        
    context = {'form':form}
    content = render_template( 'signup.html', **context )
    return content


@user.route('/signin', methods=['GET', 'POST'])
def signin():
    """ Sign in an existing user
    """
    form = SignInForm(request.form)
    next = request.args.get('next', '/')

    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data

        if email:
            user = Users.get_one( email = email )
            if not user:
                form.email.errors = ['No such user or password']
            else:
                if not user.check_password( password.encode() ):
                    form.email.errors = ['No such user or password']
                else:
                    login_user(user, remember=True)
                    return redirect(form.next.data)

    # Not a POST or errors
    form.next.data = next
    context = {'form':form }
    content = render_template( 'signin.html', **context )
    return content


@user.route('/signout')
@login_required
def signout():
    """ Logout a user
    """
    logout_user()
    return redirect('/')


def send_email( user, password ):
    """ Send new password to user
    """
    
    mail  = Mailer( host    = EMAIL['host'], 
                    port    = EMAIL['port'],
                    use_tls = EMAIL['use_tls'], 
                    usr     = EMAIL['user'], 
                    pwd     = EMAIL['password']
                  )
                   
    message = Message( From    = 'help@rxmedaccess.com',
                       To      = [user.email],
                       Subject = "Password Reset"
                     )
    
    body = """Your new password for {} is {}
              You can reset it to what you like on your settings page once you log in with
              this password
           """.format(__name__, password )

    message.Body = body
    try:
        mail.send(message)
    except Exception as e:
        log.error( 'Send mail error: {}'.format( str(e) ) )


@user.route( '/forgot', methods=['GET','POST'] )
def forgot():
    form = ForgotForm(request.form)

    if request.method == 'POST' and form.validate():
        email = form.email.data
        user = Users.get_one(email = email)
        if not user:
            form.email.errors = ['No such user']
            context = {'form':form}
            return render_template('forgot.html', **context )

        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        password = ''.join( map( lambda x: random.choice(chars), range(8) ))
        user.set_password( password )
        user.save()
        
        send_email( user, password )
        return redirect('/signin')
    else:
        context = {'form':form}
        return render_template('forgot.html', **context )
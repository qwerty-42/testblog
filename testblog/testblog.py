import os
import sqlite3
from flask import Flask,request,url_for,render_template,session,g,redirect,\
    abort,flash

app=Flask(__name__)

app.config.update(dict(
    DATABASE_USERS=os.path.join(app.root_path,'blogusers.db'),
    DATABASE_POSTS=os.path.join(app.root_path,'blogposts.db'),
    DEBUG=True,
    SECRET_KEY='I am a Jedi'
))


def connect_db(flag):
    rv=sqlite3.connect(app.config['DATABASE_'+flag.upper()])
    rv.row_factory=sqlite3.Row
    return rv

def init_db(flag):
    db=get_db(flag)
    with app.open_resource(flag+'.sql',mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb():
    init_db('posts')
    init_db('users')
    #print("Everything is alright.")

def get_db(flag):
    if not hasattr(g,flag+'_db'):
        setattr(g,flag+'_db',connect_db(flag))
    return eval('g.'+flag+'_db')

@app.teardown_appcontext
def close_db(error):
    if hasattr(g,'posts_db'):
        g.posts_db.close()
    if hasattr(g,'users_db'):
        g.users_db.close()

#databases



@app.route('/')
def index():
    return redirect(url_for('show_posts',page=1,posts_perpage=10))


@app.route('/page=<int:page>/epg=<int:posts_perpage>',methods=['GET','POST'])
def show_posts(posts_perpage=10,page=1):
    if request.method=='POST':
        if request.form['posts_perpage'].isdigit():
            posts_perpage=int(request.form['posts_perpage'])
        else:
            posts_perpage=10
    db=get_db('posts')
    posts=db.execute('select * from posts order by id desc').fetchall()
    posts_sum=len(posts)
    posts_page=max(1,(posts_sum-1)//posts_perpage+1)
    return render_template('show_posts.html',posts_perpage=posts_perpage,posts=posts[(page-1)*posts_perpage:min(posts_sum,page*posts_perpage)],posts_page=posts_page,page=page)

@app.route('/register',methods=['GET','POST'])
def register():
    db=get_db('users')
    error=None
    if request.method=='POST':
        if db.cursor().execute('select username from users where username=?',(str(request.form['username']),)).fetchall()!=[]:  
            error= 'Existed Username'
            flash('Existed Username')
        elif str(request.form['password1'])!=str(request.form['password2']):
            error='Password not the same'
            flash('Password not the same')
        elif str(request.form['username'])=='':
            error='Username is void'
            flash('Username is void')
        elif str(request.form['password1'])=='':
            error='Password is void'
            flash('Password is void')
        else:
            db.cursor().execute('insert into users (username,password) values (?,?)',[str(request.form['username']),str(request.form['password1'])])
            db.commit()
            flash('Successfully registered.')
            return redirect(url_for('show_posts',page=1,posts_perpage=10))
    return render_template('register.html',error=error)

@app.route('/<username>/add_post',methods=['GET','POST'])
def add_post(username):
    if request.method=='GET':
        return render_template('posting.html',username=username)
    db=get_db('posts')
    if session['username']==None:
        abort(401)
    if request.form['text']=='' or request.form['title']=='':
        flash('Content and title can\'t be void.')
        return redirect(url_for('show_posts',page=1,posts_perpage=10))
    db.execute('insert into posts (author,title,text) values (?,?,?)',
            [session['username'],request.form['title'],request.form['text']])
    db.commit()
    flash('New post committed.')
    return redirect(url_for('show_posts',page=1,posts_perpage=10))

@app.route('/login',methods=['GET','POST'])
def login():
    error=None
    db=get_db('users')
    if request.method=='POST':
        t=db.execute('select username,password from users where username=?',(str(request.form['username']),)).fetchall()
        if t==[]:
            error = 'Invalid username'
        elif str(t[0][1])!=str(request.form['password']):
            error = 'Invalid password'
        else:
            session['username']=str(request.form['username'])
            flash('You were logged in.')
            return redirect(url_for('show_posts',posts_perpage=10,page=1))
    return render_template('login.html',error=error)

@app.route('/logout')
def logout():
    session.pop('username',None)
    flash('You were logged out.')
    return redirect(url_for('show_posts',posts_perpage=10,page=1))

@app.route('/delete/<int:post_id>')
def delete(post_id):
    db=get_db('posts')
    c=db.execute('select * from posts where id=?',(post_id,)).fetchone()
    if (c['author']!=session['username']):
        flash('Not authorized.')
        return redirect(url_for('show_posts'))
    db.execute('delete from posts where id=?',(post_id,))
    db.commit()
    flash('Alreadly Deleted.')
    return redirect(url_for('show_posts',posts_perpage=10,page=1))    
    
@app.route('/users/<username>/<int:page>/<int:posts_perpage>',methods=['GET','POST'])
def users(username,page=1,posts_perpage=10):
    if request.method=='POST':
        if not request.form['posts_perpage'].isdigit():
            posts_perpage=10
        elif int(request.form['posts_perpage'])>0:
            posts_perpage=int(request.form['posts_perpage'])
        else: 
            posts_perpage=10
    db=get_db('posts')
    posts=db.execute('select * from posts where author=? order by id desc',(username,)).fetchall()
    posts_sum=len(posts)
    posts_page=max(1,(posts_sum-1)//int(posts_perpage)+1)
    return render_template('users.html',posts=posts[(page-1)*posts_perpage:min(posts_sum,page*posts_perpage)],username=username,page=page,posts_page=posts_page,posts_perpage=posts_perpage)

if __name__=='__main__':
    app.run()

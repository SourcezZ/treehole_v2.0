#coding=utf-8
import sqlite3, time ,os ,shutil,re
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response, send_from_directory
from contextlib import closing
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from PIL import Image
from flask_login import UserMixin,login_user,LoginManager
from random import choice,sample

#数据库
DATABASE = 'demoapp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
#USERNAME = 'admin'
#PASSWORD = 'admin'
UPLOADED_PHOTOS_DEST = 'demoapp/static/photo'
app = Flask(__name__)
app.config.from_object(__name__)



@app.route('/regist',methods=['GET', 'POST'])
def regist():
    if request.method == 'POST':
        try:
            g.db.execute('insert into user (username, password) values ( ?, ?)',[request.form['username'], request.form['password']])
            g.db.commit()
            flash('注册成功，请登陆')
            return redirect(url_for('regist'))
        except:
            flash('已存在用户或其他问题，请重新注册')
    return render_template('regist.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = g.db.execute('select username,password from user order by id asc')
    user = [dict(username=str(row[0]),password=str(row[1])) for row in cur.fetchall()]
    if request.method == 'POST':
        for i in user:
            if (request.form['username'] == i['username'] and request.form['password'] == i['password'] ):
                session['logged_in'] = True
                flash('你已成功登陆')
                return redirect(url_for('show_entries'))
        else:
             flash('账号或密码输入错误')   
    return render_template('login.html')



photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB

class UploadForm(FlaskForm):
    photo = FileField(validators=[
        FileAllowed(photos, u'只能上传图片！'), 
        FileRequired(u'文件未选择！')])
    submit = SubmitField(u'上传')

'''@app.route('/addpic', methods=['GET', 'POST'])
def upload_file():
    global file_url
    form = UploadForm()
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        file_url = photos.url(filename)
    else:
        file_url = None
    return render_template('addpic.html', form=form, file_url=file_url)'''

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hot',methods=['GET','POST'])
def show_hot():
    cur = g.db.execute('select  title, text, time, up, id,area ,flag from entries order by up desc limit 5')
    num = g.db.execute('update number set num = num +1')
    number = g.db.execute('select num from number')
    #picture = g.db.execute('select file_url,id from pictures')
    #show_pic = [dict(pic=row[0],id=row[1]) for row in picture.fetchall()]
    show_num = [dict(num=row[0]) for row in number.fetchall()]
    entries = [dict(title=row[0], text=row[1], time=row[2],up=row[3],id=row[4],area=row[5]) for row in cur.fetchall()]
    g.db.commit()
    return render_template('show_hot.html', entries=entries , show_num=show_num)

@app.route('/pictures', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    #picture = g.db.execute('select file_url,id from pictures')
    #show_pic = [dict(pic=row[0],id=row[1]) for row in picture.fetchall()]
    or_path = 'demoapp/static/photo/'
    sl_path = 'demoapp/static/slphoto/'
    or_list = os.listdir(or_path)
    sl_list = os.listdir(sl_path)
    or_result = [(or_list, os.stat(or_path + or_list).st_ctime) for or_list in os.listdir(or_path)]
    sl_result = [(sl_list, os.stat(sl_path + sl_list).st_ctime) for sl_list in os.listdir(sl_path)]
    or_list = sorted(or_result, key=lambda x: x[1],reverse=True)
    sl_list = sorted(sl_result, key=lambda x: x[1],reverse=True)
    or_photo = [dict(or_pic = row[0]) for row in or_list]
    sl_photo = [dict(sl_pic = row[0], sl_time = time.strftime("%Y-%m-%d %H:%M:%S" , time.localtime(row[1]))) for row in sl_list]
    photo = []
    for i in range(len(or_photo)):
        photo.append(dict(or_photo[i],**sl_photo[i]))
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        #file_url = photos.url(filename)
        #g.db.execute('insert into pictures (file_url,time) values (?,?)',[file_url,time.strftime("%a %m-%d %H:%M:%S", time.localtime())])
        #g.db.commit()
        #filename1 = filename.rstrip('.bmp.jpg.png.tiff.gif.pcx.tga.exif.fpx.svg.psd.cdr.pcd.dxf.ufo.eps.ai.raw.WMF')
        img = Image.open(or_path + filename)
        if img.width>=1000 or img.height>=1000:
            img = img.resize((250, 250),Image.ANTIALIAS)
            img.save(sl_path + filename)
        else:
            shutil.copyfile(or_path + filename,sl_path + filename)        
        flash('上传成功')
    else:
        filename = None
    return render_template('pictures.html',form=form,photo=photo)
    #show_pic=show_pic

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
        with closing(connect_db()) as db:
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read().decode())
            db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

@app.route('/flag',methods=['GET','POST'])
def flag():
    #cur = g.db.execute('select flag from entries where flag not null')
    #entries = [dict(flag=row[0]) for row in cur.fetchall()]
    #g.db.commit()
    return render_template('flag.html')

@app.route('/flag/<f>',methods=['GET','POST'])
def f(f):
    query = f
    cur = g.db.execute('select title, text, time, up, id,area ,flag from entries  where text like "%'+query+'%" or title like "%'+query+'%" or area like "%'+query+'%" or time like "%'+query+'%" or flag like "%'+query+'%" order by id desc')
    entries = [dict(title=row[0], text=row[1], time=row[2],up=row[3],id=row[4],area=row[5]) for row in cur.fetchall()]
    g.db.commit()
    #flag = "".join(sample(entries[0]['title'],2))
    #print (flag)
    #flag1 = [dict(title = row[0]) for row in flag.fetchall()]
    return render_template('flag.html',entries=entries)

@app.route('/index',methods=['GET', 'POST'])
def show_entries():
    cur = g.db.execute('select title, text, time, up, id,area,flag from entries order by id desc limit 10')        
    data = g.db.execute('select count(1) from entries')
    num = g.db.execute('update number set num = num +1')
    number = g.db.execute('select num from number')
    #picture = g.db.execute('select file_url,id from pictures')
    #show_pic = [dict(pic=row[0],id=row[1]) for row in picture.fetchall()]
    show_data = [dict(data=row[0]) for row in data.fetchall()]
    show_num = [dict(num=row[0]) for row in number.fetchall()]
    if request.method == 'POST':
        query = request.form['query']
        if query =='':
            return render_template('show_entries.html',num=show_num[0]['num'])
        cur = g.db.execute('select title, text, time, up, id,area,flag from entries  where text like "%'+query+'%" or title like "%'+query+'%" or area like "%'+query+'%" or time like "%'+query+'%" or flag like "%'+query+'%" order by id desc')        
        data = g.db.execute('select count(1) from entries  where text like "%'+query+'%" or title like "%'+query+'%" or area like "%'+query+'%" or time like "%'+query+'%" or flag like "%'+query+'%" order by id desc')
        show_data = [dict(data=row[0]) for row in data.fetchall()]
        entries = [dict(title=row[0], text=row[1], time=row[2],up=row[3],id=row[4],area=row[5],flag=row[6]) for row in cur.fetchall()]
        g.db.commit()
        return render_template('show_entries.html', entries=entries , num=show_num[0]['num'])
    entries = [dict(title=row[0], text=row[1], time=row[2],up=row[3],id=row[4],area=row[5],flag=row[6]) for row in cur.fetchall()]
    g.db.commit()
    return render_template('show_entries.html', entries=entries , num=show_num[0]['num'],data=int(show_data[0]['data']/10),next=10)

@app.route('/<p>',methods=["POST","GET"])
def page(p):
    route = re.sub("\D","",request.path)
    index = int(route)
#   cur = g.db.execute('select title, text, time, up, id,area from entries order by id desc limit "'+route+'",10 ')
    cur = g.db.execute('select title, text, time, up, id,area,flag from entries order by id desc limit {index}, 10'.format(index=index))
    data = g.db.execute('select count(1) from entries')
    num = g.db.execute('update number set num = num +1')
    number = g.db.execute('select num from number')
    #picture = g.db.execute('select file_url,id from pictures')
    #show_pic = [dict(pic=row[0],id=row[1]) for row in picture.fetchall()]
    show_data = [dict(data=row[0]) for row in data.fetchall()]
    show_num = [dict(num=row[0]) for row in number.fetchall()]
    entries = [dict(title=row[0], text=row[1], time=row[2],up=row[3],id=row[4],area=row[5],flag=row[6]) for row in cur.fetchall()]
    g.db.commit()
    return render_template('show_entries.html', entries=entries , num=show_num[0]['num'], data=int(show_data[0]['data']/10),next=index+10,previous=index-10)

@app.route('/up/<uid>',methods=["POST","GET"])
def up(uid):
    g.db.execute('update entries set up = up + 1 where id == "'+uid+'" ')
    g.db.commit()
    return redirect(url_for('show_entries'))

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    f = open('demoapp/static/keyword.txt', 'r', encoding='utf-8')
    f1 = request.form['title']
    f2 = request.form['text']
    for line in f: #遍历每一个敏感词
        if line.strip() in f1: #判断是否包含敏感词
            flash("该标题含有屏蔽字:%s。请重新输入"%(line.strip()))
            f.close()
            return redirect(url_for('show_entries'))
        if line.strip() in f2: #判断是否包含敏感词
            flash("该内容含有屏蔽字:%s。请重新输入"%(line.strip()))
            f.close()
            return redirect(url_for('show_entries'))    
            #result = f1.replace(line.strip(), '**')
            #f1 = result
    f.close()
    if((request.form['title']=='' and request.form['text']=='') or (request.form['title']==' ' and request.form['text']==' ') or (request.form['title']==' ' and request.form['text']=='') or (request.form['title']=='' and request.form['text']==' ')):
        flash("标题和内容至少要有一条不是空的哦")
        return redirect(url_for('show_entries')) 
    g.db.execute('insert into entries (title, text, time, area, flag) values (?, ?, ?, ?, ?)',[request.form['title'], request.form['text'], time.strftime("%a %m-%d %H:%M:%S", time.localtime()),request.form['area'],request.form['flag']])
    g.db.commit()
    flash('新记录已提交')
    return redirect(url_for('show_entries'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('你已经注销')
    return redirect(url_for('show_entries'))

@app.route('/')
def zy():
    return render_template("zy.html")

@app.route('/layout')
def layout():
    return render_template('layout.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)

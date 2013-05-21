import webapp2
import re
import os
import jinja2
from google.appengine.ext import db
import random
import string
import hmac
import hashlib
import urllib2
from xml.dom import minidom
import json
import datetime                                             #for json serializablity for datetime 
import logging
import time
from google.appengine.api import memcache

jinja_env = jinja2.Environment(autoescape=True,loader=
                               jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),'templates')))
#<---------------------------------------------------for bi-day checking----------------------------------------------------------------------------->
months = ['January','February','March','April','May','June','July','August','September','October','November','December']
month_abbvs = dict((m[:3].lower(),m) for m in months)
def escape_html(st):
    for (i,o) in (("&","&amp;"),("<","&lt;"),(">","&gt;"),('"',"&quot;")):
        st=st.replace(i,o)
    return st
def valid_month(month):
    if month:
        #month=month.capitalize()
        short_month = month[:3].lower()
        if month_abbvs.get(short_month):                #if month_abbvs[key] (if not in dict then it will raise error
            return month    #????
        #if month in month:
         #   return month
def valid_day(day):
    if day and day.isdigit():
        day=int(day)
        if day <=31 and day >0:
            return day
def valid_year(year):
    if year and year.isdigit() and len(year) ==4:
        year=int(year)
        if year <= 2040 and year >= 1920:
            return year

#<------------------------------------------------------------end-------------------------------------------------------------------------------------->

        
#<-------------------------------------rot13------------------------------------------------------------------------------------------------------------>
def rot13(p):
    q=""
    for i in range(0,len(p)):
        if 97 <= ord(p[i])and ord(p[i]) <= 122:
            if ord(p[i])+13 > 122:
                d=(ord(p[i])+13) - 122
                q=q+chr(97+d-1)
            else:
                q=q+chr(ord(p[i])+13)
        elif ord(p[i]) >=65 and ord(p[i]) <=90:
            if ord(p[i])+13 > 90:
                    d=(ord(p[i])+13) - 90
                    q=q+chr(65+d-1)
            else:
                    q=q+chr(ord(p[i])+13)
        else:
            q=q+p[i]
    return q
#<----------------------------------end------------------------------------------------------------------------------------------------------------------->

#<--------------------------------render_str-------------------------------------------------------------------------------------------------------------->

def render_str(template,**param):
    t = jinja_env.get_template(template)
    return t.render(param)
#<-------------------------------end----------------------------------------------------------------------------------------------------------------------->

#<------------------------------------------for checking the input at time of registration----------------------------------------------------------------->
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{6,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')  #[\S] means not any white space,newline,tab,catrige
def valid_email(email):
    return not email or EMAIL_RE.match(email)
#<-------------------------------------------------------end---------------------------------------------------------------------------------------------->


#<---------------------------------------------------------methods for hashing the password---------------------------------------------------------------->
def create_salt():
    s=""
    lis = random.sample(string.letters,5)
    for i in lis:
        s = s+i
    return s

def make_pw_hash(name, pw ,pass_salt):
    if pass_salt == None:           #this condition is only used at time of validating the password
        salt =create_salt()
    else:
        salt = pass_salt
    hashed = hashlib.sha256(name + pw + salt).hexdigest()   #we are hashing the password with username,pw,salt
    return '%s,%s' % (hashed,salt)                          #we are storing hashed password only and salt with it

def valid_pw(name,pw,hashed):
    salt = hashed.split(',')[1]
    if make_pw_hash(name,pw,salt) == hashed:
        return True

#<--------------------------------------------------------------------end----------------------------------------------------------------------------------->    


#<-----------------------------------------------------------cookies hashing method------------------------------------------------------------------------->

SECRET = 'ROHITCOOKIES'
def hash_str(s):
    return hmac.new(SECRET,s).hexdigest()

def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val



#<---------------------------------------------------------end of cookies---------------------------------------------------------------------------------->

    
#<--------------------------------------------------------------------Tables(entities)----------------------------------------------------------------------->

#The way to define an entity in Google App Engine is to define a class:
#basic format of type::property_name=db.TypeProperty
class Art(db.Model):                                                #db.Model
    title = db.StringProperty(required = True)                      #reqiured means it need to be 
    art = db.TextProperty(required = True)                          #in the database otherwise Python will EXCEPTION
    created = db.DateTimeProperty(auto_now_add = True)              #it wil automatically add current data and time to the property
    coordinate = db.GeoPtProperty()                                   #TextProperty has more than 500 characters but cant be indexed while string can be
    #db.GeoptProperty()  is used for storing geographics location in database means lat,lon                        
    
#table for blog
class BLOG(db.Model):
     subject = db.StringProperty(required = True)
     content = db.TextProperty(required = True)
     created = db.DateTimeProperty(auto_now_add = True)
     last_modified = db.DateTimeProperty(auto_now = True)

     def render(self):
         self._render_text = self.content.replace('\n', '<br>')
         return render_str("blog.html", p=self)

#table for registration
class Registration(db.Model):
    username = db.StringProperty(required = True)
    password = db.StringProperty(required = True)
    email = db.EmailProperty()

    
#<------------------------------------------------------------------end of tables----------------------------------------------------------------------------->
class BaseHandler(webapp2.RequestHandler):
    def write(self,*a,**kw):                                        #this will saves us from writing 
        self.response.out.write(*a,**kw)                            #self.response.out.write all time                                


    def render_str(self,template,**param):
        t = jinja_env.get_template(template)
        return t.render(param)


    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))

#<--------------------------------------------------------------- BLOG stuff---------------------------------------------------------------------------------->

def blog_cache(update = False):
    
    #s_t1 = time.strftime("%S")
    key = 'btop'
    tkey = 'time_key'
    e_t = memcache.get(tkey)
    content = memcache.get(key)
    if e_t:
        s_t = time.strftime("%S")
        s_t = str(int(s_t)+int(e_t))
        memcache.set(tkey,s_t)
         
    if update or content is None:
        logging.error("DB REQUEST")
        #content = db.GqlQuery("select * from BLOG")
        content = BLOG.all().order('-created')
        s_t = time.strftime("%S")
        content = list(content)
        memcache.set(tkey,s_t)
        memcache.set(key,content)
    return content,s_t
   
def perma_cache(blog_id):
    data = memcache.get(str(blog_id))
    tkey = "perma_time"
    end_time = memcache.get(tkey)
    if end_time:
        current_time = time.strftime("%S")
        current_time = str(int(end_time)+int(current_time))
        memcache.set(tkey,current_time)
    if data is None:
        data = BLOG.get_by_id(int(blog_id))
        current_time = time.strftime("%S")
        memcache.set(tkey,current_time)
        memcache.set(str(blog_id),data)
    return data,current_time
    
class BlogHandler(BaseHandler):
    def get(self):
        if self.request.path.endswith(".json"):
              #json_content = list(BLOG.get_latest())
            k = blog_cache()
            self.write(repr('DATABASE'))
            l = []
            timeformat = '%a %b %d %H:%M:%S %Y'
            #we can use this also i.last.modified.strftime(timeformat)
            for i in k:
                d ={}
                
                d['subject']= i.subject
                d['content']=i.content
                d['created']=i.created
                d['last_modified']=i.last_modified
                dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None    #because datetime obj is not json itratable,so we make it isostandard
                l.append(d)
            json_dump = json.dumps(l, default = dthandler)
            #self.write(json_dump)
        else:
            co_user_id = self.request.cookies.get('user_id')
            if co_user_id:
                if check_secure_val(co_user_id):
                    key_id = Registration.get_by_id(int(check_secure_val(co_user_id)))
                    name = key_id.username
                    posts,t = blog_cache()
                    self.render("blog.html", posts = posts,name=name,time=t)
            else:
                posts,t = blog_cache()
                self.render("blog.html", posts = posts,time=t)

class NewHandler(BaseHandler):
    def get(self):
        self.render("newpost.html")
    def post(self):
        subject=self.request.get("subject")
        content=self.request.get("content")

        if subject and content:
            b = BLOG(subject = subject, content = content)
            b_key = b.put()  #key('BLOG',id)
            blog_cache(True)
            self.redirect("/blog/%s" % str(b.key().id()))
        else:
          error = "We need both field subject as well as Post"
          self.render("newpost.html",error=error)

class PermaHandler(BaseHandler):
    def get(self,blog_id):
        if self.request.path.endswith(".json"):
            key1 = BLOG.get_by_id(int(blog_id))
            timeformat = '%a %b %d %H:%M:%S %Y'
            list_json = []
            d = {}
            d['subject'] = key1.subject
            d['content'] = key1.content
            d['created'] = key1.created.strftime(timeformat)
            d['lst_modified'] = key1.last_modified.strftime(timeformat)
            
            list_json.append(d)
            json_dumps = json.dumps(list_json)
            self.write(json_dumps)

        else:
            key,t = perma_cache(blog_id)
            """key1 = BLOG.get_by_id(int(blog_id))
            #post = db.get(key1)"""
            self.render("permanent.html",blog=key,time=t)
class PermaJsonHandler(BaseHandler):
    def get(self,blog_id):
        key1 = BLOG.get_by_id(int(blog_id))
        timeformat = '%a %b %d %H:%M:%S %Y'
        list_json = []
        d = {}
        d['subject'] = key1.subject
        d['content'] = key1.content
        d['created'] = key1.created.strftime(timeformat)
        d['lst_modified'] = key1.last_modified.strftime(timeformat)    
        list_json.append(d)
        json_dumps = json.dumps(list_json)
        self.write(json_dumps)

        
class JsonHandler(BaseHandler):
    def get(self):
        #json_content = list(BLOG.get_latest())
        k,t = blog_cache()
        #k=json_content
        l = []
        timeformat = '%a %b %d %H:%M:%S %Y'
        #we can use this also i.last.modified.strftime(timeformat)
        for i in k:
            d ={}
            sub = i.subject
            con = i.content
            crea = i.created
            d['subject']= i.subject
            d['content']=i.content
            d['created']=i.created
            d['last_modified']=i.last_modified
            dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None    #because datetime obj is not json itratable,so we make it isostandard
            l.append(d)
        json_dump = json.dumps(l, default = dthandler)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_dump)
       
         
#<---------------------------------------------------------end of blog stuff---------------------------------------------------------------------------------->
GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=600x300&sensor=false&"

def gmaps_img(points):
    markers = '&'.join('markers=%s,%s' % (p.lat, p.lon)
                       for p in points)
    return GMAPS_URL + markers


IP_URL = "http://api.hostip.info/?ip="
def get_coords(ip):
    #ip = "203.199.146.114"
    #ip=  "8.8.8.8"
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except urllib2.URLError:
        return
    
    if content:
        #parse the xml
        parse = minidom.parseString(content)
        coor =  parse.getElementsByTagName("gml:coordinates")
        if coor:
            coordinate = coor[0].childNodes[0].nodeValue
            st = coordinate.split(",")                     # (lon,lat), so we have to switch them around.
            lat = st[1]
            lon = st[0]
            return db.GeoPt(lat,lon)    #it is datatype for storing the postition in google data store 
            
#<------------------------------------------------------------start of ascii-chain------------------------------------------------------------------------->    
#art_key = db.key.from_path('ASCIIChan','arts')
def top_arts(update = False):
    key = 'top'
    arts = memcache.get(key)   #key and value should be string for memcache lib 
    if arts is None or update:
        logging.error("DB QUERY")
        arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC limit 10")
        #prevent the running of multiple query
        arts = list(arts)
        memcache.set(key,arts)
    return arts



class AsciiHandler(BaseHandler):
    def render_front(self,title="",art="",error=""):
        
        arts = top_arts()
        
        #find which arts have coordinate
        points = filter(None,(a.coordinate for a in arts))
        img_url=None
        if points:
            img_url = gmaps_img(points)
       
        self.render("ascii.html",title=title,art=art,error=error,arts=arts,img_url=img_url)

    def get(self):
        self.write(self.request.remote_addr)
        self.write(repr(get_coords(self.request.remote_addr)))      #repr is used for printing python objects into HTML
                                                                    #self.request.remote_addr gives the current ip address
                                                                    #127.0.0.1 is loop back address of every machine and is used to refer to itself
        self.render_front()

    def post(self):
        title=self.request.get("title")                             #title is the name in the ascii.html
        art=self.request.get("art")
        #error handling


        if art and title:
            a = Art(title = title, art = art)                           #passing the data to the art entity(table)
            coords = get_coords(self.request.remote_addr)
            if coords:
                a.coordinate = coords
            a.put()                                                 #this will store it in database
            #CACHE.clear()----->will be used.if there is only one user
            top_arts(True)          #cache stampede     means for multiple user at one time we will not clear the cache but update the cache
            self.redirect("/unit3/ascii")
        else:
            error = "we need both a title and art"
            self.render_front(title,art,error)

#<--------------------------------------------------END of ascii-chain---------------------------------------------------------------------------------------->
class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(render_str('bi-day.html'))
    def post(self):
        hv_error=False
        user_month = self.request.get('month')
        user_day = self.request.get('day')
        user_year = self.request.get('year')
        params = dict(day=user_day,month=user_month,year=user_year)
        if not valid_month(user_month):
            params['error_month']="error in month"
            hv_error=True
        if not valid_day(user_day):
            params['error_day']="error in day"
            hv_error=True
        if not valid_year(user_year):
            params['error_year']="error in year"
            hv_error=True
        if hv_error:
            self.response.out.write(render_str("bi-day.html",**params))   #if we are passing a dictionary then we have to pass like this(**p)
                                                                          #if we are passing the actual parameter like p='asa'  
        else:
            self.redirect("/rot13")
            

class Rot13Handler(webapp2.RequestHandler):
    def get(self):
         self.response.out.write(render_str("rot13.html"))
        
    def post(self):
        user_rot=self.request.get('text')
        rot_13=''
        if user_rot:
            rot_13=rot13(user_rot)

        self.response.out.write(render_str("rot13.html",text=rot_13))

        
#<--------------------------------------------start of registration--------------------------------------------------------------------------------------->
        
class SignUp(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(render_str("signup.html"))
        
    def post(self):
        us_input=self.request.get('username')
        pass_input=self.request.get('password')
        ver_input=self.request.get('verify')
        email_input=self.request.get('email')
        error_flag=False
        params=dict(username=us_input,email=email_input)      #just a dict with these else there is no need of pass we can d=dict=()
        #checking if username is already exits 
        reg = db.GqlQuery("select * from Registration")
        for r in reg:
            if r.username == us_input:
                error_flag = True
                params['usname_error'] = "username already exists"
        
        if not valid_username(us_input):
            error_flag=True
            params['usname_error']="invalid user_name"
            
        if not valid_password(pass_input):
            error_flag=True
            params['pass_error']="invalid password"
        elif ver_input!=pass_input:
            params['ver_error']="your password didn't match"
            error_flag=True

        if not valid_email(email_input) or not email_input:
            error_flag=True
            params['mail_error']="it is'nt a valid e-mail address "
        if error_flag:
            self.response.out.write(render_str("signup.html",**params))
        else:
            pw = make_pw_hash(us_input,pass_input,'')
            R = Registration(username = us_input, password = pw, email = email_input)
            R.put()
            user_id = str(R.key().id())
            hashed_user_id = make_secure_val(user_id)
            self.response.headers.add_header('set-cookie','user_id = %s;path=/welcome' % hashed_user_id)   #value of cookies always must be string type
            self.redirect('/welcome')
            #self.redirect("/unit2/welcome?userid=" + str(R.key().id()))
            #self.redirect('/unit2/welcome?username=' + self.username)

    
class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')

    def post(self):
        username=self.request.get('username')
        password=self.request.get('password')                                           #in where we can't give usname=usname instead the method is "usname=:1",usname
        #q=db.GqlQuery("select * from Registration where username=:1", username)
        #key1 = db.GqlQuery("select __key__ from Registration where username=:1", username).is_keys_only()
        #row = q.get()                                                                               #for getting the specific row we use .get() or .fetch() 
        #R = Registration.by_name(self.username)=="select * from Registration where username=username"
        
        R = Registration.all().filter('username = ',username).get()
        #R = r.by_name(username)
        if R:
            if valid_pw(username,password,R.password):
                user_id=R.key().id()
                hashed_user_id = make_secure_val(str(user_id))
                self.response.headers.add_header('set-cookie','user_id = %s;path=/' % hashed_user_id)
                #self.render('login.html',error=user_id)
                self.redirect('/welcome')
                
        else:
            error="Username or Password is incorrect"
            self.render('login.html',error=error)
        #self.response.header.add_header('set-cookie','user_id=%s;path=/')
    
class LogOutHandler(BaseHandler):
    def get(self):
        self.response.headers.add_header('set-cookie','user_id=;path=/')
        self.redirect('/blog')

        
class Welcome(webapp2.RequestHandler):
    def get(self):
        #username=self.request.get('username')
        cookie_user_name = self.request.cookies.get('user_id')
        valid_user_id = check_secure_val(cookie_user_name)
        if valid_user_id:
            id_row = Registration.get_by_id(int(valid_user_id))
            username = id_row.username
            self.response.out.write(render_str("welcome.html", username=username))
        else:
            self.redirect('/signup')

class GameHandler(BaseHandler):
    def get(self):
        self.render('gameani.html')
        
app = webapp2.WSGIApplication([
    ('/',MainHandler),
    ('/rot13',Rot13Handler),
    ('/signup',SignUp),
    ('/welcome',Welcome),
    ('/unit3/ascii',AsciiHandler),
    ('/blog/?',BlogHandler),               #with one handler we handling two requests                                       
    ('/blog/newpost',NewHandler),
    ('/blog/(\d+).json',PermaJsonHandler),
    ('/blog/(\d+)',PermaHandler),
    ('/login',LoginHandler),
    ('/logout',LogOutHandler),
    ('/blog.json',JsonHandler),
    ('/game',GameHandler)]
                              ,debug=True)

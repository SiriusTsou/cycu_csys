import httplib,urllib, json
import hmac, hashlib, base64, binascii
import sys, time, os
import urllib3
import logging
from multiprocessing import Process, freeze_support

#control output utf 8
import codecs

#define global var
str_username = ""
str_password = ""
str_JSESSIONID = ""
str_NSC_dtzt = "" 
str_secureRandom = ""
str_hash = ""
str_pageId = ""
#================================================================
def init_Cookie():
    # get the init cookie 
    conn = httplib.HTTPConnection("csys.cycu.edu.tw")
    conn.request("GET", "/student/")
    r1 = conn.getresponse()
    # print r1.status, r1.reason
    conn.close

    ar_setcookie = r1.getheader("Set-Cookie")  
    global str_JSESSIONID, str_NSC_dtzt
    str_JSESSIONID = ar_setcookie.split(', ')[0].split(';')[0]
    str_NSC_dtzt   =  ar_setcookie.split(', ')[1].split(';')[0]
    # print str_JSESSIONID
    # print str_NSC_dtzt

#================================================================
def init_Login():
    #  initlogin
    conn = httplib.HTTPConnection("csys.cycu.edu.tw")
    params = urllib.urlencode({ 'cmd': 'login_init'})
    # print params
    headers = { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Cookie": str_JSESSIONID+"; "+str_NSC_dtzt  }
    # print headers
    conn.request("POST", "/student/sso.srv", params, headers)
    r2 = conn.getresponse()
    # print r2.status, r2.reason

    global str_secureRandom, str_hash
    str_secureRandom = json.loads(r2.read())['secureRandom'] 
    # print str_secureRandom

    
    md5 = hashlib.md5()
    md5.update( str_password )
    str_md5Password = md5.hexdigest()
    # print str_md5Password

    dig = hmac.new( str_md5Password,"", hashlib.sha256)
    dig.update(str_username)
    dig.update(str_secureRandom)
    str_hash = binascii.hexlify(bytearray(dig.digest())) 
    # print str_hash
    conn.close()

#=======================================================
def login():
    #  login
    conn = httplib.HTTPConnection("csys.cycu.edu.tw")
    params = urllib.urlencode({ 'cmd': 'login', 'userid':str_username,'hash':str_hash})
    headers = { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Cookie": str_JSESSIONID+"; "+str_NSC_dtzt  }    
    conn.request("POST", "/student/sso.srv", params, headers)
    r2 = conn.getresponse()
    # print r2.status, r2.reason
    data = r2.read()
    # print data 
    conn.close()
    try:        
        if ( json.loads(data)['result'] == 'false'):
            raise    
        global str_pageId
        str_pageId = json.loads(data)['pageId']
        # print str_pageId
    except:
        print "[*] Error! repeat login. please wait"
        os.system("pause")
        os.system("chcp 950")
        sys.exit()

#======================================================
def get_Opcode():
    # get CourseId by student insert list and return it 
    conn = httplib.HTTPConnection("csys.cycu.edu.tw")
    params = urllib.urlencode({ 'cmd': 'selectJson'})
    headers = { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
              "Cookie": str_JSESSIONID+"; "+str_NSC_dtzt,     
              "Page-Id": str_pageId}
    conn.request("POST", "/student/student/op/StudentCourseTrace.srv", params, headers)
    r2 = conn.getresponse()
    # print r2.status, r2.reason
    data = r2.read()
    conn.close()
    try:        
        if ( json.loads(data)['totalRows'] == 0):
            return list()  
        insert_list = list()
        for i in range(0,len(json.loads(data)['datas'])): 
            str_op_code = json.loads(data)['datas'][i]['op_code'] 
            str_cname = json.loads(data)['datas'][i]['cname'].encode('utf8')
            try: 
                print str_op_code," ","\""+str_cname+"\""+"\r\n"
            except:
                pass            
            insert_list.append(str_op_code)
        return insert_list
    except:
        print("[*] Error! someting error")
            
#======================================================
def fuck_course( insert_list ):
    #  run addSelection post
    try:
        cir_cnt = 0 
        circle = ['/','|','\\','-'] 
        while True:            
            for i in range(0, len(insert_list)):
                tmp_op_code = insert_list[i]
                conn = httplib.HTTPConnection("csys.cycu.edu.tw")
                params = urllib.urlencode({ 'cmd': 'addSelection', 'op_code':tmp_op_code})
                headers = { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                            "Cookie": str_JSESSIONID+"; "+str_NSC_dtzt,     
                            "Page-Id": str_pageId}     
                conn.request("POST", "/student/student/op/StudentCourseView.srv", params, headers)                       
                r2 = conn.getresponse() 
                # #print r2.status, r2.reason   
                data = r2.read()
                conn.close() 

                result = json.loads(data)['result']
                sys.stdout.write("[%s] add Selection: %s, result: %s\r" % (circle[cir_cnt%4], tmp_op_code, result) )    
                sys.stdout.flush()
                cir_cnt += 1

                # release version sleep 0.5
                time.sleep( 0.5 ) 

                # if true remove tack list
                if ( result == 'true' ) :
                    insert_list.remove(tmp_op_code)
                    break
    except KeyboardInterrupt:
        pass                                                                                                 
    except:
       print("[*] Error! someting error")           

#======================================================
def logout():
    # logout
    conn = httplib.HTTPConnection("csys.cycu.edu.tw")
    params = urllib.urlencode({ 'cmd': 'logout'})
    headers = { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Cookie": str_JSESSIONID+"; "+str_NSC_dtzt  }        
    conn.request("POST", "/student/sso.srv", params, headers)
    r2 = conn.getresponse()
    #print r2.status, r2.reason
    data = r2.read() 
    conn.close      
    print "\r\nlogout succes, bye"


#================================================================

#================================================================    
def main():
    codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)
    process = os.popen("chcp 65001")

    urllib3.disable_warnings()
    logging.captureWarnings(True)

    global str_username, str_password 
    str_username = raw_input("Username: ")
    str_password = raw_input("Password: ")
   
    print "\n[*] Version: 1.0"
    print "[*] Author: sirius / sirius.tsou@gmail.com"
    print "[*] Add Course from Track lit"           
    print "\n[*] Ussage"
    print "ctrl+c to exit program."

    print "[*] Iint cookie"
    init_Cookie()
    # print str_JSESSIONID+" ,"+str_NSC_dtzt

    print "\n[*] Iint Login, get secureRandom and generate hash"
    init_Login()
    # print str_hash

    print "\n[*] login and get pageId"
    login()

    #===== optional function =====

    #===== start fuck Course =====
    try:
        print "\n[*] get CourseId by student insert list"
        list_Opcode = get_Opcode()
        print "\n[*] run addSelection post"            
        fuck_course(list_Opcode)                      
    except:
        pass    
    #===== end fuck Course =====

    logout()

    os.system("pause")
    os.system("chcp 950")
    process.close() 
    print "\n[*] logout"
if __name__ == "__main__":
    freeze_support()
    main()   
#=================================================================

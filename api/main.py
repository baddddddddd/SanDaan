import pymysql
from app import app
from config import mysql
from flask import jsonify
from flask import flash, request

@app.route('/create', methods=['POST'])
def create_emp():
    try:        
        _json = request.json
        _email = _json['email']
        _user = _json['user_db']
        _pswd = _json['pswd_db']
        if _email and _user and _pswd and request.method == 'POST':
            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)		
            sqlQuery = "INSERT INTO emp(email, user_db, pswd_db) VALUES(%s, %s, %s)"
            bindData = (_email, _user, _pswd)            
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            respone = jsonify('Account added succesfully!')
            respone.status_code = 200
            return respone
        else:
            return showMessage()
    except Exception as e:
        print(e)
    finally:
        cursor.close() 
        conn.close()          
     
@app.route('/emp')
def emp():
    try:
        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT email, user_db, pwsd_db FROM emp")
        empRows = cursor.fetchall()
        respone = jsonify(empRows)
        respone.status_code = 200
        return respone
    except Exception as e:
        print(e)
    finally:
        cursor.close() 
        conn.close()  
        
@app.route('/update', methods=['PUT'])
def update_emp():
    try:
        _json = request.json
        _email = _json['email']
        _user = _json['user_db']
        _pswd = _json['pswd_db']
        if _email and _user and _pswd and request.method == 'PUT':			
            sqlQuery = "UPDATE emp SET email=%s, user_db=%s, pwsd_db=%s"
            bindData = (_email, _user, _pswd)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            respone = jsonify('Nice!')
            respone.status_code = 200
            return respone
        else:
            return showMessage()
    except Exception as e:
        print(e)
    finally:
        cursor.close() 
        conn.close() 

@app.route('/delete/<int:email>', methods=['DELETE'])
def delete_emp(email):
	try:
		conn = mysql.connect()
		cursor = conn.cursor()
		cursor.execute("DELETE FROM emp WHERE email =%s", (email,))
		conn.commit()
		respone = jsonify('Account deleted successfully!')
		respone.status_code = 200
		return respone
	except Exception as e:
		print(e)
	finally:
		cursor.close() 
		conn.close()
        
       
@app.errorhandler(404)
def showMessage(error=None):
    message = {
        'status': 404,
        'message': 'Record not found: ' + request.url,
    }
    respone = jsonify(message)
    respone.status_code = 404
    return respone
        
if __name__ == "__main__":
    app.run()
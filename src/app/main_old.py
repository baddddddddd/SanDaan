from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
import mysql.connector
import bcrypt

Window.size = (310, 580)


class MainApp(MDApp):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="admin", 
        database="sandaan"  
    )

    cursor = db.cursor()

    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(Builder.load_file("main.kv"))
        screen_manager.add_widget(Builder.load_file("signup.kv"))
        screen_manager.add_widget(Builder.load_file("login.kv"))
        return screen_manager
    

    def verify_login(self, username: TextInput, password: TextInput):
        login_data = (username.text, username.text)
        query = "SELECT * FROM users WHERE username=%s OR email=%s"
        
        self.cursor.execute(query, login_data)
        user = self.cursor.fetchone()

        is_logged_in = False
        if user is not None:
            hashed_pw = user[2]
            
            is_logged_in = bcrypt.checkpw(password.text.encode("utf-8"), hashed_pw.encode("ascii"))


        if is_logged_in:
            print("LOGGED IN SUCCESSFULLY")
        else:
            print("INCORRECT USERNAME OR PASSWORD")


    def create_account(self, username: TextInput, email: TextInput, password: TextInput, confirm_password: TextInput):
        self.cursor.execute("SELECT * FROM users WHERE username=%s", (username.text,))
        result = self.cursor.fetchone()

        if result is not None:
            print("That username is already taken")
            return False
        
        self.cursor.execute("SELECT * FROM users WHERE email=%s", (email.text,))
        result = self.cursor.fetchone()

        if result is not None:
            print("There is already an account with that email")
            return False
        
        # Adding the salt to password
        salt = bcrypt.gensalt()

        # Hashing the password
        hashed_pw = bcrypt.hashpw(password.text.encode("utf-8"), salt)
        
        login_data = (username.text, email.text, hashed_pw)
        query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        self.cursor.execute(query, login_data)
        self.db.commit()

        print("REGISTERED SUCCESSFULLY")

        return True
    

if __name__ == "__main__":
    LabelBase.register(name="MPoppins", fn_regular=r"fonts\Poppins\Poppins-Medium.ttf")
    LabelBase.register(name="BPoppins", fn_regular=r"fonts\Poppins\Poppins-SemiBold.ttf")

    MainApp().run()
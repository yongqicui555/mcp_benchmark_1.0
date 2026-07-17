#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# =============================================================================
# Authenticator
# =============================================================================
class Authenticator:
    def __init__(self):
        load_dotenv() 
        self.username = os.getenv('USERNAME')
        self.password = os.getenv('PASSWORD')
        if not self.username or not self.password:
            raise ValueError("請在 .env 檔案中設定 USERNAME 與 PASSWORD 環境變數。")
        self.session = requests.Session()
        self.session.headers.update({'Referer': 'https://iclass.tku.edu.tw/'})
        self.auth_url = (
            "https://sso.tku.edu.tw/auth/realms/TKU/protocol/openid-connect/auth"
            "?client_id=pdsiclass&response_type=code&redirect_uri=https%3A//iclass.tku.edu.tw/login"
            "&state=L2lwb3J0YWw=&scope=openid,public_profile,email"
        )
    
    def perform_auth(self):
        try:
            self.session.get("https://iclass.tku.edu.tw/login?next=/iportal&locale=zh_TW")
            self.session.get(self.auth_url)
            login_page_url = f"https://sso.tku.edu.tw/NEAI/logineb.jsp?myurl={self.auth_url}"
            login_page = self.session.get(login_page_url)
            jsessionid = login_page.cookies.get("AMWEBJCT!%2FNEAI!JSESSIONID")
            if not jsessionid:
                raise ValueError("無法取得 JSESSIONID")
            
            image_headers = {
                'Referer': 'https://sso.tku.edu.tw/NEAI/logineb.jsp',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
            }
            self.session.get("https://sso.tku.edu.tw/NEAI/ImageValidate", headers=image_headers)
            post_headers = {
                'Origin': 'https://sso.tku.edu.tw',
                'Referer': 'https://sso.tku.edu.tw/NEAI/logineb.jsp'
            }
            body = {'outType': '2'}
            response = self.session.post("https://sso.tku.edu.tw/NEAI/ImageValidate", headers=post_headers, data=body)
            vidcode = response.text.strip()
            
            payload = {
                "myurl": self.auth_url,
                "ln": "zh_TW",
                "embed": "No",
                "vkb": "No",
                "logintype": "logineb",
                "username": self.username,
                "password": self.password,
                "vidcode": vidcode,
                "loginbtn": "登入"
            }
            login_url = f"https://sso.tku.edu.tw/NEAI/login2.do;jsessionid={jsessionid}?action=EAI"
            self.session.post(login_url, data=payload)
            
            headers = {'Referer': login_url, 'Upgrade-Insecure-Requests': '1'}
            user_redirect_url = (
                f"https://sso.tku.edu.tw/NEAI/eaido.jsp?"
                f"am-eai-user-id={self.username}&am-eai-redir-url={self.auth_url}"
            )
            self.session.get(user_redirect_url, headers=headers)
            
            return self.session
        except requests.exceptions.RequestException as e:
            raise Exception("Authentication failed: " + str(e))

# =============================================================================
# TronClassAPI
# =============================================================================
class TronClassAPI:
    def __init__(self, session):
        self.session = session

    async def get_todos(self):
        todos_url = "https://iclass.tku.edu.tw/api/todos"
        try:
            response = self.session.get(todos_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching todos: {str(e)}"}
    
    async def get_bulletins(self):
        url = "https://iclass.tku.edu.tw/api/course-bulletins"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching bulletins: {str(e)}"}

    async def get_courses(self):
        url = 'https://iclass.tku.edu.tw/api/my-courses?conditions=%7B%22status%22:%5B%22ongoing%22%5D,%22keyword%22:%22%22,%22classify_type%22:%22recently_started%22,%22display_studio_list%22:false%7D&fields=id,name,course_code,department(id,name),grade(id,name),klass(id,name),course_type,cover,small_cover,start_date,end_date,is_started,is_closed,academic_year_id,semester_id,credit,compulsory,second_name,display_name,created_user(id,name),org(is_enterprise_or_organization),org_id,public_scope,audit_status,audit_remark,can_withdraw_course,imported_from,allow_clone,is_instructor,is_team_teaching,is_default_course_cover,archived,instructors(id,name,email,avatar_small_url),course_attributes(teaching_class_name,is_during_publish_period,passing_score,score_type,copy_status,tip,data,graduate_method),user_stick_course_record(id)&page=1&page_size=10&showScorePassedStatus=true?'
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error fetching courses: {str(e)}"}

# =============================================================================
# MCP Server
# =============================================================================
mcp = FastMCP(
    "TKU-MCP",
    description="TronClass and TKU-ilife integration through the Model Context Protocol",
)

@mcp.tool()
async def getToDo():
    """
    Get the list of todos from TronClass
    """
    try:
        auth = Authenticator()
        session = auth.perform_auth()
        api = TronClassAPI(session)
        todos = await api.get_todos()
        return todos
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def getBulletins():
    """
    Get the list of bulletins from TronClass
    """
    try:
        auth = Authenticator()
        session = auth.perform_auth()
        api = TronClassAPI(session)
        bulletins = await api.get_bulletins()
        return bulletins
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def getCourses():
    """
    Get the list of courses from TronClass
    """
    try:
        auth = Authenticator()
        session = auth.perform_auth()
        api = TronClassAPI(session)
        courses = await api.get_courses()
        return courses
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')

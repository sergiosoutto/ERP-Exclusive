import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_cookie = "cookie_manager = stx.CookieManager()"
new_cookie = """@st.cache_resource(show_spinner=False, experimental_allow_widgets=True)
def get_cookie_manager():
    return stx.CookieManager(key="global_cookie_manager")

cookie_manager = get_cookie_manager()"""

content = content.replace(old_cookie, new_cookie)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed CookieManager mounting delay")

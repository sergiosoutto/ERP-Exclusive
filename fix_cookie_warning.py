import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the CookieManager initialization with the monkey-patched cache version
old_cookie = 'cookie_manager = stx.CookieManager(key="global_cookie_manager")'

new_cookie = """# Suppress CachedWidgetWarning for CookieManager
try:
    from streamlit.elements.lib import policies
    policies.check_cache_replay_rules = lambda *args, **kwargs: None
except:
    pass

@st.cache_resource(show_spinner=False)
def get_cookie_manager():
    return stx.CookieManager(key="global_cookie_manager")

cookie_manager = get_cookie_manager()"""

content = content.replace(old_cookie, new_cookie)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Monkey-patched Streamlit warning and restored cached CookieManager")

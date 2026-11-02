import os, requests, pandas as pd, streamlit as st, plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
API=os.getenv('API_URL','http://localhost:8000').rstrip('/')
st.set_page_config(page_title='CRM Specialist',page_icon='🎧',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
:root { --crm-primary:#009DA5; --crm-primary-hover:#007D85; --crm-soft:#E6F7F7; --crm-bg:#F7FBFB; --crm-border:#DDEAEA; --crm-text:#17324D; }
.stApp, [data-testid="stAppViewContainer"] { background:var(--crm-bg); color:var(--crm-text); }
[data-testid="stSidebar"] { background:#FFFFFF; border-right:1px solid var(--crm-border); }
/* Streamlit button internals vary by release: align at button AND nested content layers. */
[data-testid="stSidebar"] div.stButton { width:100%; }
[data-testid="stSidebar"] div.stButton > button,
[data-testid="stSidebar"] div.stButton button {
 width:100%!important; display:flex!important; flex-direction:row!important;
 justify-content:flex-start!important; align-items:center!important;
 text-align:left!important; padding:0.7rem 0.85rem!important;
 border:1px solid transparent!important; border-radius:10px!important;
 background:transparent!important; color:var(--crm-text)!important;
 font-weight:500!important; box-shadow:none!important;
}
[data-testid="stSidebar"] div.stButton button > div,
[data-testid="stSidebar"] div.stButton button > span,
[data-testid="stSidebar"] div.stButton button p,
[data-testid="stSidebar"] div.stButton button [data-testid="stMarkdownContainer"] {
 text-align:left!important; justify-content:flex-start!important;
 margin-left:0!important; margin-right:auto!important;
}
[data-testid="stSidebar"] div.stButton button:hover {background:var(--crm-soft)!important;color:var(--crm-primary-hover)!important;}
[data-testid="stSidebar"] div.stButton button:focus-visible {outline:2px solid var(--crm-primary)!important;outline-offset:2px;}
/* Selected navigation is keyed to its Streamlit button container. */
[data-testid="stSidebar"] div.st-key-nav_Dashboard button:focus,
[data-testid="stSidebar"] div.stButton button:active {border-color:var(--crm-primary)!important;}
[data-testid="stSidebar"] .crm-nav-active button {background:var(--crm-soft)!important;color:var(--crm-primary-hover)!important;font-weight:700!important;}
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
 background:var(--crm-primary)!important;border-color:var(--crm-primary)!important;
 color:#FFFFFF!important;border-radius:10px!important;
}
.stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {background:var(--crm-primary-hover)!important;border-color:var(--crm-primary-hover)!important;}
.stButton button:not([kind="primary"]):not(:disabled):hover,
.stFormSubmitButton button:not([kind="primary"]):not(:disabled):hover {border-color:var(--crm-primary)!important;color:var(--crm-primary-hover)!important;background:var(--crm-soft)!important;}
button:focus-visible, input:focus-visible, textarea:focus-visible {outline-color:var(--crm-primary)!important;}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within,
[data-baseweb="select"]:focus-within {border-color:var(--crm-primary)!important;box-shadow:0 0 0 1px var(--crm-primary)!important;}
[data-baseweb="tab-list"] button[aria-selected="true"] {color:var(--crm-primary-hover)!important;border-bottom-color:var(--crm-primary)!important;}
[data-baseweb="tab-highlight"] {background:var(--crm-primary)!important;}
[data-testid="stProgress"] [role="progressbar"] > div {background:var(--crm-primary)!important;}
div[data-testid="stMetric"] {background:#fff;border:1px solid var(--crm-border);border-radius:14px;padding:18px;box-shadow:0 3px 16px #17324D0B;}
div[data-testid="stVerticalBlockBorderWrapper"]>div {border-color:var(--crm-border)!important;border-radius:14px!important;}
[data-testid="stDataFrame"] {border:1px solid var(--crm-border);border-radius:12px;}
h1,h2,h3 {letter-spacing:-.03em;color:var(--crm-text);} h1{font-size:2rem!important} h3{font-size:1.15rem!important}
[data-testid="stSidebar"] h2{font-size:1.3rem}.small-muted{color:#647C8A;font-size:.85rem}
a {color:var(--crm-primary-hover)} a:hover {color:var(--crm-primary)}

/* ChatGPT-like conversation alignment: customer right, assistant left. */
[data-testid="stChatMessage"] {
 width:fit-content!important; max-width:min(82%, 900px)!important;
 min-width:0!important; margin-bottom:1rem; border-radius:16px;
 padding:.75rem 1rem; border:1px solid #E2EEEE;
 box-shadow:0 2px 8px rgba(23,50,77,.035);
}
/* Bubble shrinks to its content, but long text wraps within the viewport. */
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
 flex:0 1 auto!important; min-width:0!important; width:auto!important;
 overflow-wrap:anywhere; word-break:normal;
}
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] > div {max-width:100%;}
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p {margin-bottom:.35rem;}
@media (max-width:700px) {
 [data-testid="stChatMessage"] {max-width:96%!important; padding:.7rem .8rem;}
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {margin-left:auto!important; margin-right:0!important; background:#E6F7F7!important; border-color:#C8E9E8!important;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {margin-left:0!important; margin-right:auto!important; background:#FFFFFF!important;}
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] p {line-height:1.65;}
/* Chat history and action buttons: consistent alignment and readable spacing. */
.st-key-chat_new_button button {min-height:2.6rem!important;}
[data-testid="stSpinner"] {background:#E6F7F7; border:1px solid #B8E1E0; border-radius:10px; padding:10px 14px; color:#007D85;}
[data-testid="stSpinner"] p {font-weight:600!important;color:#007D85!important;}

/* v23: Light-teal sidebar design, isolated from the main CRM content. */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
 background:#F4FBFA!important;
}
[data-testid="stSidebar"] {border-right:1px solid #D5EAE8!important;}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {padding-top:1.2rem!important;}
[data-testid="stSidebar"] .crm-sidebar-brand {
 display:flex;align-items:center;gap:12px;padding:12px 7px 22px;
 margin-bottom:20px;border-bottom:1px solid #DCEBE9;
}
[data-testid="stSidebar"] .crm-brand-icon {
 display:flex;align-items:center;justify-content:center;width:42px;height:42px;
 flex:0 0 42px;border-radius:13px;background:#D9F4F1;
 color:#007D85;font-size:22px;
}
[data-testid="stSidebar"] .crm-brand-name {font-size:16px;font-weight:750;color:#17324D;line-height:1.3;}
[data-testid="stSidebar"] .crm-brand-subtitle {font-size:11px;color:#718C95;margin-top:4px;}
[data-testid="stSidebar"] .crm-sidebar-label,
[data-testid="stSidebar"] .crm-sidebar-footer-label {
 font-size:10px;letter-spacing:1.4px;font-weight:750;color:#72939A;
 padding:0 12px;margin:0 0 10px;
}
[data-testid="stSidebar"] .crm-sidebar-footer-label {margin-top:28px;padding-top:20px;border-top:1px solid #DCEBE9;}
[data-testid="stSidebar"] div.stButton {margin:2px 0!important;}
[data-testid="stSidebar"] div.stButton button {
 min-height:43px!important;padding:10px 14px!important;
 border-radius:10px!important;font-size:13px!important;
 color:#28485A!important;background:transparent!important;
 transition:background-color .15s ease,border-color .15s ease!important;
}
[data-testid="stSidebar"] div.stButton button:hover {background:#E7F6F4!important;color:#007D85!important;}
[data-testid="stSidebar"] div.stButton button p {font-size:13px!important;font-weight:inherit!important;}
[data-testid="stSidebar"] .crm-sidebar-status {
 display:flex;align-items:center;gap:9px;padding:13px 12px;margin:0 2px;
 border-radius:10px;font-size:12px;font-weight:650;
}
[data-testid="stSidebar"] .crm-sidebar-status.online {background:#E2F6EA;color:#16734C;}
[data-testid="stSidebar"] .crm-sidebar-status.offline {background:#FFF0E9;color:#B74A27;}
[data-testid="stSidebar"] .crm-status-dot {width:8px;height:8px;border-radius:50%;background:currentColor;flex-shrink:0;}

/* v24 · ThreeUI-inspired light SaaS visual language; no backend changes. */
:root{--crm-shadow:0 10px 28px rgba(12,92,104,.075);--crm-ease:cubic-bezier(.2,.8,.2,1)}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse 48% 18% at 26% 0%,#D9F8F4 0%,transparent 100%),#F6FBFC!important}
[data-testid="stSidebar"], [data-testid="stSidebar"]>div,[data-testid="stSidebar"] [data-testid="stSidebarContent"]{background:linear-gradient(165deg,#F8FFFF 0%,#F0FBFA 70%,#E9F8F7 100%)!important}
[data-testid="stSidebar"]{box-shadow:3px 0 25px rgba(8,104,110,.04)}
[data-testid="stSidebar"] div.stButton button{transition:background .18s var(--crm-ease),transform .18s var(--crm-ease),box-shadow .18s var(--crm-ease),color .18s ease!important}
[data-testid="stSidebar"] div.stButton button:hover{transform:translateX(3px)!important;box-shadow:0 4px 14px rgba(0,157,165,.09)!important}
[data-testid="stSidebar"] .crm-brand-icon{background:linear-gradient(135deg,#D2F8F3,#C4ECFA)!important;box-shadow:0 6px 18px #009DA520}
[data-testid="stSidebar"] .crm-sidebar-status.online{box-shadow:0 5px 14px rgba(20,137,94,.08)}
.stButton button[kind="primary"],.stFormSubmitButton button[kind="primary"],button[data-testid="stBaseButton-primary"]{background:linear-gradient(115deg,#00B8AC,#009DA5 62%,#007D85)!important;border:1px solid #009DA5!important;box-shadow:0 6px 16px rgba(0,157,165,.18)!important;transition:transform .18s var(--crm-ease),box-shadow .18s var(--crm-ease),filter .18s ease!important}
.stButton button[kind="primary"]:hover,.stFormSubmitButton button[kind="primary"]:hover,button[data-testid="stBaseButton-primary"]:hover{filter:brightness(1.04);transform:translateY(-2px);box-shadow:0 10px 20px rgba(0,157,165,.25)!important}
.stButton button:not([kind="primary"]),.stFormSubmitButton button:not([kind="primary"]){border-radius:11px;transition:transform .18s var(--crm-ease),background .18s ease,border-color .18s ease!important}
.stButton button:not([kind="primary"]):hover,.stFormSubmitButton button:not([kind="primary"]):hover{transform:translateY(-1px)}
.stButton button:active,.stFormSubmitButton button:active{transform:translateY(0) scale(.99)!important}
[data-testid="stMetric"]{border:1px solid #DCEDEA!important;border-radius:18px!important;background:linear-gradient(145deg,#FFF,#FAFFFF)!important;box-shadow:var(--crm-shadow)!important;transition:transform .2s var(--crm-ease),box-shadow .2s ease!important}
[data-testid="stMetric"]:hover{transform:translateY(-3px);box-shadow:0 14px 32px rgba(12,92,104,.13)!important}
[data-testid="stMetricLabel"]{color:#526C7B!important;font-weight:650}
[data-testid="stMetricValue"]{color:#112B48!important;font-weight:750!important}
[data-testid="stVerticalBlockBorderWrapper"]:has(>div[data-testid="stVerticalBlock"]){border-radius:17px!important}
[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:17px!important}
[data-testid="stDataFrame"]{overflow:hidden;box-shadow:0 3px 12px #17324D08}
[data-testid="stMainBlockContainer"]{animation:crm-page-enter .26s var(--crm-ease) both}
@keyframes crm-page-enter{from{opacity:.35;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
[data-testid="stChatMessage"]{animation:crm-chat-enter .22s ease-out both}
@keyframes crm-chat-enter{from{opacity:.35;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
.crm-dashboard-kicker{color:#007D85;font-size:.8rem;font-weight:750;letter-spacing:.12em;margin:0 0 4px}
.crm-dashboard-subtitle{color:#6D8595;margin-top:-.45rem;margin-bottom:1.1rem;font-size:.92rem}
.crm-dashboard-banner{background:linear-gradient(105deg,#E2F9F5,#F7FFFF 65%,#EAF5FF);border:1px solid #D5EDEA;border-radius:16px;padding:16px 20px;margin-bottom:18px}
.crm-dashboard-banner h2{font-size:1.65rem!important;margin:0!important;color:#17324D}
.crm-dashboard-banner p{color:#657D8D;font-size:.9rem;margin:.35rem 0 0}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}

/* v25: interaction polish, responsive spacing, reduced-motion support */
[data-testid="stSidebar"] div.stButton button{transition:background .2s ease,transform .2s ease,box-shadow .2s ease!important}
[data-testid="stSidebar"] div.stButton button:hover{transform:translateX(3px)!important}
[data-testid="stSidebar"] .stButton button:active{transform:scale(.985)!important}
[data-testid="stMainBlockContainer"]{max-width:1600px;padding-top:1.4rem}
[data-testid="stVerticalBlockBorderWrapper"]{transition:box-shadow .2s ease,transform .2s ease}
[data-testid="stVerticalBlockBorderWrapper"]:hover{box-shadow:0 8px 22px rgba(0,110,118,.055)}
.st-key-crm_sidebar_toggle button{background:#E6F7F7!important;color:#007D85!important;border:1px solid #B7E5E3!important}
@media(max-width:950px){[data-testid="stMainBlockContainer"]{padding-left:1rem;padding-right:1rem}[data-testid="stMetric"]{padding:12px!important}}
@media(max-width:700px){[data-testid="stMainBlockContainer"]{padding-left:.65rem;padding-right:.65rem}[data-testid="stChatMessage"]{max-width:96%!important}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}

/* v26 Ticket Management workspace */
.crm-ticket-hint {padding:12px 16px;background:linear-gradient(110deg,#E5F9F6,#F4FBFF);border:1px solid #CDECE8;border-radius:12px;color:#426A75;margin:12px 0 20px;font-size:.92rem}
[data-baseweb="tab-list"] {gap:10px!important;border-bottom:1px solid #D9EBE9!important;padding-bottom:8px!important}
[data-baseweb="tab-list"] button {border-radius:11px 11px 5px 5px!important;padding:10px 18px!important;transition:background .18s ease,color .18s ease!important}
[data-baseweb="tab-list"] button[aria-selected="true"] {background:#E6F7F7!important;color:#007D85!important;font-weight:750!important}
@media(max-width:800px){.crm-ticket-hint{padding:10px 12px}[data-baseweb="tab-list"] button{padding:8px 10px!important}}

/* v29: ThreeUI-inspired BUTTON tabs for Ticket Management and Settings. */
[data-baseweb="tab-list"], [role="tablist"] {
  display:flex!important; flex-wrap:wrap!important; gap:10px!important;
  align-items:center!important; border-bottom:0!important;
  padding:6px 2px 12px!important; background:transparent!important;
}
[data-baseweb="tab-list"] button[role="tab"], [role="tablist"] button[role="tab"] {
  flex:0 0 auto!important; min-height:43px!important;
  padding:10px 17px!important; border-radius:12px!important;
  border:1px solid #D4E8E8!important;
  background:linear-gradient(145deg,#FFFFFF,#F7FCFC)!important;
  color:#28485A!important; font-weight:650!important;
  box-shadow:0 2px 8px rgba(13,86,95,.035)!important;
  transition:background .18s ease,box-shadow .18s ease,transform .18s ease,color .18s ease!important;
}
[data-baseweb="tab-list"] button[role="tab"]:hover, [role="tablist"] button[role="tab"]:hover {
  background:#E6F7F7!important; color:#007D85!important;
  border-color:#90D7D5!important; transform:translateY(-1px)!important;
  box-shadow:0 5px 14px rgba(0,157,165,.12)!important;
}
[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"], [role="tablist"] button[role="tab"][aria-selected="true"] {
  background:linear-gradient(115deg,#00B8AC,#009DA5 62%,#007D85)!important;
  border-color:#009DA5!important; color:#FFFFFF!important;
  box-shadow:0 6px 16px rgba(0,157,165,.22)!important;
}
[data-baseweb="tab-list"] button[role="tab"][aria-selected="true"] *, [role="tablist"] button[role="tab"][aria-selected="true"] * {color:#FFFFFF!important;}
[data-baseweb="tab-list"] button[role="tab"]:focus-visible, [role="tablist"] button[role="tab"]:focus-visible {
  outline:3px solid #65CECD!important; outline-offset:3px!important;
}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {display:none!important;}
/* Ticket and Settings tab panels retain their existing Streamlit behavior. */
@media(max-width:760px){
  [data-baseweb="tab-list"] button[role="tab"], [role="tablist"] button[role="tab"] {
    min-height:39px!important; padding:8px 11px!important; font-size:12px!important;
  }
  [data-baseweb="tab-list"], [role="tablist"] {gap:7px!important;}
}
@media(prefers-reduced-motion:reduce){[role="tablist"] button[role="tab"]{transition:none!important;transform:none!important}}


/* v30: target the actual BaseWeb tab element, not only button[role=tab]. */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  display:flex!important;flex-wrap:wrap!important;gap:10px!important;
  border-bottom:none!important;padding:7px 0 15px!important;
  background:transparent!important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  display:inline-flex!important;flex:0 0 auto!important;
  align-items:center!important;justify-content:center!important;
  padding:11px 17px!important;min-height:44px!important;
  border:1px solid #CFE5E4!important;border-radius:12px!important;
  background:#FFFFFF!important;color:#28485A!important;
  box-shadow:0 2px 9px rgba(12,92,104,.06)!important;
  font-weight:650!important;
  transition:background .18s ease,transform .18s ease,box-shadow .18s ease!important;
}
[data-testid="stTabs"] [data-baseweb="tab"] p,
[data-testid="stTabs"] [data-baseweb="tab"] span {color:inherit!important;font-weight:inherit!important;}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
  background:#E6F7F7!important;border-color:#8DD4D1!important;
  color:#007D85!important;transform:translateY(-2px)!important;
  box-shadow:0 6px 17px rgba(0,157,165,.12)!important;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
  background:linear-gradient(115deg,#00B8AC,#009DA5 65%,#007D85)!important;
  color:#FFFFFF!important;border-color:#009DA5!important;
  box-shadow:0 7px 18px rgba(0,157,165,.2)!important;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] * {color:#FFFFFF!important;}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] {display:none!important;}
[data-testid="stTabs"] [data-baseweb="tab"]:focus-visible {outline:3px solid #68D1CE!important;outline-offset:2px!important;}
@media(max-width:700px){[data-testid="stTabs"] [data-baseweb="tab"] {padding:9px 11px!important;font-size:12px!important;}}

/* v32: real segmented button widgets, not Streamlit native st.tabs links. */
[data-testid="stSegmentedControl"] [role="radiogroup"],
[data-testid="stSegmentedControl"] > div {gap:8px!important;flex-wrap:wrap!important;}
[data-testid="stSegmentedControl"] button,
[data-testid="stSegmentedControl"] [role="radio"],
[data-testid="stSegmentedControl"] label {
  border:1px solid #CFE5E4!important;border-radius:12px!important;
  background:#FFFFFF!important;color:#28485A!important;
  min-height:43px!important;padding:9px 15px!important;
  box-shadow:0 3px 12px rgba(12,92,104,.06)!important;
  transition:background .18s ease,transform .18s ease,box-shadow .18s ease!important;
}
[data-testid="stSegmentedControl"] button:hover,
[data-testid="stSegmentedControl"] [role="radio"]:hover,
[data-testid="stSegmentedControl"] label:hover {background:#E6F7F7!important;transform:translateY(-1px)!important;}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[aria-pressed="true"],
[data-testid="stSegmentedControl"] [role="radio"][aria-checked="true"],
[data-testid="stSegmentedControl"] label:has(input:checked) {
  background:linear-gradient(110deg,#00B8AC,#009DA5 65%,#007D85)!important;
  border-color:#009DA5!important;color:#FFFFFF!important;
  box-shadow:0 6px 16px rgba(0,157,165,.20)!important;
}
[data-testid="stSegmentedControl"] [aria-checked="true"] *,
[data-testid="stSegmentedControl"] [aria-pressed="true"] *,
[data-testid="stSegmentedControl"] label:has(input:checked) * {color:#FFFFFF!important;}
@media(max-width:720px){[data-testid="stSegmentedControl"] button,[data-testid="stSegmentedControl"] label{font-size:12px!important;padding:8px 10px!important;}}

/* v33: Theme-consistent pill buttons for both Ticket Management and Settings.
   Supports Streamlit segmented controls implemented as buttons or radio labels. */
[data-testid="stSegmentedControl"] {margin:12px 0 18px!important;}
[data-testid="stSegmentedControl"] [role="radiogroup"] {display:flex!important;gap:9px!important;flex-wrap:wrap!important;background:transparent!important;border:0!important;}
[data-testid="stSegmentedControl"] button,
[data-testid="stSegmentedControl"] [role="radio"],
[data-testid="stSegmentedControl"] label {
  min-height:44px!important;padding:10px 17px!important;
  border:1px solid #CDE5E4!important;border-radius:12px!important;
  background:#FFFFFF!important;color:#28485A!important;
  box-shadow:0 3px 10px rgba(12,92,104,.06)!important;
  font-weight:650!important;cursor:pointer!important;
  transition:background .18s ease,transform .18s ease,box-shadow .18s ease!important;
}
[data-testid="stSegmentedControl"] button:hover,
[data-testid="stSegmentedControl"] [role="radio"]:hover,
[data-testid="stSegmentedControl"] label:hover {
  background:#E6F7F7!important;color:#007D85!important;
  border-color:#80CECC!important;transform:translateY(-1px)!important;
}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[aria-pressed="true"],
[data-testid="stSegmentedControl"] button[data-state="active"],
[data-testid="stSegmentedControl"] [role="radio"][aria-checked="true"],
[data-testid="stSegmentedControl"] label:has(input:checked) {
  background:linear-gradient(115deg,#00B8AC,#009DA5 65%,#007D85)!important;
  color:#FFFFFF!important;border-color:#009DA5!important;
  box-shadow:0 6px 17px rgba(0,157,165,.22)!important;
}
[data-testid="stSegmentedControl"] :is(button[aria-checked="true"],button[aria-pressed="true"],button[data-state="active"],[role="radio"][aria-checked="true"],label:has(input:checked)) * {color:#FFFFFF!important;}
[data-testid="stSegmentedControl"] :is(button,label,[role="radio"]):focus-visible {outline:3px solid #67D3D0!important;outline-offset:2px!important;}
@media(max-width:760px){[data-testid="stSegmentedControl"] :is(button,label,[role="radio"]){padding:8px 11px!important;min-height:40px!important;font-size:12px!important;}}
@media(prefers-reduced-motion:reduce){[data-testid="stSegmentedControl"] :is(button,label,[role="radio"]){transition:none!important;transform:none!important;}}

/* v34: actual Streamlit button tabs. No dependence on segmented-control DOM. */
.st-key-crm_tm_tabs button, .st-key-crm_settings_tabs button {
 min-height:35px!important;border-radius:9px!important;padding:6px 12px!important;font-size:12px!important;
 background:#FFFFFF!important;border:1px solid #CDE5E4!important;
 color:#28485A!important;font-weight:650!important;
 box-shadow:0 3px 10px rgba(12,92,104,.06)!important;
 transition:background .18s ease,transform .18s ease,box-shadow .18s ease!important;
 white-space:normal!important;
}
.st-key-crm_tm_tabs button:hover, .st-key-crm_settings_tabs button:hover {
 background:#E6F7F7!important;border-color:#80CECC!important;color:#007D85!important;
 transform:translateY(-1px)!important;
}
.st-key-crm_tm_tabs button[kind="primary"], .st-key-crm_settings_tabs button[kind="primary"],
.st-key-crm_tm_tabs button[data-testid="stBaseButton-primary"],
.st-key-crm_settings_tabs button[data-testid="stBaseButton-primary"] {
 background:linear-gradient(115deg,#00B8AC,#009DA5 65%,#007D85)!important;
 color:#FFFFFF!important;border-color:#009DA5!important;
 box-shadow:0 6px 17px rgba(0,157,165,.22)!important;
}
.st-key-crm_tm_tabs button[kind="primary"] *, .st-key-crm_settings_tabs button[kind="primary"] * {color:#FFFFFF!important;}
.st-key-crm_tm_tabs button:focus-visible,.st-key-crm_settings_tabs button:focus-visible {outline:3px solid #67D3D0!important;outline-offset:2px!important;}
@media(max-width:850px){.st-key-crm_tm_tabs button,.st-key-crm_settings_tabs button{font-size:12px!important;padding:8px!important;}}

/* v37: compact, left-clustered navigation buttons. Streamlit columns use
   stColumn (not `column`) in current releases. Avoid distributing buttons. */
.st-key-crm_tm_tabs [data-testid="stHorizontalBlock"],
.st-key-crm_settings_tabs [data-testid="stHorizontalBlock"] {
  justify-content:flex-start!important;
  column-gap:7px!important;
  row-gap:7px!important;
  flex-wrap:wrap!important;
  align-items:center!important;
}
.st-key-crm_tm_tabs [data-testid="stColumn"],
.st-key-crm_settings_tabs [data-testid="stColumn"] {
  flex:0 0 auto!important;
  width:max-content!important;
  min-width:0!important;
  max-width:100%!important;
}
.st-key-crm_tm_tabs [data-testid="stButton"],
.st-key-crm_settings_tabs [data-testid="stButton"] {width:max-content!important;}
.st-key-crm_tm_tabs button,
.st-key-crm_settings_tabs button {
  width:max-content!important;
  white-space:nowrap!important;
  min-height:34px!important;
  padding:6px 11px!important;
  font-size:12px!important;
}
@media(max-width:760px) {
  .st-key-crm_tm_tabs [data-testid="stHorizontalBlock"],
  .st-key-crm_settings_tabs [data-testid="stHorizontalBlock"] {column-gap:6px!important;row-gap:8px!important;}
}
/* Compact ticket and settings buttons: no equal-width full-row stretching. */
.st-key-crm_tm_tabs [data-testid="stButton"],.st-key-crm_settings_tabs [data-testid="stButton"]{width:auto!important;}
.st-key-crm_tm_tabs button,.st-key-crm_settings_tabs button{width:auto!important;min-width:0!important;min-height:35px!important;padding:6px 12px!important;font-size:12px!important;border-radius:9px!important;}
.st-key-crm_tm_tabs [data-testid="stHorizontalBlock"],.st-key-crm_settings_tabs [data-testid="stHorizontalBlock"]{justify-content:flex-start!important;gap:8px!important;flex-wrap:wrap!important;}
.st-key-crm_tm_tabs [data-testid="column"],.st-key-crm_settings_tabs [data-testid="column"]{flex:0 0 auto!important;width:auto!important;min-width:0!important;}

/* v38: stable teal buttons, compact natural widths, consistent spacing */
.st-key-crm_tm_tabs [data-testid="stHorizontalBlock"],
.st-key-crm_settings_tabs [data-testid="stHorizontalBlock"] {
  justify-content:flex-start!important; gap:7px!important; flex-wrap:wrap!important;
}
.st-key-crm_tm_tabs [data-testid="stColumn"],
.st-key-crm_settings_tabs [data-testid="stColumn"] {
  flex:0 0 auto!important; width:max-content!important; min-width:0!important;
}
.st-key-crm_tm_tabs button,
.st-key-crm_settings_tabs button {
  min-height:34px!important; width:max-content!important; padding:6px 12px!important;
  border-radius:9px!important; font-size:12px!important;
  border:1px solid #CDE5E4!important; background:#FFFFFF!important;
  color:#28485A!important; box-shadow:0 2px 7px rgba(23,50,77,.04)!important;
  transition:background .17s ease,transform .17s ease,box-shadow .17s ease!important;
}
.st-key-crm_tm_tabs button:hover,
.st-key-crm_settings_tabs button:hover {
  background:#E6F7F7!important; border-color:#009DA5!important;
  transform:translateY(-1px)!important;
}
.st-key-crm_tm_tabs button[kind="primary"],
.st-key-crm_settings_tabs button[kind="primary"],
.st-key-crm_tm_tabs button[data-testid="stBaseButton-primary"],
.st-key-crm_settings_tabs button[data-testid="stBaseButton-primary"] {
  background:linear-gradient(110deg,#00B8B5,#007D85)!important;
  color:#FFFFFF!important; border-color:#009DA5!important;
  box-shadow:0 5px 12px rgba(0,157,165,.16)!important;
}
.st-key-crm_tm_tabs button[kind="primary"] *,
.st-key-crm_settings_tabs button[kind="primary"] * {color:#FFFFFF!important;}
@media(prefers-reduced-motion:reduce) {
  .st-key-crm_tm_tabs button,.st-key-crm_settings_tabs button {transition:none!important;transform:none!important;}
}
</style>''',unsafe_allow_html=True)

# Only the four evaluation agents appear in the customer-facing execution journey.
# GroundingValidator and ToolVerification remain in backend audit data, not this UI.
def render_agent_journey(turn):
    ordered = ('QueryAgent', 'KnowledgeAgent', 'ResolutionAgent', 'LogAgent')
    descriptions = {
        'QueryAgent': ('01', 'Understand the request', 'Classifies the message and determines its urgency.'),
        'KnowledgeAgent': ('02', 'Find approved knowledge', 'Searches the knowledge base and identifies relevant documents.'),
        'ResolutionAgent': ('03', 'Prepare the answer', 'Uses retrieved evidence to prepare a customer-facing response.'),
        'LogAgent': ('04', 'Record and route', 'Records the request and determines whether escalation is needed.'),
    }
    stages = {s.get('agent'): s for s in turn.get('agent_process', []) if s.get('agent') in ordered}
    with st.expander('🧭 How your request was processed · 4 agents', expanded=False):
        st.caption('Four stages · In order · Internal validation and tool diagnostics are hidden from this view')
        for name in ordered:
            number, title, purpose = descriptions[name]
            stage = stages.get(name)
            detail = (stage or {}).get('detail') or {}
            if not isinstance(detail, dict):
                detail = {'detail': str(detail)}
            ms = (stage or {}).get('duration_ms')
            duration = f'{ms / 1000:.2f}s' if isinstance(ms, (int, float)) and ms > 0 else 'Not recorded'
            with st.container(border=True):
                header, meta = st.columns([4, 1], vertical_alignment='center')
                with header:
                    st.markdown(f'**{number} · {name}**  — {title}')
                with meta:
                    if stage:
                        st.markdown(':green[● Completed]')
                    else:
                        st.markdown(':gray[● Not recorded]')
                st.caption(purpose)
                if name == 'QueryAgent':
                    a, b, c = st.columns(3)
                    a.markdown('**Category**')
                    a.write(detail.get('category') or turn.get('category') or 'Not available')
                    b.markdown('**Urgency**')
                    urgency = detail.get('urgency') or turn.get('urgency') or 'Unknown'
                    b.write(('🔴 ' if urgency == 'High' else '🟠 ' if urgency == 'Medium' else '🟢 ') + str(urgency))
                    c.markdown('**Sentiment**')
                    c.write(detail.get('sentiment') or 'Not recorded')
                    if detail.get('summary'):
                        st.markdown('**Request summary**')
                        st.write(detail['summary'])
                elif name == 'KnowledgeAgent':
                    sources = detail.get('sources') or turn.get('sources') or []
                    if isinstance(sources, str): sources = [sources] if sources else []
                    passage_count = detail.get('passages')
                    st.markdown('**Knowledge retrieved**')
                    st.write(f"{passage_count} matching passage(s)" if passage_count is not None else 'Passage count not recorded')
                    st.caption('Sources: ' + (', '.join(map(str, sources)) if sources else 'No matching approved documents'))
                elif name == 'ResolutionAgent':
                    st.markdown('**Outcome**')
                    if turn.get('sources'):
                        st.write('Response prepared using retrieved knowledge. See the answer and citations above.')
                    else:
                        st.write('No matching approved source was identified; the response should not invent policy details.')
                    if detail.get('confidence') is not None:
                        st.caption(f"Grounding confidence: {detail['confidence']}")
                else:
                    st.markdown('**Audit and ticket status**')
                    st.write('Request processed and recorded in the audit workflow.' if stage else 'No agent audit stage was recorded.')
                    if turn.get('ticket_id'):
                        st.caption(f"Support ticket: {turn['ticket_id']}")
                    else:
                        st.caption('No support ticket created · Waiting for customer feedback')
                st.caption('Processing time: ' + duration)

CRM_CHART_COLORS=['#009DA5','#4D7CFE','#F59E43','#A56DE2','#2BBFAF','#EF668B','#E8C54B']
def crm_chart(fig):
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
        font=dict(color='#17324D'),colorway=CRM_CHART_COLORS,
        margin=dict(l=12,r=12,t=48,b=12),
        legend=dict(font=dict(color='#17324D')),
    )
    fig.update_xaxes(gridcolor='#E8F1F1',zerolinecolor='#E8F1F1')
    fig.update_yaxes(gridcolor='#E8F1F1',zerolinecolor='#E8F1F1')
    return fig

# Cache read-only API responses across Streamlit reruns. Writes always bypass cache.
# Short TTL ensures ticket, chat and notification data remains reasonably fresh.
@st.cache_data(ttl=10, show_spinner=False, max_entries=150)
def _cached_get(api_url, path, params_key):
    import json
    params = json.loads(params_key) if params_key else None
    r = requests.get(api_url + path, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=10, show_spinner=False)
def _health_ok(api_url):
    try:
        return requests.get(api_url + '/health', timeout=2).ok
    except requests.RequestException:
        return False

def req(path,method='get',**kwargs):
    import json
    try:
        if method.lower() == 'get' and not any(k in kwargs for k in ('json', 'data', 'files', 'headers')):
            params_key = json.dumps(kwargs.get('params') or {}, sort_keys=True, default=str)
            return _cached_get(API, path, params_key)
        # The calling page owns its progress indicator: avoid nested loaders.
        r = requests.request(method, API + path, timeout=90, **kwargs)
        r.raise_for_status()
        if method.lower() != 'get':
            _cached_get.clear()
        return r.json() if r.content else {}
    except requests.RequestException as exc:
        st.error(f'API request failed: {exc}')
        return None

def heading(title,subtitle):
    st.title(title); st.caption(subtitle)

def table(rows):
    if not rows: st.info('No records yet.'); return
    keys=['ticket_id','customer_name','order_id','summary','category','urgency','status']
    df=pd.DataFrame(rows); st.dataframe(df[[k for k in keys if k in df.columns]],hide_index=True,use_container_width=True)

nav=[('🏠','Dashboard'),('💬','AI Support Chat'),('🎫','Ticket Management'),('📊','Analytics'),('✉️','Notifications'),('⚙️','Settings')]
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'

def _go_to_page(destination):
    st.session_state.page = destination

def crm_button_tabs(group, options, state_key, columns=2):
    """Render real theme-aware buttons; preserve selection across Streamlit reruns."""
    if st.session_state.get(state_key) not in options:
        st.session_state[state_key] = options[0]
    # CSS targets this stable keyed container and button kinds (primary/secondary).
    with st.container(key=f'crm_{group}_tabs'):
        # Give the buttons compact intrinsic-width columns rather than distributing
        # seven equal columns across the entire Settings page.
        if group == 'settings':
            weights = [1.05, 1.60, 1.45, 1.60, 1.65, 2.15, 1.60, 3.0]
            slots = st.columns(weights, gap='small')
        else:
            slots = st.columns([1.25, 1.65, 7.1], gap='small')
        for idx, label in enumerate(options):
            with slots[idx]:
                if st.button(label, key=f'{group}_tab_{idx}', use_container_width=False,
                             type='primary' if st.session_state[state_key] == label else 'secondary'):
                    st.session_state[state_key] = label
                    st.rerun()
    return st.session_state[state_key]

if 'crm_sidebar_compact' not in st.session_state:
    st.session_state.crm_sidebar_compact = False

# Compact mode changes the actual sidebar width, not just the labels.
# CSS-only tooltips stay available on hover and keyboard focus.
compact = st.session_state.crm_sidebar_compact
sidebar_width = '84px' if compact else '272px'
# Native Streamlit tooltip is more reliable than CSS pseudo-elements,
# which can be clipped by sidebar portals and stacking contexts.
nav_tooltips = []
st.markdown(f"""<style>
[data-testid="stSidebar"] {{
    width:{sidebar_width}!important; min-width:{sidebar_width}!important;
    max-width:{sidebar_width}!important; flex-basis:{sidebar_width}!important;
    transition:width .22s ease,min-width .22s ease,max-width .22s ease!important;
}}
/* Hide the built-in sidebar chevron: our single custom toggle controls compact mode. */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {{display:none!important;}}
[data-testid="stSidebar"] button[aria-label="Close sidebar"],
[data-testid="stSidebar"] button[aria-label="Collapse sidebar"] {{display:none!important;}}
/* Keep the toggle top-right, rather than showing a second full-width navigation item. */
[data-testid="stSidebar"] .st-key-crm_sidebar_toggle {{display:flex!important;justify-content:flex-end!important;margin:0 0 10px!important;}}
[data-testid="stSidebar"] .st-key-crm_sidebar_toggle button {{
 width:38px!important;min-width:38px!important;max-width:38px!important;
 min-height:36px!important;padding:6px!important;justify-content:center!important;
 background:transparent!important;border:1px solid transparent!important;
 font-size:21px!important;color:#007D85!important;
}}
[data-testid="stSidebar"] .st-key-crm_sidebar_toggle button:hover {{background:#E6F7F7!important;border-color:#B7E5E3!important;}}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
    padding-left:{'10px' if compact else '16px'}!important;
    padding-right:{'10px' if compact else '16px'}!important;
}}
{''.join(nav_tooltips)}

{('[data-testid="stSidebar"] div.stButton:not(.st-key-crm_sidebar_toggle) button {justify-content:center!important;text-align:center!important;padding:10px 4px!important;}' if compact else '')}
{('[data-testid="stSidebar"] div.stButton:not(.st-key-crm_sidebar_toggle) button p {text-align:center!important;margin:auto!important;font-size:20px!important;}' if compact else '')}
{('[data-testid="stSidebar"] .st-key-crm_sidebar_toggle button {min-height:40px!important;font-size:20px!important;}' if compact else '')}
{('[data-testid="stSidebar"] .crm-sidebar-status {justify-content:center!important;padding:12px 4px!important;}' if compact else '')}
/* Raise the rail ABOVE the page: previously the main view painted over the tooltip. */
[data-testid="stSidebar"] {{
 overflow:visible!important; z-index:100000!important; isolation:auto!important;
 position:relative!important;
}}
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] [data-testid="stSidebarContent"],
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stSidebar"] [data-testid="stElementContainer"],
[data-testid="stSidebar"] div.stButton {{overflow:visible!important;}}
[data-testid="stSidebar"] div.stButton button {{position:relative!important;overflow:visible!important;}}

[data-testid="stAppViewContainer"] {{z-index:0!important;}}


@media(max-width:700px) {{[data-testid="stSidebar"] {{max-width:272px!important;}}}}
@media(prefers-reduced-motion:reduce) {{[data-testid="stSidebar"] {{transition:none!important;}}}}
</style>""",unsafe_allow_html=True)

with st.sidebar:
    # One icon-only toggle; native Streamlit chevron hidden to avoid duplicates.
    st.button('»' if compact else '«',
              key='crm_sidebar_toggle', use_container_width=True,
              help=None,  # avoid Streamlit native tooltip overlapping the icon rail
              on_click=lambda: st.session_state.update(crm_sidebar_compact=not st.session_state.crm_sidebar_compact))
    if not compact:
        st.markdown("""<div class="crm-sidebar-brand">
        <div class="crm-brand-icon">🎧</div>
        <div><div class="crm-brand-name">CRM Specialist</div>
        <div class="crm-brand-subtitle">AutoGen · RAG · CRM</div></div>
    </div><div class="crm-sidebar-label">WORKSPACE</div>""", unsafe_allow_html=True)
    for icon, name in nav:
        st.button(icon if compact else f'{icon}  {name}',
                  key='nav_'+name, use_container_width=True,
                  help=name if compact else None,  # one native tooltip only in compact mode
                  on_click=_go_to_page, args=(name,))
    if not compact:
        st.markdown('<div class="crm-sidebar-footer-label">SYSTEM STATUS</div>', unsafe_allow_html=True)
    online = _health_ok(API)
    status_class = 'online' if online else 'offline'
    if compact:
        st.markdown(f'<div class="crm-sidebar-status {status_class}" title="CRM service {"connected" if online else "offline"}"><span class="crm-status-dot"></span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="crm-sidebar-status {status_class}"><span class="crm-status-dot"></span> CRM service {"connected" if online else "offline"}</div>', unsafe_allow_html=True)

page = st.session_state.page
if page in ('Tickets', 'Human Review'):
    page = 'Ticket Management'
    st.session_state.page = page
# Scope the selected style to the corresponding Streamlit widget key.
active_key = ('nav_' + page).replace(' ', '_')
st.markdown(f'''<style>
[data-testid="stSidebar"] .st-key-{active_key} button,
[data-testid="stSidebar"] .st-key-{active_key} button:hover {{
 background:#E6F7F7!important; color:#007D85!important;
 border:1px solid #B7E5E3!important; border-left:4px solid #009DA5!important;
 font-weight:700!important; box-shadow:0 2px 8px rgba(0,157,165,.06)!important;
}}
</style>''', unsafe_allow_html=True)

if page=='Dashboard':
    st.markdown('''<div class="crm-dashboard-banner"><div class="crm-dashboard-kicker">CUSTOMER SUPPORT OVERVIEW</div><h2>Welcome back, Admin 👋</h2><p>Monitor tickets, knowledge-driven responses and agent activity in one place.</p></div>''', unsafe_allow_html=True)
    stats=req('/stats') or {}; rows=req('/tickets',params={'limit':1000}) or []
    filter_col, period_col = st.columns([2,1])
    with filter_col:
        st.caption('Explore ticket trends and categories')
    with period_col:
        period=st.selectbox('Date range',['All time','7 days','30 days','90 days'],key='dashboard_period')
    if period!='All time' and rows:
        cutoff=pd.Timestamp.now(tz='UTC')-pd.Timedelta(days=int(period.split()[0]))
        rows=[r for r in rows if pd.notna(pd.to_datetime(r.get('created_at'),errors='coerce',utc=True)) and pd.to_datetime(r['created_at'],utc=True)>=cutoff]
    filtered_stats={**stats,'total':len(rows),'resolved':sum(r.get('status')=='Resolved' for r in rows),
                    'escalated':sum(r.get('status')=='Escalated' for r in rows),
                    'categories':{cat:sum(r.get('category')==cat for r in rows) for cat in sorted({r.get('category','General') for r in rows})}}
    if period!='All time':
        st.caption('Metrics and charts reflect the selected date range; SLA compliance remains the backend-wide value.')
    stats=filtered_stats
    cols=st.columns(4)
    for c,label,key in zip(cols,['Total Tickets','Resolved','Escalated','SLA Compliance'],['total','resolved','escalated','sla_compliance']):
        with c: st.metric(label,f"{stats.get(key,0)}{'%' if key=='sla_compliance' else ''}")
    left,right=st.columns([1.7,1])
    with left:
        with st.container(border=True):
            st.subheader('Ticket Trend')
            if rows:
                df = pd.DataFrame(rows)
                timestamps = pd.to_datetime(df['created_at'], errors='coerce', utc=True).dt.tz_convert(None)
                daily = timestamps.dt.normalize().value_counts().sort_index()
                if not daily.empty:
                    # Continuous calendar dates, including zero-ticket days; categorical labels avoid timestamp artifacts.
                    days = pd.date_range(daily.index.min(), daily.index.max(), freq='D')
                    counts = daily.reindex(days, fill_value=0)
                    trend = pd.DataFrame({
                        'Day': days.strftime('%d %b'),
                        'Tickets': counts.astype(int).to_numpy(),
                        'Date': days.strftime('%d %b %Y'),
                    })
                    fig = px.bar(trend, x='Day', y='Tickets', text='Tickets',
                                 color='Tickets', color_continuous_scale=['#BDEBE8','#009DA5','#087E91'],
                                 custom_data=['Date'])
                    fig.update_traces(textposition='outside', textfont=dict(size=13, color='#17324D'),
                                      hovertemplate='<b>%{customdata[0]}</b><br>Tickets: %{y}<extra></extra>',
                                      marker_line_width=0)
                    fig.update_layout(height=345, showlegend=False, coloraxis_showscale=False,
                                      bargap=0.42, margin=dict(l=10,r=12,t=25,b=12),
                                      xaxis_title=None, yaxis_title='Number of tickets')
                    fig.update_xaxes(type='category', tickangle=0, showgrid=False)
                    fig.update_yaxes(dtick=1, rangemode='tozero', zeroline=False,
                                     range=[0, max(2, int(trend['Tickets'].max()) + 1)])
                    st.plotly_chart(crm_chart(fig), use_container_width=True)
                else:
                    st.info('No valid ticket dates are available yet.')
            else: st.info('Ticket trends will appear after complaints are submitted.')
    with right:
        with st.container(border=True):
            st.subheader('Tickets by Category')
            cats=stats.get('categories',{})
            if cats:
                category_df = pd.DataFrame({'Category': list(cats.keys()), 'Tickets': list(cats.values())})
                category_df['Tickets'] = pd.to_numeric(category_df['Tickets'], errors='coerce').fillna(0).astype(int)
                category_df = category_df[category_df['Tickets'] > 0]
                if not category_df.empty:
                    fig = px.pie(category_df, names='Category', values='Tickets', hole=0.58,
                                 color='Category', color_discrete_sequence=CRM_CHART_COLORS)
                    fig.update_traces(textinfo='percent', textposition='inside',
                                      textfont=dict(size=12, color='white'),
                                      marker=dict(line=dict(color='white', width=3)),
                                      hovertemplate='<b>%{label}</b><br>Tickets: %{value}<br>Share: %{percent}<extra></extra>')
                    fig.update_layout(height=345, showlegend=True,
                                      legend=dict(orientation='h', yanchor='top', y=-0.06,
                                                  xanchor='center', x=0.5, font=dict(size=11)),
                                      margin=dict(l=6,r=6,t=12,b=54),
                                      annotations=[dict(text=f"<b>{int(category_df['Tickets'].sum())}</b><br><span style='font-size:11px'>Tickets</span>",
                                                        x=0.5,y=0.5,font=dict(size=23,color='#17324D'),showarrow=False)])
                    st.plotly_chart(crm_chart(fig), use_container_width=True)
                else:
                    st.info('No category data yet.')
            else: st.info('No category data yet.')
    left,right=st.columns([2.3,1])
    with left:
        with st.container(border=True):
            st.subheader('Recent Tickets'); table(rows[:8])
    with right:
        with st.container(border=True):
            st.subheader('Live Agent Progress')
            latest_runs=req('/runs',params={'limit':100}) or []
            names=['QueryAgent','KnowledgeAgent','ResolutionAgent','LogAgent']
            if latest_runs:
                for agent in names:
                    matched=next((r for r in latest_runs if r.get('agent')==agent),None)
                    if matched:
                        duration=matched.get('duration_ms')
                        st.markdown(f"🟢 **{agent}** · {duration/1000:.2f}s" if isinstance(duration,(int,float)) else f"🟢 **{agent}** · recorded")
                    else:
                        st.caption(f'⚪ {agent} · No recent run')
                st.caption('Most recently persisted execution records. Not a live streaming feed.')
            else:
                st.info('Agent execution history will appear after a request is processed.')
        with st.container(border=True):
            st.subheader('Quick Actions')
            if st.button('＋ New Ticket',use_container_width=True): st.session_state.page='AI Support Chat'; st.rerun()
            if st.button('↑ Knowledge Base (Settings)',use_container_width=True): st.session_state.page='Settings'; st.rerun()

elif page=='AI Support Chat':
    # Callbacks run before Streamlit instantiates the complaint widget.
    def _new_chat():
        st.session_state['active_conversation'] = None
        st.session_state['faq_complaint'] = ''

    def _select_conversation():
        st.session_state['active_conversation'] = st.session_state['chat_history_selection']
        st.session_state['faq_complaint'] = ''

    def _select_faq(prompt):
        st.session_state['faq_complaint'] = prompt

    heading('AI Support Chat','Ask questions first. A ticket is created only if you request human support.')
    if 'active_conversation' not in st.session_state: st.session_state.active_conversation=None
    if 'faq_complaint' not in st.session_state: st.session_state.faq_complaint=''
    if st.session_state.pop('_clear_faq_on_next_run', False):
        st.session_state['faq_complaint'] = ''
    top_left,top_right=st.columns([3,1], vertical_alignment='bottom', gap='medium')
    with top_right:
        st.button('＋ New Request / New Chat',type='primary',use_container_width=True,on_click=_new_chat,key='chat_new_button')
    with top_left:
        history=req('/conversations') or []
        options=[None]+[c['id'] for c in history]
        labels={None:'New conversation',**{c['id']:f"#{c['id']} · {c['title'][:55]}" for c in history}}
        current=st.session_state.active_conversation
        if current not in options: current=None;st.session_state.active_conversation=None
        # Explicitly initialize the selectbox state, even when current is None.
        # .get() alone is insufficient because a missing key also returns None.
        if 'chat_history_selection' not in st.session_state:
            st.session_state['chat_history_selection'] = current
        elif st.session_state['chat_history_selection'] not in options or st.session_state['chat_history_selection'] != current:
            st.session_state['chat_history_selection'] = current
        st.selectbox('Continue an old conversation (optional)',options,
                     format_func=lambda x:labels.get(x,str(x)),
                     key='chat_history_selection',on_change=_select_conversation)
    faq_items=[
        ('🚚 Shipping','Where is my order?','My order has not arrived yet. Can you help me track the delivery?'),
        ('↩️ Returns','How do I return a product?','I want to return a product. What is the return and refund process?'),
        ('🔐 Account','How can I reset my password?','I forgot my account password. How can I reset it?'),
        ('📦 Products','I received a damaged product','My product arrived damaged. How can I request a replacement?'),
        ('💳 Billing','Why was I charged twice?','I was charged multiple times for my order. Please help investigate.'),
        ('🎫 Support','How can I check my ticket status?','I want to check the current status of my support ticket.')]
    with st.expander('✨ Frequently Asked Questions',expanded=st.session_state.active_conversation is None):
        for row_start in range(0,len(faq_items),3):
            cols=st.columns(3)
            for i,(col,(category,title,prompt)) in enumerate(zip(cols,faq_items[row_start:row_start+3])):
                with col:
                    st.caption(category)
                    st.button(title,key=f'faq_{row_start+i}',use_container_width=True,
                              on_click=_select_faq,args=(prompt,))
    conversation=None
    if st.session_state.active_conversation is not None:
        conversation=req(f"/conversations/{st.session_state.active_conversation}")
    if conversation:
        st.caption('Conversation history — each request has its own agent execution process')
        for turn in conversation['turns']:
            with st.chat_message('user'):
                st.write(turn['question'])
            with st.chat_message('assistant'):
                st.write(turn['answer'])
                st.caption('Sources: '+(', '.join(turn.get('sources',[])) or 'No matching source'))
                st.caption(f"Category: {turn['category']} · Urgency: {turn['urgency']}")
                render_agent_journey(turn)
                if turn.get('ticket_id'):
                    st.success('Support ticket: '+turn['ticket_id'])
                else:
                    st.caption('Did this answer resolve your issue?')
                    yes,no,unused=st.columns([1.3,1.6,3.6], gap='small')
                    if yes.button('👍 Yes, resolved — no ticket',key=f'yes_{turn["id"]}',use_container_width=True):
                        st.success('Thanks! No ticket was created.')
                    if no.button('👎 Not satisfied — Create Ticket',key=f'no_{turn["id"]}',use_container_width=True):
                        created=req(f"/conversations/{conversation['id']}/ticket",'post',json={'turn_id':turn['id']})
                        if created:
                            st.success(f"Ticket {created['ticket_id']} created · {created['status']}")
                            st.rerun()
    else:
        st.info('Start a new request, or choose an old conversation above to continue it. No previous answer is shown automatically.')
    with st.form('chat_request',clear_on_submit=False):
        if not conversation:
            a,b,c=st.columns(3)
            name=a.text_input('Customer name',value='Demo Customer')
            email=b.text_input('Email (optional)')
            order=c.text_input('Order ID (optional)')
        complaint=st.text_area('Your message',height=110,placeholder='Ask a question or describe the issue...',key='faq_complaint')
        submitted=st.form_submit_button('Send Message',type='primary')
    if submitted:
        if len(complaint.strip())<5: st.warning('Please enter at least five characters.')
        else:
            conversation_id=st.session_state.active_conversation
            if conversation_id is None:
                new=req('/conversations','post',json={'customer_name':name,'email':email or None,'order_id':order or None})
                conversation_id=new['id'] if new else None
            if conversation_id is not None:
                with st.spinner('Processing: Query → Knowledge → Resolution → Log...'):
                    result=req(f'/conversations/{conversation_id}/messages','post',json={'question':complaint.strip()})
                if result:
                    st.session_state.active_conversation=conversation_id
                    st.session_state['_clear_faq_on_next_run'] = True
                    st.rerun()

elif page=='Ticket Management':
    heading('Ticket Management', 'Manage customer tickets and review escalations in one workspace.')
    all_rows = req('/tickets', params={'limit': 1000}) or []
    escalated_count = sum(str(t.get('status', '')).lower() == 'escalated' for t in all_rows)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric('Total tickets', len(all_rows))
    k2.metric('Awaiting human review', escalated_count)
    k3.metric('Resolved', sum(t.get('status') == 'Resolved' for t in all_rows))
    k4.metric('High urgency', sum(t.get('urgency') == 'High' for t in all_rows))
    st.markdown('<div class="crm-ticket-hint">Manage requests, update ticket status, and approve AI responses without switching pages.</div>', unsafe_allow_html=True)
    tm_options = [f'🎫 All Tickets ({len(all_rows)})', f'🙋 Human Review ({escalated_count})']
    tm_selected = crm_button_tabs('tm', tm_options, 'tm_view_v34', columns=2)
    if tm_selected == tm_options[0]:
        st.markdown('#### Find and manage tickets')
        a, b, c, d = st.columns([2, 1, 1, 1])
        search = a.text_input('Search tickets', placeholder='Ticket ID, customer, order or complaint', key='tm_search')
        status = b.selectbox('Status', ['', 'Open', 'In Progress', 'Answered', 'Escalated', 'Resolved'], key='tm_status')
        category = c.selectbox('Category', ['', 'Shipping', 'Refund', 'Billing', 'Account', 'Product', 'General'], key='tm_category')
        urgency = d.selectbox('Urgency', ['', 'Low', 'Medium', 'High'], key='tm_urgency')
        rows = req('/tickets', params={'search': search, 'status': status, 'category': category, 'urgency': urgency, 'limit': 1000}) or []
        sort_col, count_col = st.columns([1, 3])
        with sort_col:
            ticket_sort = st.selectbox('Sort by', ['Newest first', 'Oldest first', 'Urgency (high first)', 'Customer A–Z'], key='tm_sort')
        if ticket_sort == 'Oldest first':
            rows.sort(key=lambda x: x.get('created_at') or '')
        elif ticket_sort == 'Urgency (high first)':
            rows.sort(key=lambda x: ({'High': 0, 'Medium': 1, 'Low': 2}.get(x.get('urgency'), 3), -(x.get('id') or 0)))
        elif ticket_sort == 'Customer A–Z':
            rows.sort(key=lambda x: (x.get('customer_name') or '').lower())
        with count_col:
            st.caption(f'{len(rows)} matching ticket(s)')
        table(rows)
        if rows:
            chosen = st.selectbox('Ticket details', rows, format_func=lambda x: f"{x['ticket_id']} · {x.get('customer_name', '')} · {x.get('status', '')}", key='tm_ticket')
            with st.container(border=True):
                st.markdown(f"#### {chosen['ticket_id']} · {chosen.get('category') or 'General'}")
                left, right = st.columns([3, 1])
                with left:
                    st.markdown('**Customer request**')
                    st.write(chosen.get('complaint') or 'Not available')
                    st.markdown('**AI response**')
                    st.info(chosen.get('response') or 'Pending AI response')
                    st.caption('Knowledge sources: ' + (', '.join(chosen.get('sources') or []) or 'None'))
                with right:
                    st.markdown(f"**Status:** {chosen.get('status', 'Unknown')}")
                    st.markdown(f"**Urgency:** {chosen.get('urgency', 'Unknown')}")
                    if chosen.get('status') != 'Resolved':
                        if st.button('✓ Resolve', key='tm_resolve', use_container_width=True):
                            updated = req(f"/tickets/{chosen['id']}/review", 'post', json={'action': 'Resolve', 'reviewer': 'Admin', 'notes': 'Resolved from Ticket Management'})
                            if updated: st.rerun()
                    else:
                        if st.button('↩ Reopen', key='tm_reopen', use_container_width=True):
                            updated = req(f"/tickets/{chosen['id']}/review", 'post', json={'action': 'Reopen', 'reviewer': 'Admin', 'notes': 'Reopened from Ticket Management'})
                            if updated: st.rerun()
                    if chosen.get('status') == 'Escalated':
                        st.caption('Use the Human Review tab to approve or edit this response.')
        st.markdown('#### Export ticket records')
        if st.button('Prepare CSV export', key='tm_export'):
            try:
                response = requests.get(API + '/tickets/export', timeout=30)
                response.raise_for_status()
                st.session_state['tm_csv_export'] = response.content
            except requests.RequestException as exc:
                st.error(f'Export failed: {exc}')
        if st.session_state.get('tm_csv_export'):
            st.download_button('⬇ Download tickets.csv', st.session_state['tm_csv_export'], 'tickets.csv', 'text/csv', key='tm_csv_download')
    else:
        st.markdown('#### Escalated tickets awaiting review')
        st.caption('Review the evidence and AI draft before approving, rejecting, assigning, or resolving a ticket.')
        escalated = [t for t in all_rows if t.get('status') == 'Escalated']
        if escalated:
            t = st.selectbox('Select escalated ticket', escalated, format_func=lambda x: f"{x['ticket_id']} · {(x.get('summary') or x.get('complaint') or '')[:65]}", key='tm_review_ticket')
            with st.container(border=True):
                st.markdown(f"#### {t['ticket_id']} · {t.get('urgency', 'Unknown')} urgency")
                if t.get('escalation_reason'):
                    st.warning('Escalation reason: ' + str(t['escalation_reason']))
                st.markdown('**Customer complaint**')
                st.write(t.get('complaint') or 'Not available')
                st.caption('Evidence sources: ' + (', '.join(t.get('sources') or []) or 'None'))
            with st.form('tm_review_form'):
                response_text = st.text_area('Review / edit AI response', value=t.get('response') or '', height=170)
                action_col, reviewer_col = st.columns(2)
                action = action_col.selectbox('Review action', ['Approve', 'Reject', 'Resolve', 'Reopen', 'Assign'])
                reviewer = reviewer_col.text_input('Reviewer', value='Admin')
                notes = st.text_area('Review notes', placeholder='Add your review decision and supporting notes')
                if st.form_submit_button('Save review decision', type='primary', use_container_width=True):
                    if not reviewer.strip():
                        st.error('Reviewer is required.')
                    else:
                        result = req(f"/tickets/{t['id']}/review", 'post', json={'action': action, 'reviewer': reviewer.strip(), 'notes': notes, 'response': response_text})
                        if result:
                            st.success('Review saved successfully.')
                            st.rerun()
        else:
            st.success('All caught up — no escalated tickets awaiting human review.')

elif page=='Analytics':
    heading('Analytics','Ticket distribution, support performance and trends.')
    rows=req('/tickets') or []
    if rows:
        df=pd.DataFrame(rows); a,b=st.columns(2)
        with a: st.plotly_chart(crm_chart(px.bar(df.groupby('category').size().reset_index(name='Count'),x='category',y='Count',title='Tickets by Category',color_discrete_sequence=CRM_CHART_COLORS)),use_container_width=True)
        with b: st.plotly_chart(crm_chart(px.pie(df,names='status',title='Resolution Outcomes',hole=.6,color_discrete_sequence=CRM_CHART_COLORS)),use_container_width=True)
        st.dataframe(df[['ticket_id','category','urgency','status']],hide_index=True,use_container_width=True)
    else: st.info('Analytics will appear after ticket creation.')

elif page=='Notifications':
    heading('Notifications','Escalation email history and SMTP delivery status.')
    smtp=req('/notifications/smtp-status')
    if smtp:
        if smtp.get('configured'):
            st.success('SMTP settings are configured. This does not guarantee successful delivery.')
        else:
            missing=[k for k,v in smtp.get('fields',{}).items() if not v]
            st.warning('SMTP configuration incomplete: '+(', '.join(missing) if missing else 'check backend .env'))
    records=req('/notifications')
    if records is not None:
        if records:
            df=pd.DataFrame(records)
            sent=sum(r['delivery_status']=='Sent' for r in records)
            failed=sum(r['delivery_status']=='Failed' for r in records)
            c1,c2,c3=st.columns(3)
            c1.metric('Notification records',len(records))
            c2.metric('Sent',sent)
            c3.metric('Failed',failed)
            status_filter=st.selectbox('Delivery status',['All','Sent','Failed','Sending','Pending'])
            filtered=df if status_filter=='All' else df[df['delivery_status']==status_filter]
            columns=['from_email','to_email','ticket_id','ticket_status','priority','delivery_status','subject','created_at']
            st.dataframe(filtered[columns].rename(columns={
                'from_email':'From','to_email':'To','ticket_id':'Ticket ID',
                'ticket_status':'Ticket Status','priority':'Priority',
                'delivery_status':'Email Status','subject':'Subject','created_at':'Created At'
            }),hide_index=True,use_container_width=True)
            st.caption('From shows the currently configured SMTP sender; historical sender addresses are not stored. Sent means the SMTP server accepted the message, not confirmed inbox delivery.')
        else:
            st.info('No email notifications recorded yet. An escalation creates a record when SMTP_TO_EMAIL is configured.')

elif page=='Settings':
    heading('Settings','Application configuration, customer insights and monitoring tools.')
    settings_options = [
        '⚙️ General', '👥 Customer 360°', '🤖 Agent Monitor', '💡 Knowledge Gaps',
        '🕒 SLA Management', '⭐ AI Quality & Feedback', '📖 Knowledge Base'
    ]
    settings_selected = crm_button_tabs('settings', settings_options, 'settings_view_v34', columns=7)
    if settings_selected == settings_options[0]:
        st.subheader('Application Configuration')
        st.write('**Backend:**',API)
        st.write('**Database:** SQLite')
        st.write('**Knowledge retrieval:** BM25 + optional FAISS')
        st.write('**Agent order:** Query → Knowledge → Resolution → Log')
        st.warning('Before public deployment: implement authentication, role enforcement, tenant isolation, email delivery, background jobs, rate limits and production-grade agent workflows.')
    if settings_selected == settings_options[1]:
        heading('Customer 360°','Complete view of customer history and interactions.')
        customers=req('/customers') or []
        if customers:
            c=st.selectbox('Customer',customers,format_func=lambda x:x['name']+' · '+str(x['tickets'])+' tickets')
            detail=req(f"/customers/{c['id']}") or {}; a,b,c1=st.columns(3); a.metric('Customer',detail.get('name')); b.metric('Tickets',len(detail.get('tickets',[]))); c1.metric('Language',detail.get('language','English')); table(detail.get('tickets',[]))
        else: st.info('No customers yet.')
    if settings_selected == settings_options[2]:
        heading('Agent Monitor','Execution traces for the four specialized agents.')
        runs=req('/runs') or []
        if runs:
            df=pd.DataFrame(runs); st.dataframe(df[['ticket_id','agent','duration_ms','created_at']],hide_index=True,use_container_width=True)
            run=st.selectbox('Inspect step',runs,format_func=lambda x:f"TKT-{x['ticket_id']:04d} · {x['agent']}"); st.code(run['detail'],language='json')
            st.link_button('Download complete agent logs (CSV)',API+'/runs/export')
            st.caption('CSV includes ticket, priority, status, question, answer, sources, per-agent timing and execution detail.')
        else: st.info('No agent runs yet.')
        st.link_button('Export agent execution logs',API+'/runs/export')
        st.subheader('Knowledge grounding checks')
        grounding=req('/evaluation/grounding')
        if grounding:
            a,b,c=st.columns(3)
            a.metric('Tickets checked',grounding['checked'])
            b.metric('Source names verified',grounding['verified_source_names'])
            c.metric('Needs review',grounding['needs_review'])
            if grounding.get('results'):
                st.dataframe(pd.DataFrame(grounding['results']),hide_index=True,use_container_width=True)
            st.caption(grounding['disclaimer'])
    if settings_selected == settings_options[3]:
        heading('Knowledge Gaps','Questions with no verified knowledge-base answer.')
        items=req('/knowledge-gaps') or []; st.metric('Potential Gaps',len(items))
        if items: st.dataframe(pd.DataFrame(items),hide_index=True,use_container_width=True)
        else: st.success('No recorded gaps yet.')

    if settings_selected == settings_options[4]:
        heading('SLA Management','Monitor response deadlines and overdue tickets.')
        rows=req('/tickets') or []; now=pd.Timestamp.now(tz='UTC'); overdue=[]
        for r in rows:
            if r.get('due_at') and r['status'] not in ['Resolved','Answered'] and pd.to_datetime(r['due_at'],utc=True)<now: overdue.append(r)
        a,b=st.columns(2); a.metric('Open SLA Breaches',len(overdue)); b.metric('Total Tracked',len(rows)); table(overdue)
        st.caption('Initial demonstration SLA: High 4 hours · Medium 24 hours · Low 72 hours. Configure before production.')
    if settings_selected == settings_options[5]:
        heading('AI Quality & Feedback','Customer feedback and AI quality monitoring.')
        items=req('/feedback') or []; total=len(items); helpful=sum(bool(x['helpful']) for x in items)
        a,b=st.columns(2); a.metric('Feedback Received',total); b.metric('Helpful Rate',f'{helpful/total:.0%}' if total else '—')
        if items: st.dataframe(pd.DataFrame(items),hide_index=True,use_container_width=True)
        st.info('DeepEval evaluation runner is an optional dependency. Automated production scoring is not enabled in this starter.')

    if settings_selected == settings_options[6]:
        heading('Knowledge Base','Upload and manage PDF, TXT and Markdown policies.')
        files=st.file_uploader('Choose knowledge documents',type=['pdf','txt','md'],accept_multiple_files=True,help='Select up to 50 files; maximum 8 MB each. Duplicate content is skipped.')
        if files:
            st.caption(f'{len(files)} document(s) selected · {sum(len(f.getvalue()) for f in files)/1024/1024:.2f} MB total')
            st.dataframe(pd.DataFrame([{'Filename':f.name,'Size (KB)':round(len(f.getvalue())/1024,1),'Type':f.name.rsplit('.',1)[-1].upper()} for f in files]),hide_index=True,use_container_width=True)
        if st.button('Ingest All Documents',type='primary',disabled=not files):
            if len(files)>50:
                st.error('Select no more than 50 files per batch.')
            else:
                progress=st.progress(0,text='Preparing documents...')
                # Process each file independently to display real-time progress and per-file errors.
                outcomes=[]
                for index,f in enumerate(files):
                    progress.progress(index/len(files),text=f'Processing {index+1}/{len(files)}: {f.name}')
                    try:
                        r=requests.post(API+'/documents/upload',files={'file':(f.name,f.getvalue(),f.type or 'application/octet-stream')},timeout=120)
                        if r.ok:
                            item=r.json()
                            outcomes.append({'File':f.name,'Status':item.get('status','uploaded').title(),'Details':item.get('reason',f"Version {item.get('version','—')} · {item.get('characters',0)} characters")})
                        else:
                            try: detail=r.json().get('detail',r.text)
                            except ValueError: detail=r.text[:200]
                            outcomes.append({'File':f.name,'Status':'Failed','Details':str(detail)})
                    except requests.RequestException as exc:
                        outcomes.append({'File':f.name,'Status':'Failed','Details':str(exc)})
                    progress.progress((index+1)/len(files),text=f'Processed {index+1}/{len(files)} documents')
                st.session_state['kb_upload_results']=outcomes
        if st.session_state.get('kb_upload_results'):
            outcomes=st.session_state['kb_upload_results']
            a,b,c=st.columns(3)
            a.metric('Uploaded',sum(x['Status']=='Uploaded' for x in outcomes))
            b.metric('Duplicates skipped',sum(x['Status']=='Skipped' for x in outcomes))
            c.metric('Failed',sum(x['Status']=='Failed' for x in outcomes))
            st.dataframe(pd.DataFrame(outcomes),hide_index=True,use_container_width=True)
            if any(x['Status']=='Failed' for x in outcomes): st.warning('Some files failed. Check the details and retry only those files.')
        docs=req('/documents') or []
        if docs:
            st.dataframe(pd.DataFrame(docs),hide_index=True,use_container_width=True)
            selected=st.selectbox('Delete document',docs,format_func=lambda x:f"{x['filename']} · v{x['version']}")
            if st.button('Delete selected document'):
                if req(f"/documents/{selected['id']}",'delete'): st.rerun()
        q=st.text_input('Test knowledge search')
        if q and st.button('Search KB'):
            result=req('/search',params={'q':q}) or {}; st.json(result.get('matches',[]))


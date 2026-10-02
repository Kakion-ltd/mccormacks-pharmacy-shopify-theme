"""Re-takes the storefront screenshots in this folder, arrows drawn on. Run from anywhere:
    python3 setup/staff-guide/shoot.py
Admin screenshots are not taken here: the admin needs a logged-in session.
"""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw
import math
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
B='https://www.mccormackspharmacy.ie'; RED=(220,38,38)
def arrow(d, tip, ang, L=110, w=9):
    # ang: direction the arrow comes FROM (degrees, 0=from right)
    a=math.radians(ang); tx,ty=tip; sx,sy=tx+L*math.cos(a), ty+L*math.sin(a)
    hx,hy=tx+30*math.cos(a), ty+30*math.sin(a)
    d.line([(sx,sy),(hx,hy)],fill=RED,width=w)
    p=math.radians(90)
    d.polygon([(tx,ty),(hx+18*math.cos(a+p),hy+18*math.sin(a+p)),(hx+18*math.cos(a-p),hy+18*math.sin(a-p))],fill=RED)
def shot(pg,out,clip,arrows):
    pg.screenshot(path=out,clip=clip); im=Image.open(out).convert('RGB'); d=ImageDraw.Draw(im)
    for box,side in arrows:
        x,y,w,h=box['x']-clip['x'],box['y']-clip['y'],box['width'],box['height']
        if side=='left': arrow(d,(x-6,y+h/2),180)
        elif side=='right': arrow(d,(x+w+6,y+h/2),0)
        elif side=='below': arrow(d,(x+w/2,y+h+6),90)
    im.save(out)
def bb(pg,sel): 
    l=pg.locator(sel).first; l.scroll_into_view_if_needed(); return l.bounding_box()
with sync_playwright() as p:
    b=p.chromium.launch(channel='chrome'); pg=b.new_page(viewport={'width':1280,'height':860})
    def go(path):
        pg.goto(B+path, wait_until='networkidle', timeout=60000); pg.wait_for_timeout(600)
    go('/products/cydonia-cooling-polar-ice-100ml'); pg.evaluate('scrollTo(0,0)')
    shot(pg,'oos.png',{'x':0,'y':180,'width':1280,'height':400},[(bb(pg,'text=Out of stock >> nth=0'),'left')])
    go('/products/nurofen-tablets-12pk'); pg.evaluate('scrollTo(0,0)')
    shot(pg,'med.png',{'x':0,'y':180,'width':1280,'height':620},[(bb(pg,'a:has-text("Ask a pharmacist")'),'left'),(bb(pg,'button:has-text("health questions")'),'below')])
    pg.locator('button:has-text("health questions")').first.click(); pg.wait_for_timeout(1200)
    pg.screenshot(path='modal.png'); Image.open('modal.png').crop((350,50,930,815)).save('modal.png')
    go('/collections/pain-relief')
    card=pg.locator('text=Nurofen Tablets 24Pk').first; card.scroll_into_view_if_needed(); pg.wait_for_timeout(500)
    vb=pg.locator('a:has-text("View Product"), button:has-text("View Product")').nth(7).bounding_box()
    ab=pg.locator('button:has-text("Add To Bag"), a:has-text("Add To Bag")').first.bounding_box()
    y0=vb['y']-330; shot(pg,'grid.png',{'x':300,'y':max(0,y0),'width':980,'height':420},[(vb,'below'),(ab,'below')])
    b.close()

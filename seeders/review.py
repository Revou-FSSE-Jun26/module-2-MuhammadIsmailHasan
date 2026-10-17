"""Halaman review data hasil seeding: python -m seeders.review."""

import json
import os

from sqlalchemy import text

from app import create_app
from app.extensions import db

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "static", "images",
)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "review.html")

QUERY = """
    select c.name, s.name, p.id, p.name, p.price, p.stock, p.description,
           array_agg(i.url order by i."order") as urls
    from products p
    join sub_categories s on s.id = p.sub_category_id
    join categories c on c.id = s.category_id
    left join product_images i on i.product_id = p.id and i.is_active
    where p.is_active
    group by c.name, s.name, p.id, p.name, p.price, p.stock, p.description
    order by c.name, s.name, p.id
"""

TEMPLATE = """<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review Produk Seeder</title>
<style>
:root{--bg:#0f1115;--card:#181b22;--line:#272b35;--fg:#e7e9ee;--dim:#9aa1ad;--acc:#5b9cff;--warn:#f0a73a}
@media(prefers-color-scheme:light){:root{--bg:#f6f7f9;--card:#fff;--line:#e2e5ea;--fg:#1b1e24;--dim:#6b7280;--acc:#2563eb;--warn:#b45309}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:14px 16px}
h1{margin:0 0 8px;font-size:17px;font-weight:650}
.meta{color:var(--dim);font-size:12px;margin-bottom:10px}
nav{display:flex;flex-wrap:wrap;gap:6px}
nav button{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:999px;
 padding:5px 11px;font-size:12px;cursor:pointer;font-family:inherit}
nav button.on{background:var(--acc);border-color:var(--acc);color:#fff}
main{padding:16px;max-width:1100px}
section{margin-bottom:26px}
h2{font-size:14px;margin:0 0 10px;font-weight:650}
h2 span{color:var(--dim);font-weight:400}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px;
 margin-bottom:9px;display:grid;grid-template-columns:96px 1fr;gap:12px}
.thumbs{display:flex;flex-direction:column;gap:4px}
.thumbs img{width:96px;height:96px;object-fit:cover;border-radius:6px;background:var(--line);cursor:zoom-in;display:block}
.strip{display:flex;gap:4px;flex-wrap:wrap}
.strip img{width:28px;height:28px;object-fit:cover;border-radius:4px;background:var(--line);cursor:zoom-in}
.nm{font-weight:600;margin-bottom:3px}
.pr{color:var(--acc);font-weight:650}
.st{font-size:12px;color:var(--dim)}
.st b.zero{color:var(--warn)}
.de{font-size:12.5px;color:var(--dim);margin-top:5px}
.cnt{font-size:11px;color:var(--dim);margin-top:4px}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;align-items:center;
 justify-content:center;z-index:20;cursor:zoom-out;padding:20px}
#lb.on{display:flex}
#lb img{max-width:100%;max-height:88vh;object-fit:contain}
@media(max-width:560px){.card{grid-template-columns:72px 1fr}.thumbs img{width:72px;height:72px}}
</style></head><body>
<header><h1>Review Produk Seeder</h1><div class="meta" id="meta"></div><nav id="nav"></nav></header>
<main id="main"></main><div id="lb"><img alt=""></div>
<script>
const G = __DATA__;
const rupiah = n => "Rp" + n.toLocaleString("id-ID");
document.getElementById("meta").textContent =
  G.reduce((a,g)=>a+g.items.length,0) + " produk \\u00b7 " + G.length +
  " sub-category \\u00b7 gambar pertama = foto produk sendiri, sisanya galeri sintetis";
const nav=document.getElementById("nav"), main=document.getElementById("main");
const mk=(l,on)=>{const b=document.createElement("button");b.textContent=l;
  if(on)b.className="on";nav.appendChild(b);return b;};
const esc = s => s.replace(/[<>&]/g,"");
function render(f){
  main.innerHTML="";
  G.filter(g=>!f||g.sub===f).forEach(g=>{
    const s=document.createElement("section");
    s.innerHTML='<h2>'+g.sub+' <span>\\u2014 '+g.cat+' \\u00b7 '+g.items.length+' produk</span></h2>';
    g.items.forEach(it=>{
      const d=document.createElement("div"); d.className="card";
      d.innerHTML=
        '<div class="thumbs"><img loading="lazy" src="'+it.g[0]+'" alt="">'+
        '<div class="strip">'+it.g.slice(1).map(u=>
          '<img loading="lazy" src="'+u+'" alt="">').join("")+'</div></div>'+
        '<div><div class="nm">'+esc(it.n)+'</div>'+
        '<div class="pr">'+rupiah(it.p)+'</div>'+
        '<div class="st">stock: <b class="'+(it.s===0?"zero":"")+'">'+it.s+'</b></div>'+
        '<div class="de">'+esc(it.d)+'</div>'+
        '<div class="cnt">'+it.g.length+' gambar</div></div>';
      s.appendChild(d);
    });
    main.appendChild(s);
  });
}
const all=mk("Semua",true), btns=[all,...G.map(g=>mk(g.sub,false))];
btns.forEach((b,i)=>b.onclick=()=>{btns.forEach(x=>x.className="");b.className="on";
  render(i===0?null:G[i-1].sub);scrollTo({top:0});});
render(null);
const lb=document.getElementById("lb");
main.addEventListener("click",e=>{if(e.target.tagName!=="IMG")return;
  lb.querySelector("img").src=e.target.src;lb.className="on";});
lb.onclick=()=>lb.className="";
addEventListener("keydown",e=>{if(e.key==="Escape")lb.className="";});
</script></body></html>
"""


def thumb_src(url):
    if url.startswith("/static/images/"):
        return url[len("/static/images/"):]
    return url


def collect():
    groups, index = [], {}
    rows = db.session.execute(text(QUERY)).fetchall()

    for category, sub_category, _pid, name, price, stock, description, urls in rows:
        key = (category, sub_category)
        if key not in index:
            index[key] = len(groups)
            groups.append({"cat": category, "sub": sub_category, "items": []})
        groups[index[key]]["items"].append(
            {
                "n": name,
                "p": float(price),
                "s": stock,
                "d": description or "",
                "g": [thumb_src(url) for url in urls if url],
            }
        )
    return groups


def generate():
    app = create_app()
    app.config["SQLALCHEMY_ECHO"] = False

    with app.app_context():
        groups = collect()

    if not groups:
        print("Tidak ada produk di database. Jalankan seeder dulu.")
        return

    payload = json.dumps(groups, ensure_ascii=False, separators=(",", ":"))
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        handle.write(TEMPLATE.replace("__DATA__", payload))

    total = sum(len(group["items"]) for group in groups)
    size = os.path.getsize(OUTPUT_PATH) // 1024
    print(f"{total} produk, {len(groups)} sub-category -> {OUTPUT_PATH} ({size} KB)")
    print("Buka: http://localhost:5000/static/images/review.html")


if __name__ == "__main__":
    generate()
